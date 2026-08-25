"""0.2.0 live memory adaptation tests."""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from httpx import ASGITransport, AsyncClient

from cogkura_demo.agent import AgentService
from cogkura_demo.catalogue import load_catalogue
from cogkura_demo.config import DATA_DIR, DEMO_AS_OF, get_settings
from cogkura_demo.events import EventService
from cogkura_demo.interaction_mapper import DemoInteractionMapper, load_interactions
from cogkura_demo.llm.openai import LLMResponse
from cogkura_demo.main import DemoState, app
from cogkura_demo.memory import DemoMemory
from cogkura_demo.metrics import CogkuraTokenEstimator, TiktokenCounter
from cogkura_demo.models import PurchaseEventRequest, ReturnEventRequest

SIZE_STATEMENT = "Actually, I'm back to a large now."
JACKET_PROMPT = (
    "I'm looking for a waterproof jacket for a hiking trip to Scotland "
    "next month. What would you recommend?"
)


@dataclass
class FakeLLM:
    async def respond(self, **kwargs) -> LLMResponse:  # type: ignore[no-untyped-def]
        memory = kwargs["customer_context"].lower()
        assert "jacket size l" in memory or "size l" in memory or "large" in memory
        return LLMResponse(
            content="Try RidgeShell 2 in large.",
            request_id="resp-live-1",
            input_tokens=120,
            output_tokens=25,
        )


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


@pytest.fixture
def interaction_mapper() -> DemoInteractionMapper:
    return DemoInteractionMapper(load_interactions(DATA_DIR))


@pytest.fixture
async def agent_inspect_only(
    demo_memory: DemoMemory,
    interaction_mapper: DemoInteractionMapper,
) -> AgentService:
    counter = TiktokenCounter("gpt-4.1-mini")
    return AgentService(
        demo_memory=demo_memory,
        catalogue=load_catalogue(DATA_DIR),
        token_counter=counter,
        llm_client=None,
        model_available=False,
        interaction_mapper=interaction_mapper,
    )


@pytest.fixture
async def agent_with_fake_llm(
    demo_memory: DemoMemory,
    interaction_mapper: DemoInteractionMapper,
) -> AgentService:
    counter = TiktokenCounter("gpt-4.1-mini")
    return AgentService(
        demo_memory=demo_memory,
        catalogue=load_catalogue(DATA_DIR),
        token_counter=counter,
        llm_client=FakeLLM(),
        model_available=True,
        interaction_mapper=interaction_mapper,
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
async def test_baseline_jacket_size_is_medium(demo_memory: DemoMemory) -> None:
    snapshot = await demo_memory.semantic_snapshot(valid_at=DEMO_AS_OF)
    current_sizes = [
        item.object_value.upper()
        for item in snapshot
        if item.predicate == "jacket_size" and item.status in {"current", "active"}
    ]
    assert current_sizes == ["M"]


@pytest.mark.asyncio
async def test_size_statement_supersedes_and_same_turn_context(
    agent_inspect_only: AgentService,
) -> None:
    result = await agent_inspect_only.handle_message(SIZE_STATEMENT)
    assert result.response.mutation is not None
    processing = result.response.mutation.processing
    assert processing.revisions_created >= 1 or processing.updated >= 1
    snapshot = await agent_inspect_only._demo_memory.semantic_snapshot(
        valid_at=agent_inspect_only._demo_memory.session.clock.current,
    )
    current_sizes = [
        item.object_value.lower()
        for item in snapshot
        if item.predicate == "jacket_size" and item.status in {"current", "active"}
    ]
    assert "l" in current_sizes


@pytest.mark.asyncio
async def test_fake_llm_chat_after_size_update(agent_with_fake_llm: AgentService) -> None:
    await agent_with_fake_llm.handle_message(SIZE_STATEMENT)
    result = await agent_with_fake_llm.handle_message(JACKET_PROMPT)
    assert result.response.status == "completed"


@pytest.mark.asyncio
async def test_purchase_learning_and_order(
    demo_memory: DemoMemory,
    interaction_mapper: DemoInteractionMapper,
) -> None:
    counter = TiktokenCounter("gpt-4.1-mini")
    agent = AgentService(
        demo_memory=demo_memory,
        catalogue=load_catalogue(DATA_DIR),
        token_counter=counter,
        llm_client=None,
        model_available=False,
        interaction_mapper=interaction_mapper,
    )
    chat = await agent.handle_message(JACKET_PROMPT)
    assert chat.response.turn_id
    events = EventService(
        demo_memory=demo_memory,
        catalogue=load_catalogue(DATA_DIR),
        interaction_mapper=interaction_mapper,
    )
    purchase = await events.handle_event(
        PurchaseEventRequest(
            product_id="ridge-shell-2",
            turn_id=chat.response.turn_id,
            client_event_id="purchase-1",
        )
    )
    assert purchase.response.order is not None
    assert purchase.response.learning is not None
    assert purchase.response.learning.helpful > 0
    session = demo_memory.session
    assert session.order_count == session.seed_bundle.customer.order_count + 1
    assert len(session.live_orders) == 1


@pytest.mark.asyncio
async def test_return_learning_and_fit_issue(
    demo_memory: DemoMemory,
    interaction_mapper: DemoInteractionMapper,
) -> None:
    counter = TiktokenCounter("gpt-4.1-mini")
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
            client_event_id="purchase-return-flow",
        )
    )
    order_id = purchase.response.order.id if purchase.response.order else ""
    returned = await events.handle_event(
        ReturnEventRequest(
            order_id=order_id,
            reason_id="hood-too-restrictive",
            client_event_id="return-1",
        )
    )
    assert returned.response.learning is not None
    assert returned.response.learning.unhelpful > 0
    seed_returns = demo_memory.session.seed_bundle.customer.return_count
    assert demo_memory.session.return_count == seed_returns + 1

    context = await demo_memory.prepare_customer_context(
        JACKET_PROMPT,
        goal=demo_memory.session.seed_bundle.scenario.goal,
        as_of=demo_memory.session.clock.current,
    )
    rendered = context.render().lower()
    assert "hood" in rendered or "restrictive" in rendered or "fit" in rendered


@pytest.mark.asyncio
async def test_duplicate_client_event_id_is_idempotent(
    demo_memory: DemoMemory,
    interaction_mapper: DemoInteractionMapper,
) -> None:
    counter = TiktokenCounter("gpt-4.1-mini")
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
    first = await events.handle_event(
        PurchaseEventRequest(
            product_id="ridge-shell-2",
            turn_id=chat.response.turn_id,
            client_event_id="dup-1",
        )
    )
    second = await events.handle_event(
        PurchaseEventRequest(
            product_id="ridge-shell-2",
            turn_id=chat.response.turn_id,
            client_event_id="dup-1",
        )
    )
    assert second.response.status == "duplicate"
    assert len(demo_memory.session.live_orders) == 1
    assert first.response.order is not None


@pytest.mark.asyncio
async def test_reset_clears_live_state(client: AsyncClient) -> None:
    await client.post("/api/chat", json={"message": SIZE_STATEMENT})
    reset = await client.post("/api/reset")
    assert reset.status_code == 200
    demo = await client.get("/api/demo")
    payload = demo.json()
    assert payload["current_time"].startswith(DEMO_AS_OF.isoformat()[:10])
    chat = await client.post("/api/chat", json={"message": JACKET_PROMPT})
    memory = chat.json()["memory"]["rendered"].lower()
    assert "size m" in memory or "medium" in memory
