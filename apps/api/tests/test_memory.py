"""CogKura memory integration tests."""

from __future__ import annotations

import pytest

from cogkura_demo.config import DATA_DIR, DEMO_AS_OF
from cogkura_demo.memory import DemoMemory
from cogkura_demo.metrics import CogkuraTokenEstimator, TiktokenCounter
from cogkura_demo.scenarios import load_scenario_bundle


def _looks_like_uuid(value: str) -> bool:
    return len(value) == 36 and value.count("-") == 4


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
async def test_prepare_context_returns_bounded_memory(demo_memory: DemoMemory) -> None:
    bundle = load_scenario_bundle(DATA_DIR)
    context = await demo_memory.prepare_customer_context(
        bundle.scenario.prompt,
        goal=bundle.scenario.goal,
        as_of=DEMO_AS_OF,
    )
    mapped = demo_memory.map_context(context)
    assert mapped.estimated_tokens <= 750
    assert mapped.estimated_tokens > 0
    statements = " ".join(item.statement.lower() for item in mapped.items)
    keywords = ("hiking", "lightweight", "northpeak", "medium", "m")
    assert any(token in statements for token in keywords)
    event_ids = [event_id for item in mapped.items for event_id in item.source_event_ids]
    assert event_ids
    assert all(not _looks_like_uuid(event_id) for event_id in event_ids)
    assert any(event_id.startswith("evt-") for event_id in event_ids)


@pytest.mark.asyncio
async def test_render_excludes_full_history(demo_memory: DemoMemory) -> None:
    bundle = load_scenario_bundle(DATA_DIR)
    context = await demo_memory.prepare_customer_context(
        bundle.scenario.prompt,
        goal=bundle.scenario.goal,
        as_of=DEMO_AS_OF,
    )
    rendered = context.render()
    assert "camp mugs" not in rendered.lower() or len(rendered) < 5000
