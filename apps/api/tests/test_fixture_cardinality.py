"""Fixture cardinality and semantic coexistence tests."""

from __future__ import annotations

import pytest

from cogkura_demo.agent import AgentService
from cogkura_demo.catalogue import load_catalogue
from cogkura_demo.config import DATA_DIR, DEMO_AS_OF
from cogkura_demo.events import EventService
from cogkura_demo.interaction_mapper import DemoInteractionMapper, load_interactions
from cogkura_demo.memory import DemoMemory
from cogkura_demo.metrics import CogkuraTokenEstimator, TiktokenCounter
from cogkura_demo.models import PurchaseEventRequest, ReturnEventRequest
from cogkura_demo.scenarios import load_scenario_bundle

JACKET_PROMPT = (
    "I'm looking for a waterproof jacket for a hiking trip to Scotland "
    "next month. What would you recommend?"
)


def _seed_fact_cardinality(event_id: str, predicate: str) -> str:
    bundle = load_scenario_bundle(DATA_DIR)
    event = next(item for item in bundle.history if item.id == event_id)
    fact = next(item for item in event.semantic_facts if item.predicate == predicate)
    return fact.cardinality


def test_seed_hiking_activity_interest_is_many() -> None:
    assert _seed_fact_cardinality("evt-013", "activity_interest") == "many"


def test_seed_skiing_activity_interest_is_many() -> None:
    assert _seed_fact_cardinality("evt-024", "activity_interest") == "many"


def test_seed_northpeak_fit_issue_is_many() -> None:
    assert _seed_fact_cardinality("evt-022", "product_fit_issue") == "many"


def test_all_seed_product_fit_issues_are_many() -> None:
    bundle = load_scenario_bundle(DATA_DIR)
    fit_facts = [
        fact
        for event in bundle.history
        for fact in event.semantic_facts
        if fact.predicate == "product_fit_issue"
    ]
    assert fit_facts
    assert all(fact.cardinality == "many" for fact in fit_facts)


def test_all_runtime_return_reason_fit_issues_are_many() -> None:
    interactions = load_interactions(DATA_DIR)
    fit_facts = [
        fact
        for reason in interactions.return_reasons
        for fact in reason.semantic_facts
        if fact.predicate == "product_fit_issue"
    ]
    assert fit_facts
    assert all(fact.cardinality == "many" for fact in fit_facts)


@pytest.fixture
async def demo_memory() -> DemoMemory:
    counter = TiktokenCounter("gpt-4.1-mini")
    memory = DemoMemory(
        data_dir=DATA_DIR,
        token_estimator=CogkuraTokenEstimator(counter),
        memory_budget_tokens=750,
    )
    await memory.initialise()
    return memory


@pytest.mark.asyncio
async def test_hiking_interest_semantic_exists_without_skiing_semantic(
    demo_memory: DemoMemory,
) -> None:
    snapshot = await demo_memory.semantic_snapshot(valid_at=DEMO_AS_OF)
    active_statuses = {"current", "active"}
    activity_values = {
        item.object_value.lower()
        for item in snapshot
        if item.predicate == "activity_interest" and item.status in active_statuses
    }
    assert "hiking" in activity_values
    assert "skiing" not in activity_values
    bundle = load_scenario_bundle(DATA_DIR)
    ski_browse = [event for event in bundle.history if event.session_id == "sess-ski-browse"]
    assert len(ski_browse) == 6
    assert all(event.type == "browse" for event in ski_browse)


@pytest.mark.asyncio
async def test_northpeak_and_ridgeshell_fit_issues_coexist(demo_memory: DemoMemory) -> None:
    counter = TiktokenCounter("gpt-4.1-mini")
    interaction_mapper = DemoInteractionMapper(load_interactions(DATA_DIR))
    agent = AgentService(
        demo_memory=demo_memory,
        catalogue=load_catalogue(DATA_DIR),
        token_counter=counter,
        llm_client=None,
        model_available=False,
        interaction_mapper=interaction_mapper,
    )
    chat = await agent.handle_message(JACKET_PROMPT)
    events = EventService(
        demo_memory=demo_memory,
        catalogue=load_catalogue(DATA_DIR),
        interaction_mapper=interaction_mapper,
    )
    purchase = await events.handle_event(
        PurchaseEventRequest(
            product_id="ridge-shell-2",
            turn_id=chat.response.turn_id,
            client_event_id="fit-coexist-purchase",
        )
    )
    order_id = purchase.response.order.id if purchase.response.order else ""
    await events.handle_event(
        ReturnEventRequest(
            order_id=order_id,
            reason_id="hood-too-restrictive",
            client_event_id="fit-coexist-return",
        )
    )

    snapshot = await demo_memory.semantic_snapshot(valid_at=demo_memory.session.clock.current)
    active_statuses = {"current", "active"}
    fit_values = {
        item.object_value
        for item in snapshot
        if item.predicate == "product_fit_issue" and item.status in active_statuses
    }
    assert "northpeak-alpine-shell:sleeves_too_short" in fit_values
    assert "ridge-shell-2:hood_too_restrictive" in fit_values
