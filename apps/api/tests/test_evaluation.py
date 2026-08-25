"""Comparison evaluation tests."""

from __future__ import annotations

import pytest

from cogkura_demo.agent import AgentService
from cogkura_demo.catalogue import load_catalogue
from cogkura_demo.config import DATA_DIR
from cogkura_demo.context_strategies.base import (
    ComparisonMode,
    ContextUnit,
    PreparedCustomerContext,
)
from cogkura_demo.context_strategies.cogkura import CogKuraStrategy
from cogkura_demo.context_strategies.full_history import FullHistoryStrategy
from cogkura_demo.evaluation import ComparisonEvaluator, load_comparison_config
from cogkura_demo.interaction_mapper import DemoInteractionMapper, load_interactions
from cogkura_demo.memory import DemoMemory
from cogkura_demo.metrics import CogkuraTokenEstimator, TiktokenCounter
from cogkura_demo.scenarios import load_scenario_bundle

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
        if item.concept_id == "jacket_size:M" and item.status == "expected"
    ]
    size_stale = [
        item
        for item in concepts
        if item.concept_id == "jacket_size:L" and item.status == "excluded"
    ]
    assert len(size_expected) == 1
    assert size_expected[0].evidence_event_ids == ("evt-031",)
    assert any(item.evidence_event_ids == ("evt-018",) for item in size_stale)
    assert any(item.evidence_event_ids == ("evt-021",) for item in size_stale)


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
    assert "jacket_size:L" in expected
    assert "jacket_size:M" in excluded

    snapshot = session.snapshot(snapshot_id="eval-live")
    full_history = await FullHistoryStrategy(token_counter=counter).prepare(
        message=JACKET_PROMPT,
        goal=session.seed_bundle.scenario.goal,
        snapshot=snapshot,
    )
    relevance = evaluator.evaluate(full_history, snapshot.history)
    assert relevance.stale_units >= 1
    assert "jacket_size:M" in relevance.stale_concepts_found
    assert "jacket_size:L" in relevance.concepts_found


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
