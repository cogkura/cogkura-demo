"""Deterministic comparison relevance evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field

from cogkura_demo.context_strategies.base import PreparedCustomerContext
from cogkura_demo.metrics import sort_history_chronologically
from cogkura_demo.models import RelevanceMetrics
from cogkura_demo.scenarios import HistoryEvent


class StaticConceptSpec(BaseModel):
    id: str
    label: str
    status: str
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
    status: str
    evidence_event_ids: tuple[str, ...]


def load_comparison_config(data_dir: Path) -> ComparisonConfig:
    path = data_dir / "alex" / "comparison.json"
    return ComparisonConfig.model_validate_json(path.read_text(encoding="utf-8"))


def _resolve_semantic_slot_concepts(
    history: tuple[HistoryEvent, ...],
    slots: list[SemanticSlotSpec],
) -> list[ConceptState]:
    concepts: list[ConceptState] = []
    ordered = sort_history_chronologically(list(history))
    for slot in slots:
        values: list[tuple[str, str]] = []
        for event in ordered:
            for fact in event.semantic_facts:
                if (
                    fact.predicate == slot.predicate
                    and fact.cardinality == "one"
                    and fact.polarity == "affirm"
                ):
                    values.append((fact.object_value.upper(), event.id))
        if not values:
            continue
        current_value, current_event_id = values[-1]
        concepts.append(
            ConceptState(
                concept_id=f"{slot.predicate}:{current_value}",
                label=f"{slot.label}: {current_value}",
                status="expected",
                evidence_event_ids=(current_event_id,),
            )
        )
        for value, event_id in values[:-1]:
            concepts.append(
                ConceptState(
                    concept_id=f"{slot.predicate}:{value}",
                    label=f"Previous {slot.label.lower()}: {value}",
                    status="excluded",
                    evidence_event_ids=(event_id,),
                )
            )
    return concepts


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
        expected = [item for item in concepts if item.status == "expected"]
        excluded = [item for item in concepts if item.status == "excluded"]

        found_expected: set[str] = set()
        found_excluded: set[str] = set()
        relevant_units = 0
        stale_units = 0
        unclassified_units = 0

        for unit in context.units:
            unit_concepts: set[str] = set()
            for event_id in unit.source_event_ids:
                unit_concepts.update(event_to_concepts.get(event_id, set()))
            if not unit_concepts:
                unclassified_units += 1
                continue
            is_relevant = bool(unit_concepts & {item.concept_id for item in expected})
            is_stale = bool(unit_concepts & {item.concept_id for item in excluded})
            if is_relevant:
                relevant_units += 1
            if is_stale:
                stale_units += 1
            if not is_relevant and not is_stale:
                unclassified_units += 1
            found_expected.update(unit_concepts & {item.concept_id for item in expected})
            found_excluded.update(unit_concepts & {item.concept_id for item in excluded})

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
        )
