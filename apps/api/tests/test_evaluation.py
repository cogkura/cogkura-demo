"""Comparison evaluation tests."""

from __future__ import annotations

import pytest

from cogkura_demo.agent import AgentService
from cogkura_demo.catalogue import load_catalogue
from cogkura_demo.config import DATA_DIR, DEMO_AS_OF
from cogkura_demo.context_strategies.base import (
    ComparisonMode,
    ComparisonSnapshot,
    ContextUnit,
    PreparedCustomerContext,
)
from cogkura_demo.context_strategies.cogkura import CogKuraStrategy
from cogkura_demo.context_strategies.full_history import FullHistoryStrategy
from cogkura_demo.evaluation import (
    ComparisonConfig,
    ComparisonEvaluator,
    SemanticSlotSpec,
    StaticConceptSpec,
    load_comparison_config,
    validate_comparison_config,
)
from cogkura_demo.interaction_mapper import DemoInteractionMapper, load_interactions
from cogkura_demo.memory import DemoMemory
from cogkura_demo.metrics import CogkuraTokenEstimator, TiktokenCounter
from cogkura_demo.scenarios import HistoryEvent, SemanticFactSpec, load_scenario_bundle

JACKET_PROMPT = (
    "I'm looking for a waterproof jacket for a hiking trip to Scotland "
    "next month. What would you recommend?"
)
SIZE_STATEMENT = "Actually, I'm back to a large now."


def _evaluator() -> ComparisonEvaluator:
    return ComparisonEvaluator(load_comparison_config(DATA_DIR))


def test_baseline_jacket_size_expected_from_source_events() -> None:
    bundle = load_scenario_bundle(DATA_DIR)
    evaluator = _evaluator()
    concepts = evaluator.build_concept_states(tuple(bundle.history))
    size_expected = [
        item
        for item in concepts
        if item.concept_id == "jacket_size:current:M" and item.status == "expected"
    ]
    size_stale = [
        item
        for item in concepts
        if item.concept_id == "jacket_size:stale:L" and item.status == "excluded"
    ]
    assert len(size_expected) == 1
    assert size_expected[0].evidence_event_ids == ("evt-031",)
    assert len(size_stale) == 1
    assert set(size_stale[0].evidence_event_ids) == {"evt-018", "evt-021"}


def test_concept_ids_never_overlap_expected_and_excluded() -> None:
    bundle = load_scenario_bundle(DATA_DIR)
    evaluator = _evaluator()
    concepts = evaluator.build_concept_states(tuple(bundle.history))
    expected = {item.concept_id for item in concepts if item.status == "expected"}
    excluded = {item.concept_id for item in concepts if item.status == "excluded"}
    assert expected.isdisjoint(excluded)


def test_expanded_lightweight_evidence_without_purchase() -> None:
    bundle = load_scenario_bundle(DATA_DIR)
    evaluator = _evaluator()
    context = PreparedCustomerContext(
        mode=ComparisonMode.SEARCH,
        rendered="synthetic",
        estimated_tokens=10,
        units=(
            ContextUnit(
                id="evt-019",
                text="review",
                source_event_ids=("evt-019",),
            ),
        ),
        prepare_ms=1.0,
    )
    metrics = evaluator.evaluate(context, tuple(bundle.history))
    assert "outerwear_weight_preference:lightweight" in metrics.concepts_found


def test_expanded_northpeak_support_evidence() -> None:
    bundle = load_scenario_bundle(DATA_DIR)
    evaluator = _evaluator()
    context = PreparedCustomerContext(
        mode=ComparisonMode.SEARCH,
        rendered="synthetic",
        estimated_tokens=10,
        units=(
            ContextUnit(
                id="evt-023",
                text="support",
                source_event_ids=("evt-023",),
            ),
        ),
        prepare_ms=1.0,
    )
    metrics = evaluator.evaluate(context, tuple(bundle.history))
    assert "northpeak_fit_issue" in metrics.concepts_found


def test_expanded_hiking_evidence_without_boot_purchase() -> None:
    bundle = load_scenario_bundle(DATA_DIR)
    evaluator = _evaluator()
    context = PreparedCustomerContext(
        mode=ComparisonMode.SEARCH,
        rendered="synthetic",
        estimated_tokens=10,
        units=(
            ContextUnit(
                id="evt-032",
                text="scotland jackets",
                source_event_ids=("evt-032",),
            ),
        ),
        prepare_ms=1.0,
    )
    metrics = evaluator.evaluate(context, tuple(bundle.history))
    assert "hiking_interest" in metrics.concepts_found


