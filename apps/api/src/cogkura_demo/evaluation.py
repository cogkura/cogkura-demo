"""Deterministic comparison relevance evaluation."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from cogkura_demo.context_strategies.base import ComparisonMode, PreparedCustomerContext
from cogkura_demo.metrics import sort_history_chronologically
from cogkura_demo.models import RelevanceMetrics, UnitEvaluation
from cogkura_demo.scenarios import HistoryEvent, load_scenario_bundle

ConceptStatus = Literal["expected", "excluded"]
UnitClassification = Literal["relevant", "stale", "relevant_and_stale", "unclassified"]
ProvenanceStatus = Literal["resolved", "unresolved", "n_a"]


class StaticConceptSpec(BaseModel):
    id: str
    label: str
    status: ConceptStatus
    evidence_event_ids: list[str] = Field(default_factory=list)


class SemanticSlotSpec(BaseModel):
    id: str
    label: str
    predicate: str


class ComparisonConfig(BaseModel):
    scenario_id: str
    concepts: list[StaticConceptSpec] = Field(default_factory=list)
    semantic_slots: list[SemanticSlotSpec] = Field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ConceptState:
    concept_id: str
    label: str
    status: ConceptStatus
    evidence_event_ids: tuple[str, ...]


def validate_comparison_config(config: ComparisonConfig, *, history_event_ids: set[str]) -> None:
    expected_static_events: set[str] = set()
    excluded_static_events: set[str] = set()

    for concept in config.concepts:
        if concept.status not in ("expected", "excluded"):
            msg = f"Concept {concept.id} has unsupported status {concept.status!r}"
            raise ValueError(msg)
        if not concept.evidence_event_ids:
            msg = f"Concept {concept.id} has no evidence_event_ids"
            raise ValueError(msg)
        if len(concept.evidence_event_ids) != len(set(concept.evidence_event_ids)):
            msg = f"Concept {concept.id} has duplicate evidence_event_ids"
            raise ValueError(msg)
        for event_id in concept.evidence_event_ids:
            if event_id not in history_event_ids:
                msg = f"Concept {concept.id} references unknown event {event_id}"
                raise ValueError(msg)
            if concept.status == "expected":
                expected_static_events.add(event_id)
            else:
                excluded_static_events.add(event_id)

    overlap = expected_static_events & excluded_static_events
    if overlap:
        msg = f"Static concepts assign the same event to expected and excluded: {sorted(overlap)}"
        raise ValueError(msg)


def load_comparison_config(data_dir: Path) -> ComparisonConfig:
    path = data_dir / "alex" / "comparison.json"
    config = ComparisonConfig.model_validate_json(path.read_text(encoding="utf-8"))
    bundle = load_scenario_bundle(data_dir)
    validate_comparison_config(config, history_event_ids={event.id for event in bundle.history})
    return config


def _resolve_semantic_slot_concepts(
    history: tuple[HistoryEvent, ...],
    slots: list[SemanticSlotSpec],
) -> list[ConceptState]:
    concepts: list[ConceptState] = []
    ordered = sort_history_chronologically(list(history))
    for slot in slots:
        assertions: list[tuple[str, str]] = []
        for event in ordered:
            for fact in event.semantic_facts:
                if (
                    fact.predicate == slot.predicate
                    and fact.cardinality == "one"
                    and fact.polarity == "affirm"
                ):
                    assertions.append((fact.object_value.upper(), event.id))
        if not assertions:
            continue

        current_value, current_event_id = assertions[-1]
        concepts.append(
            ConceptState(
                concept_id=f"{slot.predicate}:current:{current_value}",
                label=f"{slot.label}: {current_value}",
                status="expected",
                evidence_event_ids=(current_event_id,),
            )
        )

        stale_by_value: dict[str, list[str]] = defaultdict(list)
        for value, event_id in assertions[:-1]:
            stale_by_value[value].append(event_id)

        for value in sorted(stale_by_value):
            concepts.append(
                ConceptState(
                    concept_id=f"{slot.predicate}:stale:{value}",
                    label=f"Previous {slot.label.lower()}: {value}",
                    status="excluded",
                    evidence_event_ids=tuple(stale_by_value[value]),
                )
            )
    return concepts


def _classify_unit(
    *,
    expected_matches: set[str],
    excluded_matches: set[str],
) -> UnitClassification:
    is_relevant = bool(expected_matches)
    is_stale = bool(excluded_matches)
    if is_relevant and is_stale:
        return "relevant_and_stale"
    if is_relevant:
        return "relevant"
    if is_stale:
        return "stale"
    return "unclassified"


def _provenance_status(
    *,
    mode: ComparisonMode,
    source_event_ids: tuple[str, ...],
    had_observation_ids: bool,
) -> ProvenanceStatus:
    if mode != ComparisonMode.COGKURA:
        return "n_a"
    if not source_event_ids and had_observation_ids:
        return "unresolved"
    return "resolved"


class ComparisonEvaluator:
    def __init__(self, config: ComparisonConfig) -> None:
        self._config = config

    def build_concept_states(self, history: tuple[HistoryEvent, ...]) -> list[ConceptState]:
        static = [
            ConceptState(
                concept_id=item.id,
                label=item.label,
                status=item.status,
                evidence_event_ids=tuple(item.evidence_event_ids),
            )
            for item in self._config.concepts
        ]
        dynamic = _resolve_semantic_slot_concepts(history, self._config.semantic_slots)
        return [*static, *dynamic]

    def build_event_to_concepts(self, history: tuple[HistoryEvent, ...]) -> dict[str, set[str]]:
        mapping: dict[str, set[str]] = {}
        for concept in self.build_concept_states(history):
            for event_id in concept.evidence_event_ids:
                mapping.setdefault(event_id, set()).add(concept.concept_id)
        return mapping

    def evaluate(
        self,
        context: PreparedCustomerContext,
        history: tuple[HistoryEvent, ...],
    ) -> RelevanceMetrics:
        concepts = self.build_concept_states(history)
        event_to_concepts = self.build_event_to_concepts(history)
        expected_ids = {item.concept_id for item in concepts if item.status == "expected"}
        excluded_ids = {item.concept_id for item in concepts if item.status == "excluded"}
        expected = [item for item in concepts if item.status == "expected"]

        found_expected: set[str] = set()
        found_excluded: set[str] = set()
        relevant_units = 0
        stale_units = 0
        unclassified_units = 0
        unit_evaluations: list[UnitEvaluation] = []

        for unit in context.units:
            unit_concepts: set[str] = set()
            for event_id in unit.source_event_ids:
                unit_concepts.update(event_to_concepts.get(event_id, set()))

            expected_matches = sorted(unit_concepts & expected_ids)
            excluded_matches = sorted(unit_concepts & excluded_ids)
            classification = _classify_unit(
                expected_matches=set(expected_matches),
                excluded_matches=set(excluded_matches),
            )

            had_observation_ids = bool(unit.raw_observation_ids)
            provenance = _provenance_status(
                mode=context.mode,
                source_event_ids=unit.source_event_ids,
                had_observation_ids=had_observation_ids,
            )

            if classification == "relevant":
                relevant_units += 1
            elif classification == "stale":
                stale_units += 1
            elif classification == "relevant_and_stale":
                relevant_units += 1
                stale_units += 1
            else:
                unclassified_units += 1

            found_expected.update(expected_matches)
            found_excluded.update(excluded_matches)

            unit_evaluations.append(
                UnitEvaluation(
                    unit_id=unit.id,
                    expected_concepts=expected_matches,
                    excluded_concepts=excluded_matches,
                    classification=classification,
                    provenance_status=provenance,
                )
            )

        expected_total = len(expected)
        coverage = len(found_expected) / expected_total if expected_total else 0.0
        tokens_per_relevant = None
        if found_expected and context.estimated_tokens > 0:
            tokens_per_relevant = round(context.estimated_tokens / len(found_expected), 1)

        concept_labels = {item.concept_id: item.label for item in concepts}
        return RelevanceMetrics(
            expected_concepts_total=expected_total,
            expected_concepts_found=len(found_expected),
            relevant_concept_coverage=round(coverage, 3),
            excluded_concepts_present=len(found_excluded),
            relevant_units=relevant_units,
            stale_units=stale_units,
            unclassified_units=unclassified_units,
            tokens_per_relevant_concept=tokens_per_relevant,
            concepts_found=sorted(found_expected),
            concepts_missing=sorted(
                item.concept_id for item in expected if item.concept_id not in found_expected
            ),
            stale_concepts_found=sorted(found_excluded),
            concept_labels={key: concept_labels[key] for key in sorted(concept_labels)},
            unit_evaluations=unit_evaluations,
        )
