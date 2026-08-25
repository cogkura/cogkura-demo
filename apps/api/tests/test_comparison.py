"""Comparison API and orchestration tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from cogkura_demo.catalogue import load_catalogue
from cogkura_demo.comparison import ComparisonService
from cogkura_demo.config import DATA_DIR, get_settings
from cogkura_demo.evaluation import ComparisonEvaluator, load_comparison_config
from cogkura_demo.llm.openai import LLMResponse
from cogkura_demo.main import DemoState, app
from cogkura_demo.memory import DemoMemory
from cogkura_demo.metrics import CogkuraTokenEstimator, TiktokenCounter
from cogkura_demo.models import ComparisonRequest

JACKET_PROMPT = (
    "I'm looking for a waterproof jacket for a hiking trip to Scotland "
    "next month. What would you recommend?"
)
SIZE_STATEMENT = "Actually, I'm back to a large now."


@dataclass
class ComparisonLLM:
    contexts: list[str] = field(default_factory=list)
    assessment_flags: list[list[str]] = field(default_factory=list)

    async def respond(self, **kwargs) -> LLMResponse:  # type: ignore[no-untyped-def]
        self.contexts.append(kwargs["customer_context"])
        self.assessment_flags.append(list(kwargs.get("assessment_flags", [])))
        return LLMResponse(
            content=f"answer-{len(self.contexts)}",
            request_id=f"resp-compare-{len(self.contexts)}",
            input_tokens=50,
            output_tokens=10,
        )


@pytest.fixture
async def client() -> AsyncClient:
    settings = get_settings()
    demo_state = DemoState(settings)
    app.state.demo = demo_state
    await demo_state.bootstrap()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client


@pytest.mark.asyncio
async def test_compare_generate_answers_false_returns_three_results_without_mutation(
    client: AsyncClient,
) -> None:
    demo_before = (await client.get("/api/demo")).json()
    response = await client.post(
        "/api/compare",
        json={"message": JACKET_PROMPT, "generate_answers": False},
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["results"]) == 3
    assert [item["mode"] for item in payload["results"]] == [
        "full_history",
        "search",
        "cogkura",
    ]
    assert all(item["answer"] is None for item in payload["results"])
    demo_after = (await client.get("/api/demo")).json()
    assert demo_after["history"]["events"] == demo_before["history"]["events"]
    assert demo_after["current_time"] == demo_before["current_time"]


@pytest.mark.asyncio
async def test_compare_fake_llm_only_customer_context_differs() -> None:
    settings = get_settings()
    counter = TiktokenCounter(settings.openai_model)
    demo_memory = DemoMemory(
        data_dir=DATA_DIR,
        token_estimator=CogkuraTokenEstimator(counter),
        memory_budget_tokens=settings.cogkura_memory_budget_tokens,
    )
    await demo_memory.initialise()
    fake_llm = ComparisonLLM()
    service = ComparisonService(
        demo_memory=demo_memory,
        catalogue=load_catalogue(DATA_DIR),
        token_counter=counter,
        evaluator=ComparisonEvaluator(load_comparison_config(DATA_DIR)),
        llm_client=fake_llm,
        model_available=True,
        search_budget_tokens=settings.search_context_budget_tokens,
        search_max_events=settings.search_max_events,
    )
    result = await service.compare(ComparisonRequest(message=JACKET_PROMPT, generate_answers=True))
    assert len(result.response.results) == 3
    assert len(fake_llm.contexts) == 3
    assert len({context for context in fake_llm.contexts}) >= 2
    assert all(flags == [] for flags in fake_llm.assessment_flags)


@pytest.mark.asyncio
async def test_record_context_use_only_after_cogkura_generated_success() -> None:
    settings = get_settings()
    counter = TiktokenCounter(settings.openai_model)
    demo_memory = DemoMemory(
        data_dir=DATA_DIR,
        token_estimator=CogkuraTokenEstimator(counter),
        memory_budget_tokens=settings.cogkura_memory_budget_tokens,
    )
    await demo_memory.initialise()
    fake_llm = ComparisonLLM()
    service = ComparisonService(
        demo_memory=demo_memory,
        catalogue=load_catalogue(DATA_DIR),
        token_counter=counter,
        evaluator=ComparisonEvaluator(load_comparison_config(DATA_DIR)),
        llm_client=fake_llm,
        model_available=True,
        search_budget_tokens=settings.search_context_budget_tokens,
        search_max_events=settings.search_max_events,
    )
    record_spy = AsyncMock(wraps=demo_memory.record_context_use)
    demo_memory.record_context_use = record_spy  # type: ignore[method-assign]

    await service.compare(ComparisonRequest(message=JACKET_PROMPT, generate_answers=True))
    assert record_spy.await_count == 1

    await service.compare(ComparisonRequest(message=JACKET_PROMPT, generate_answers=False))
    assert record_spy.await_count == 1


@pytest.mark.asyncio
async def test_compare_after_live_size_update_marks_stale_medium(
    client: AsyncClient,
) -> None:
    await client.post("/api/chat", json={"message": SIZE_STATEMENT})
    response = await client.post(
        "/api/compare",
        json={"message": JACKET_PROMPT, "generate_answers": False},
    )
    assert response.status_code == 200
    payload = response.json()
    full_history = next(item for item in payload["results"] if item["mode"] == "full_history")
    full_ids = {
        event_id
        for unit in full_history["context"]["units"]
        for event_id in unit["source_event_ids"]
    }
    assert "evt-031" in full_ids
    assert any(unit["id"].startswith("live-") for unit in full_history["context"]["units"])
    full_relevance = full_history["relevance"]
    assert full_relevance["stale_units"] >= 1
    assert "jacket_size:M" in full_relevance["stale_concepts_found"]
    assert "jacket_size:L" in full_relevance["concepts_found"]