def test_any_ski_event_registers_stale_concept() -> None:
    bundle = load_scenario_bundle(DATA_DIR)
    evaluator = _evaluator()
    for event_id in ("evt-024", "evt-029"):
        context = PreparedCustomerContext(
            mode=ComparisonMode.SEARCH,
            rendered="synthetic",
            estimated_tokens=10,
            units=(
                ContextUnit(
                    id=event_id,
                    text="ski",
                    source_event_ids=(event_id,),
                ),
            ),
            prepare_ms=1.0,
        )
        metrics = evaluator.evaluate(context, tuple(bundle.history))
        assert "skiing_interest" in metrics.stale_concepts_found


@pytest.mark.asyncio
async def test_full_history_counts_all_ski_stale_units() -> None:
    counter = TiktokenCounter("gpt-4.1-mini")
    bundle = load_scenario_bundle(DATA_DIR)
    evaluator = _evaluator()
    snapshot = ComparisonSnapshot(
        snapshot_id="fh",
        as_of=DEMO_AS_OF,
        history=tuple(bundle.history),
        history_version=0,
    )
    prepared = await FullHistoryStrategy(token_counter=counter).prepare(
        message=JACKET_PROMPT,
        goal=bundle.scenario.goal,
        snapshot=snapshot,
    )
    metrics = evaluator.evaluate(prepared, snapshot.history)
    assert metrics.excluded_concepts_present >= 1
    assert metrics.stale_units >= 6
    assert metrics.stale_evidence_units >= 6
    assert metrics.stale_evidence_units == sum(
        1 for item in metrics.unit_evaluations if item.excluded_concepts
    )


def test_repeated_semantic_value_l_m_l() -> None:
    history = (
        HistoryEvent(
            id="evt-a",
            type="preference_statement",
            customer_id="alex",
            occurred_at="2025-01-01T00:00:00Z",
            content="size L",
            semantic_facts=[
                SemanticFactSpec(
                    predicate="jacket_size",
                    object_value="L",
                    cardinality="one",
                    polarity="affirm",
                )
            ],
        ),
        HistoryEvent(
            id="evt-b",
            type="preference_statement",
            customer_id="alex",
            occurred_at="2025-02-01T00:00:00Z",
            content="size M",
            semantic_facts=[
                SemanticFactSpec(
                    predicate="jacket_size",
                    object_value="M",
                    cardinality="one",
                    polarity="affirm",
                )
            ],
        ),
        HistoryEvent(
            id="evt-c",
            type="preference_statement",
            customer_id="alex",
            occurred_at="2025-03-01T00:00:00Z",
            content="back to L",
            semantic_facts=[
                SemanticFactSpec(
                    predicate="jacket_size",
                    object_value="L",
                    cardinality="one",
                    polarity="affirm",
                )
            ],
        ),
    )
    config = ComparisonConfig(
        scenario_id="test",
        semantic_slots=[
            SemanticSlotSpec(
                id="jacket_size",
                label="Current jacket size",
                predicate="jacket_size",
            )
        ],
    )
    evaluator = ComparisonEvaluator(config)
    concepts = evaluator.build_concept_states(history)
    expected = {item.concept_id: item for item in concepts if item.status == "expected"}
    excluded = {item.concept_id: item for item in concepts if item.status == "excluded"}
    assert expected["jacket_size:current:L"].evidence_event_ids == ("evt-c",)
    assert set(excluded["jacket_size:stale:L"].evidence_event_ids) == {"evt-a"}
    assert excluded["jacket_size:stale:M"].evidence_event_ids == ("evt-b",)

    old_l_context = PreparedCustomerContext(
        mode=ComparisonMode.SEARCH,
        rendered="synthetic",
        estimated_tokens=5,
        units=(ContextUnit(id="evt-a", text="old L", source_event_ids=("evt-a",)),),
        prepare_ms=1.0,
    )
    metrics = evaluator.evaluate(old_l_context, history)
    assert "jacket_size:current:L" not in metrics.concepts_found
    assert "jacket_size:stale:L" in metrics.stale_concepts_found


def test_validation_rejects_unknown_evidence_event() -> None:
    config = ComparisonConfig(
        scenario_id="test",
        concepts=[
            StaticConceptSpec(
                id="bad",
                label="Bad",
                status="expected",
                evidence_event_ids=["evt-missing"],
            )
        ],
    )
    with pytest.raises(ValueError, match="unknown event"):
        validate_comparison_config(config, history_event_ids={"evt-001"})


