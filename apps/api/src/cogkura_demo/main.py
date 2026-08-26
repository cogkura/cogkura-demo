"""FastAPI application entrypoint."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from cogkura_demo.agent import AgentService
from cogkura_demo.catalogue import load_catalogue
from cogkura_demo.comparison import ComparisonService
from cogkura_demo.config import Settings, get_settings
from cogkura_demo.evaluation import ComparisonEvaluator, load_comparison_config
from cogkura_demo.events import EventService
from cogkura_demo.interaction_mapper import DemoInteractionMapper, load_interactions
from cogkura_demo.llm.openai import OpenAIResponsesClient
from cogkura_demo.memory import DemoMemory
from cogkura_demo.metrics import (
    CogkuraTokenEstimator,
    TiktokenCounter,
    estimate_full_history_tokens,
)
from cogkura_demo.models import (
    CatalogueSummary,
    ChatRequest,
    ChatResponse,
    ComparisonRequest,
    ComparisonResponse,
    CustomerSummary,
    DemoStateResponse,
    EventRequest,
    EventResponse,
    HealthResponse,
    HistorySummary,
    ResetResponse,
    ScenarioInfo,
    TimelineEvent,
)

logger = logging.getLogger(__name__)


class DemoState:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._lock = asyncio.Lock()
        self.ready = False
        self.error: str | None = None
        self.token_counter = TiktokenCounter(settings.openai_model)
        self.token_estimator = CogkuraTokenEstimator(self.token_counter)
        self.demo_memory = DemoMemory(
            data_dir=settings.data_dir,
            token_estimator=self.token_estimator,
            memory_budget_tokens=settings.cogkura_memory_budget_tokens,
        )
        self.catalogue = load_catalogue(settings.data_dir)
        interactions = load_interactions(settings.data_dir)
        self.interaction_mapper = DemoInteractionMapper(interactions)
        llm_client = None
        if settings.model_available:
            llm_client = OpenAIResponsesClient(
                api_key=settings.openai_api_key or "",
                model=settings.openai_model,
                timeout_seconds=settings.openai_timeout_seconds,
            )
        self.agent = AgentService(
            demo_memory=self.demo_memory,
            catalogue=self.catalogue,
            token_counter=self.token_counter,
            llm_client=llm_client,
            model_available=settings.model_available,
            interaction_mapper=self.interaction_mapper,
        )
        self.event_service = EventService(
            demo_memory=self.demo_memory,
            catalogue=self.catalogue,
            interaction_mapper=self.interaction_mapper,
        )
        comparison_config = load_comparison_config(settings.data_dir)
        self.comparison_service = ComparisonService(
            demo_memory=self.demo_memory,
            catalogue=self.catalogue,
            token_counter=self.token_counter,
            evaluator=ComparisonEvaluator(comparison_config),
            llm_client=llm_client,
            model_available=settings.model_available,
            search_budget_tokens=settings.search_context_budget_tokens,
            search_max_events=settings.search_max_events,
        )

    async def bootstrap(self) -> None:
        async with self._lock:
            try:
                await self.demo_memory.initialise()
                self.ready = True
                self.error = None
            except Exception as exc:  # noqa: BLE001
                self.ready = False
                self.error = str(exc)
                logger.exception("Failed to bootstrap demo memory")
                raise

    async def reset(self) -> None:
        async with self._lock:
            await self.demo_memory.reset()
            self.ready = True
            self.error = None


def get_demo_state(request: Request) -> DemoState:
    state: DemoState = request.app.state.demo
    return state


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    demo_state = DemoState(settings)
    app.state.demo = demo_state
    await demo_state.bootstrap()
    yield


app = FastAPI(title="CogKura Demo API", version="0.3.1", lifespan=lifespan)
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()


@app.get("/api/demo", response_model=DemoStateResponse)
async def demo_state_endpoint(
    state: Annotated[DemoState, Depends(get_demo_state)],
) -> DemoStateResponse:
    if not state.ready:
        raise HTTPException(status_code=503, detail=state.error or "Demo is initialising")
    session = state.demo_memory.session
    bundle = session.seed_bundle
    full_history_tokens = estimate_full_history_tokens(session.history, state.token_counter)
    waterproof_count = sum(
        1 for product in state.catalogue.products if product.category == "waterproof-jacket"
    )
    size_update = next(
        (item.message for item in state.interaction_mapper.statements if item.id == "size-large"),
        None,
    )
    timeline = session.build_timeline()
    return DemoStateResponse(
        customer=CustomerSummary(
            id=bundle.customer.id,
            name=bundle.customer.name,
            customer_since=bundle.customer.customer_since,
            order_count=session.order_count,
            return_count=session.return_count,
        ),
        scenario=ScenarioInfo(
            id=bundle.scenario.id,
            name=bundle.scenario.name,
            suggested_prompt=bundle.scenario.prompt,
            goal=bundle.scenario.goal,
            size_update_message=size_update,
        ),
        history=HistorySummary(
            events=len(session.history),
            estimated_tokens=full_history_tokens,
        ),
        timeline=[
            TimelineEvent(
                id=item.id,
                label=item.label,
                detail=item.detail,
                occurred_at=item.occurred_at,
                kind="live" if "· New" in item.label else "seed",
                is_live="· New" in item.label,
            )
            for item in timeline
        ],
        catalogue=CatalogueSummary(
            product_count=len(state.catalogue.products),
            waterproof_jacket_count=waterproof_count,
        ),
        model_available=state.settings.model_available,
        ready=state.ready,
        current_time=session.clock.current.isoformat(),
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(
    payload: ChatRequest,
    state: Annotated[DemoState, Depends(get_demo_state)],
) -> ChatResponse:
    if not state.ready:
        raise HTTPException(status_code=503, detail=state.error or "Demo is initialising")
    if len(payload.message) > state.settings.max_message_length:
        raise HTTPException(status_code=400, detail="Message too long")
    async with state._lock:
        result = await state.agent.handle_message(payload.message)
    return result.response


@app.post("/api/events", response_model=EventResponse)
async def events_endpoint(
    payload: EventRequest,
    state: Annotated[DemoState, Depends(get_demo_state)],
) -> EventResponse:
    if not state.ready:
        raise HTTPException(status_code=503, detail=state.error or "Demo is initialising")
    async with state._lock:
        try:
            result = await state.event_service.handle_event(payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.response


@app.post("/api/compare", response_model=ComparisonResponse)
async def compare_endpoint(
    payload: ComparisonRequest,
    state: Annotated[DemoState, Depends(get_demo_state)],
) -> ComparisonResponse:
    if not state.ready:
        raise HTTPException(status_code=503, detail=state.error or "Demo is initialising")
    if len(payload.message) > state.settings.max_message_length:
        raise HTTPException(status_code=400, detail="Message too long")
    async with state._lock:
        result = await state.comparison_service.compare(payload)
    return result.response


@app.post("/api/reset", response_model=ResetResponse)
async def reset_endpoint(
    state: Annotated[DemoState, Depends(get_demo_state)],
) -> ResetResponse:
    await state.reset()
    return ResetResponse(ready=state.ready)
