"""Agent orchestration tests."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from cogkura_demo.agent import AgentService
from cogkura_demo.catalogue import load_catalogue
from cogkura_demo.config import DATA_DIR
from cogkura_demo.interaction_mapper import DemoInteractionMapper, load_interactions
from cogkura_demo.llm.openai import LLMResponse
from cogkura_demo.memory import DemoMemory
from cogkura_demo.metrics import CogkuraTokenEstimator, TiktokenCounter


@dataclass
class FakeLLM:
    async def respond(self, **kwargs) -> LLMResponse:  # type: ignore[no-untyped-def]
        assert "customer_context" in kwargs
        memory = kwargs["customer_context"]
        assert "2025-02-03 | browse" not in memory
        return LLMResponse(
            content="Try RidgeShell 2 in medium.",
            request_id="resp-test-1",
            input_tokens=100,
            output_tokens=20,
        )


@pytest.fixture
async def agent_with_fake_llm() -> AgentService:
    counter = TiktokenCounter("gpt-4.1-mini")
    demo_memory = DemoMemory(
        data_dir=DATA_DIR,
        token_estimator=CogkuraTokenEstimator(counter),
        memory_budget_tokens=750,
    )
    await demo_memory.initialise()
    interaction_mapper = DemoInteractionMapper(load_interactions(DATA_DIR))
    return AgentService(
        demo_memory=demo_memory,
        catalogue=load_catalogue(DATA_DIR),
        token_counter=counter,
        llm_client=FakeLLM(),
        model_available=True,
        interaction_mapper=interaction_mapper,
    )


@pytest.mark.asyncio
async def test_agent_completed_response(agent_with_fake_llm: AgentService) -> None:
    bundle = agent_with_fake_llm._demo_memory.bundle
    result = await agent_with_fake_llm.handle_message(bundle.scenario.prompt)
    assert result.response.status == "completed"
    assert result.response.message.content
    assert result.response.metrics.model_input_tokens == 100
    assert result.response.turn_id == "turn-001"


@pytest.mark.asyncio
async def test_agent_inspect_only() -> None:
    counter = TiktokenCounter("gpt-4.1-mini")
    demo_memory = DemoMemory(
        data_dir=DATA_DIR,
        token_estimator=CogkuraTokenEstimator(counter),
        memory_budget_tokens=750,
    )
    await demo_memory.initialise()
    interaction_mapper = DemoInteractionMapper(load_interactions(DATA_DIR))
    agent = AgentService(
        demo_memory=demo_memory,
        catalogue=load_catalogue(DATA_DIR),
        token_counter=counter,
        llm_client=None,
        model_available=False,
        interaction_mapper=interaction_mapper,
    )
    result = await agent.handle_message("Need a waterproof jacket.")
    assert result.response.status == "model_unavailable"
    assert result.context is not None