def test_validation_rejects_static_expected_excluded_overlap() -> None:
    config = ComparisonConfig(
        scenario_id="test",
        concepts=[
            StaticConceptSpec(
                id="good",
                label="Good",
                status="expected",
                evidence_event_ids=["evt-001"],
            ),
            StaticConceptSpec(
                id="bad",
                label="Bad",
                status="excluded",
                evidence_event_ids=["evt-001"],
            ),
        ],
    )
    with pytest.raises(ValueError, match="expected and excluded"):
        validate_comparison_config(config, history_event_ids={"evt-001"})


@pytest.mark.asyncio
async def test_live_size_update_flips_jacket_size_ground_truth() -> None:
    counter = TiktokenCounter("gpt-4.1-mini")
    demo_memory = DemoMemory(
        data_dir=DATA_DIR,
        token_estimator=CogkuraTokenEstimator(counter),
        memory_budget_tokens=750,
    )
    await demo_memory.initialise()
    agent = AgentService(
        demo_memory=demo_memory,
        catalogue=load_catalogue(DATA_DIR),
        token_counter=counter,
        llm_client=None,
        model_available=False,
        interaction_mapper=DemoInteractionMapper(load_interactions(DATA_DIR)),
    )
    await agent.handle_message(SIZE_STATEMENT)
    session = demo_memory.session
    evaluator = _evaluator()
    concepts = evaluator.build_concept_states(tuple(session.history))
    expected = {item.concept_id for item in concepts if item.status == "expected"}
    excluded = {item.concept_id for item in concepts if item.status == "excluded"}
    assert "jacket_size:current:L" in expected
    assert "jacket_size:stale:M" in excluded
    assert "jacket_size:stale:L" in excluded

    snapshot = session.snapshot(snapshot_id="eval-live")
    full_history = await FullHistoryStrategy(token_counter=counter).prepare(
        message=JACKET_PROMPT,
        goal=session.seed_bundle.scenario.goal,
        snapshot=snapshot,
    )
    relevance = evaluator.evaluate(full_history, snapshot.history)
    assert relevance.stale_units >= 1
    assert "jacket_size:stale:M" in relevance.stale_concepts_found
    assert "jacket_size:current:L" in relevance.concepts_found


def test_evaluator_ignores_cogkura_scores() -> None:
    bundle = load_scenario_bundle(DATA_DIR)
    evaluator = _evaluator()
    snapshot = bundle.history

    context = PreparedCustomerContext(
        mode=ComparisonMode.SEARCH,
        rendered="synthetic",
        estimated_tokens=10,
        units=(
            ContextUnit(
                id="evt-013",
                text="hiking",
                source_event_ids=("evt-013",),
                score=0.01,
            ),
        ),
        prepare_ms=1.0,
    )
    metrics = evaluator.evaluate(context, tuple(snapshot))
    assert metrics.expected_concepts_found >= 1
    assert "hiking_interest" in metrics.concepts_found


def test_unit_evaluations_include_classification() -> None:
    bundle = load_scenario_bundle(DATA_DIR)
    evaluator = _evaluator()
    context = PreparedCustomerContext(
        mode=ComparisonMode.SEARCH,
        rendered="synthetic",
        estimated_tokens=10,
        units=(
            ContextUnit(
                id="evt-018",
                text="lightweight L",
                source_event_ids=("evt-018",),
            ),
        ),
        prepare_ms=1.0,
    )
    metrics = evaluator.evaluate(context, tuple(bundle.history))
    assert len(metrics.unit_evaluations) == 1
    assert metrics.unit_evaluations[0].classification == "relevant_and_stale"


@pytest.mark.asyncio
async def test_cogkura_units_resolve_to_commerce_event_ids() -> None:
    counter = TiktokenCounter("gpt-4.1-mini")
    demo_memory = DemoMemory(
        data_dir=DATA_DIR,
        token_estimator=CogkuraTokenEstimator(counter),
        memory_budget_tokens=750,
    )
    await demo_memory.initialise()
    snapshot = demo_memory.session.snapshot(snapshot_id="eval-cogkura")
    prepared = await CogKuraStrategy(demo_memory=demo_memory).prepare(
        message=JACKET_PROMPT,
        goal=demo_memory.session.seed_bundle.scenario.goal,
        snapshot=snapshot,
    )
    event_ids = {event_id for unit in prepared.units for event_id in unit.source_event_ids}
    assert event_ids
    assert all(
        event_id.startswith("evt-") or event_id.startswith("live-") for event_id in event_ids
    )
    relevance = _evaluator().evaluate(prepared, snapshot.history)
    assert relevance.expected_concepts_found >= 1
    assert relevance.unclassified_units < len(prepared.units)
