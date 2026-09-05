"""Evidence-aware semantic ingestion policy tests."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from cogkura_demo.config import DATA_DIR, DEMO_AS_OF
from cogkura_demo.evidence_policy import (
    evidence_class_for_event,
    semantic_facts_for_observation,
)
from cogkura_demo.memory import DemoMemory
from cogkura_demo.metrics import CogkuraTokenEstimator, TiktokenCounter
from cogkura_demo.scenarios import (
    HistoryEvent,
    SemanticFactSpec,
    event_to_observation,
    load_scenario_bundle,
)

POLICY_PATH = Path(__file__).resolve().parents[1] / "src" / "cogkura_demo" / "evidence_policy.py"


def _event(
    *,
    event_id: str,
    type_: str,
    content: str,
    semantic_facts: list[SemanticFactSpec] | None = None,
    session_id: str | None = "sess-test",
    occurred_at: datetime | None = None,
) -> HistoryEvent:
    return HistoryEvent(
        id=event_id,
        type=type_,  # type: ignore[arg-type]
        customer_id="alex",
        occurred_at=occurred_at or datetime(2026, 1, 14, 20, 0, tzinfo=UTC),
        content=content,
        semantic_facts=semantic_facts or [],
        session_id=session_id,
    )


def _activity_fact(value: str) -> SemanticFactSpec:
    return SemanticFactSpec(
        predicate="activity_interest",
        object_value=value,
        cardinality="many",
        polarity="affirm",
    )


def test_isolated_browse_remains_episode_only() -> None:
    event = _event(
        event_id="evt-browse-a",
        type_="browse",
        content="Customer browsed activity-a products briefly.",
        semantic_facts=[_activity_fact("activity-a")],
    )
    observation = event_to_observation(event)
    assert observation.content == event.content
    assert "semantic_facts" not in observation.metadata
    assert semantic_facts_for_observation(event) == []
    assert evidence_class_for_event(event) == "episode_only"


def test_same_session_repeated_browse_remains_episode_only() -> None:
    session_id = "sess-brief-browse"
    events = [
        _event(
            event_id=f"evt-browse-{index}",
            type_="browse",
            content=f"Customer browsed activity-a item {index}.",
            semantic_facts=[_activity_fact("activity-a")] if index == 0 else [],
            session_id=session_id,
            occurred_at=datetime(2026, 1, 14 + index, 20, 0, tzinfo=UTC),
        )
        for index in range(6)
    ]
    for event in events:
        observation = event_to_observation(event)
        assert observation.content == event.content
        assert observation.metadata.get("semantic_facts") in (None, [])
        assert semantic_facts_for_observation(event) == []


def test_purchase_keeps_authored_activity_interest() -> None:
    event = _event(
        event_id="evt-purchase-a",
        type_="purchase",
        content="Customer purchased activity-a equipment.",
        semantic_facts=[_activity_fact("activity-a")],
    )
    observation = event_to_observation(event)
    facts = observation.metadata["semantic_facts"]
    assert facts[0]["predicate"] == "activity_interest"
    assert facts[0]["object_value"] == "activity-a"
    assert facts[0]["cardinality"] == "many"


def test_explicit_preference_keeps_authored_semantic() -> None:
    event = _event(
        event_id="evt-pref",
        type_="preference_statement",
        content="Customer said they prefer navy jackets.",
        semantic_facts=[
            SemanticFactSpec(
                predicate="colour_preference",
                object_value="navy",
                cardinality="many",
                polarity="affirm",
            )
        ],
    )
    facts = event_to_observation(event).metadata["semantic_facts"]
    assert facts[0]["predicate"] == "colour_preference"
    assert facts[0]["object_value"] == "navy"


def test_return_reason_keeps_fit_issue() -> None:
    event = HistoryEvent(
        id="evt-return",
        type="product_return",
        customer_id="alex",
        occurred_at=datetime(2025, 9, 18, 10, 15, tzinfo=UTC),
        content="Customer returned a product because the sleeves were too short.",
        product_id="northpeak-alpine-shell",
        reason="Sleeves were too short",
        semantic_facts=[
            SemanticFactSpec(
                predicate="product_fit_issue",
                object_value="northpeak-alpine-shell:sleeves_too_short",
                cardinality="many",
                polarity="affirm",
            )
        ],
    )
    facts = event_to_observation(event).metadata["semantic_facts"]
    assert facts[0]["predicate"] == "product_fit_issue"


def test_size_update_keeps_authoritative_semantic() -> None:
    event = _event(
        event_id="evt-size",
        type_="preference_statement",
        content="Customer said they are a medium now.",
        semantic_facts=[
            SemanticFactSpec(
                predicate="jacket_size",
                object_value="M",
                cardinality="one",
                polarity="affirm",
            )
        ],
    )
    facts = event_to_observation(event).metadata["semantic_facts"]
    assert facts[0]["predicate"] == "jacket_size"
    assert facts[0]["object_value"] == "M"


def test_positive_review_keeps_authored_semantic() -> None:
    event = _event(
        event_id="evt-review",
        type_="positive_outcome",
        content="Customer left a positive review of lightweight outerwear.",
        semantic_facts=[
            SemanticFactSpec(
                predicate="outerwear_weight_preference",
                object_value="lightweight",
                cardinality="one",
                polarity="affirm",
            )
        ],
    )
    facts = event_to_observation(event).metadata["semantic_facts"]
    assert facts[0]["object_value"] == "lightweight"


def test_support_interaction_is_episode_only() -> None:
    event = _event(
        event_id="evt-support",
        type_="support_interaction",
        content="Customer asked support about gaiters.",
        semantic_facts=[_activity_fact("activity-a")],
    )
    assert semantic_facts_for_observation(event) == []
    assert "semantic_facts" not in event_to_observation(event).metadata


def test_causality_follows_evidence_class_not_activity_name() -> None:
    browse_a = _event(
        event_id="evt-a",
        type_="browse",
        content="Customer browsed activity-a products briefly.",
        semantic_facts=[_activity_fact("activity-a")],
    )
    purchase_b = _event(
        event_id="evt-b",
        type_="purchase",
        content="Customer purchased activity-b equipment.",
        semantic_facts=[_activity_fact("activity-b")],
    )
    swapped_browse = _event(
        event_id="evt-c",
        type_="browse",
        content="Customer browsed activity-b products briefly.",
        semantic_facts=[_activity_fact("activity-b")],
    )
    swapped_purchase = _event(
        event_id="evt-d",
        type_="purchase",
        content="Customer purchased activity-a equipment.",
        semantic_facts=[_activity_fact("activity-a")],
    )
    assert semantic_facts_for_observation(browse_a) == []
    assert semantic_facts_for_observation(purchase_b)[0].object_value == "activity-b"
    assert semantic_facts_for_observation(swapped_browse) == []
    assert semantic_facts_for_observation(swapped_purchase)[0].object_value == "activity-a"


def test_policy_does_not_import_gold_or_evaluation() -> None:
    source = POLICY_PATH.read_text(encoding="utf-8")
    assert "evaluation" not in source
    assert "comparison.json" not in source
    assert "expected_concepts" not in source
    assert "skiing" not in source
    assert "hiking" not in source


def _active_activity_values(snapshot: list) -> set[str]:
    active_statuses = {"current", "active"}
    return {
        item.object_value.lower()
        for item in snapshot
        if item.predicate == "activity_interest" and item.status.lower() in active_statuses
    }


def _snapshot_inventory(snapshot: list) -> set[tuple[str, str, str]]:
    return {(item.predicate, item.object_value, item.status) for item in snapshot}


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
async def test_seed_replay_promotes_purchase_not_isolated_browse(
    demo_memory: DemoMemory,
) -> None:
    bundle = load_scenario_bundle(DATA_DIR)
    ski_events = [
        event
        for event in bundle.history
        if event.id in {"evt-024", "evt-025", "evt-026", "evt-027", "evt-028", "evt-029"}
    ]
    assert len(ski_events) == 6
    assert all(event.content for event in ski_events)
    snapshot = await demo_memory.semantic_snapshot(valid_at=DEMO_AS_OF)
    values = _active_activity_values(snapshot)
    assert "hiking" in values
    assert "skiing" not in values


@pytest.mark.asyncio
async def test_semantic_inventory_is_query_independent(demo_memory: DemoMemory) -> None:
    before = _snapshot_inventory(await demo_memory.semantic_snapshot(valid_at=DEMO_AS_OF))
    bundle = load_scenario_bundle(DATA_DIR)
    await demo_memory.prepare_customer_context(
        bundle.scenario.prompt,
        goal=bundle.scenario.goal,
        as_of=DEMO_AS_OF,
    )
    after = _snapshot_inventory(await demo_memory.semantic_snapshot(valid_at=DEMO_AS_OF))
    assert before == after
    values = _active_activity_values(await demo_memory.semantic_snapshot(valid_at=DEMO_AS_OF))
    assert "hiking" in values
    assert "skiing" not in values


@pytest.mark.asyncio
async def test_semantic_replay_is_deterministic() -> None:
    counter = TiktokenCounter("gpt-4.1-mini")

    async def replay() -> set[tuple[str, str, str]]:
        memory = DemoMemory(
            data_dir=DATA_DIR,
            token_estimator=CogkuraTokenEstimator(counter),
            memory_budget_tokens=750,
        )
        await memory.initialise()
        snapshot = await memory.semantic_snapshot(valid_at=DEMO_AS_OF)
        return _snapshot_inventory(snapshot)

    first = await replay()
    second = await replay()
    assert first == second
    assert first
