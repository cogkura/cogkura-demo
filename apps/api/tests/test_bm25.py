"""BM25 search strategy tests."""

from __future__ import annotations

import pytest

from cogkura_demo.catalogue import load_catalogue
from cogkura_demo.config import DATA_DIR, DEMO_AS_OF, get_settings
from cogkura_demo.context_strategies.base import ComparisonSnapshot
from cogkura_demo.context_strategies.bm25 import Bm25SearchStrategy, build_search_document
from cogkura_demo.metrics import TiktokenCounter
from cogkura_demo.scenarios import load_scenario_bundle

JACKET_PROMPT = (
    "I'm looking for a waterproof jacket for a hiking trip to Scotland "
    "next month. What would you recommend?"
)


def _snapshot(bundle_history: list) -> ComparisonSnapshot:
    return ComparisonSnapshot(
        snapshot_id="bm25-test",
        as_of=DEMO_AS_OF,
        history=tuple(bundle_history),
        history_version=0,
    )


@pytest.mark.asyncio
async def test_search_stays_within_budget() -> None:
    settings = get_settings()
    bundle = load_scenario_bundle(DATA_DIR)
    counter = TiktokenCounter("gpt-4.1-mini")
    strategy = Bm25SearchStrategy(
        token_counter=counter,
        catalogue=load_catalogue(DATA_DIR),
        budget_tokens=settings.search_context_budget_tokens,
        max_events=settings.search_max_events,
    )
    prepared = await strategy.prepare(
        message=JACKET_PROMPT,
        goal=bundle.scenario.goal,
        snapshot=_snapshot(bundle.history),
    )
    assert prepared.estimated_tokens <= settings.search_context_budget_tokens
    assert len(prepared.units) <= settings.search_max_events
    assert prepared.diagnostics.budget_constrained is True
    assert prepared.diagnostics.unit_cap_reached is False


@pytest.mark.asyncio
async def test_default_search_not_limited_by_event_cap() -> None:
    settings = get_settings()
    assert settings.search_max_events == 100
    bundle = load_scenario_bundle(DATA_DIR)
    counter = TiktokenCounter("gpt-4.1-mini")
    strategy = Bm25SearchStrategy(
        token_counter=counter,
        catalogue=load_catalogue(DATA_DIR),
        budget_tokens=settings.search_context_budget_tokens,
        max_events=settings.search_max_events,
    )
    prepared = await strategy.prepare(
        message=JACKET_PROMPT,
        goal=bundle.scenario.goal,
        snapshot=_snapshot(bundle.history),
    )
    assert prepared.diagnostics.unit_cap_reached is False
    assert prepared.diagnostics.budget_constrained is True


@pytest.mark.asyncio
async def test_search_event_cap_diagnostics() -> None:
    bundle = load_scenario_bundle(DATA_DIR)
    counter = TiktokenCounter("gpt-4.1-mini")
    strategy = Bm25SearchStrategy(
        token_counter=counter,
        catalogue=load_catalogue(DATA_DIR),
        budget_tokens=10_000,
        max_events=2,
    )
    prepared = await strategy.prepare(
        message=JACKET_PROMPT,
        goal=bundle.scenario.goal,
        snapshot=_snapshot(bundle.history),
    )
    assert prepared.diagnostics.unit_cap_reached is True
    assert prepared.diagnostics.budget_constrained is False
    assert len(prepared.units) == 2


@pytest.mark.asyncio
async def test_search_budget_diagnostics() -> None:
    bundle = load_scenario_bundle(DATA_DIR)
    counter = TiktokenCounter("gpt-4.1-mini")
    strategy = Bm25SearchStrategy(
        token_counter=counter,
        catalogue=load_catalogue(DATA_DIR),
        budget_tokens=50,
        max_events=100,
    )
    prepared = await strategy.prepare(
        message=JACKET_PROMPT,
        goal=bundle.scenario.goal,
        snapshot=_snapshot(bundle.history),
    )
    assert prepared.diagnostics.budget_constrained is True
    assert prepared.diagnostics.unit_cap_reached is False
    assert prepared.estimated_tokens <= 50


@pytest.mark.asyncio
async def test_search_query_uses_goal_and_message() -> None:
    bundle = load_scenario_bundle(DATA_DIR)
    counter = TiktokenCounter("gpt-4.1-mini")
    strategy = Bm25SearchStrategy(
        token_counter=counter,
        catalogue=load_catalogue(DATA_DIR),
        budget_tokens=750,
        max_events=20,
    )
    events = list(bundle.history)
    with_goal = strategy._rank_events(
        events=events,
        goal=bundle.scenario.goal,
        message=JACKET_PROMPT,
    )
    without_goal = strategy._rank_events(
        events=events,
        goal="",
        message=JACKET_PROMPT,
    )
    assert (
        with_goal[0].event.id != without_goal[0].event.id
        or with_goal[0].score != without_goal[0].score
    )


def test_search_document_excludes_evaluation_labels() -> None:
    bundle = load_scenario_bundle(DATA_DIR)
    catalogue = load_catalogue(DATA_DIR)
    event = next(item for item in bundle.history if item.id == "evt-013")
    event_with_label = event.model_copy(
        update={"metadata": {"evaluation_label": "expected_hiking_interest"}}
    )
    document = build_search_document(event_with_label, catalogue)
    assert "expected_hiking_interest" not in document
    assert "hiking" in document.lower() or event.content.lower() in document.lower()


def test_default_search_budget_matches_cogkura_budget() -> None:
    settings = get_settings()
    assert settings.search_context_budget_tokens == settings.cogkura_memory_budget_tokens
