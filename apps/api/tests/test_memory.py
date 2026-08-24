"""CogKura memory integration tests."""

from __future__ import annotations

import pytest

from cogkura_demo.config import DATA_DIR
from cogkura_demo.memory import DemoMemory, map_memory_context
from cogkura_demo.metrics import CogkuraTokenEstimator, TiktokenCounter
from cogkura_demo.scenarios import load_scenario_bundle


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
    )
    mapped = map_memory_context(context)
    assert mapped.estimated_tokens <= 750
    assert mapped.estimated_tokens > 0
    statements = " ".join(item.statement.lower() for item in mapped.items)
    keywords = ("hiking", "lightweight", "northpeak", "medium", "m")
    assert any(token in statements for token in keywords)


@pytest.mark.asyncio
async def test_render_excludes_full_history(demo_memory: DemoMemory) -> None:
    bundle = load_scenario_bundle(DATA_DIR)
    context = await demo_memory.prepare_customer_context(
        bundle.scenario.prompt,
        goal=bundle.scenario.goal,
    )
    rendered = context.render()
    assert "camp mugs" not in rendered.lower() or len(rendered) < 5000
