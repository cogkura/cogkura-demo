"""HTTP API models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CustomerSummary(BaseModel):
    id: str
    name: str
    customer_since: str
    order_count: int
    return_count: int


class TimelineEvent(BaseModel):
    id: str
    label: str
    detail: str
    occurred_at: str


class ScenarioInfo(BaseModel):
    id: str
    name: str
    suggested_prompt: str
    goal: str


class HistorySummary(BaseModel):
    events: int
    estimated_tokens: int


class CatalogueSummary(BaseModel):
    product_count: int
    waterproof_jacket_count: int


class DemoStateResponse(BaseModel):
    customer: CustomerSummary
    scenario: ScenarioInfo
    history: HistorySummary
    timeline: list[TimelineEvent]
    catalogue: CatalogueSummary
    model_available: bool
    ready: bool


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


class ChatMessage(BaseModel):
    role: Literal["assistant"] = "assistant"
    content: str


class MemoryItemResponse(BaseModel):
    statement: str
    memory_kind: str
    score: float | None = None
    activation: float | None = None
    retrieval_reason: str | None = None
    selection_reason: str | None = None
    rank: int | None = None
    estimated_tokens: int | None = None


class MemoryAssessmentResponse(BaseModel):
    flags: list[str]


class MemoryContextResponse(BaseModel):
    rendered: str
    estimated_tokens: int
    items: list[MemoryItemResponse]
    assessment: MemoryAssessmentResponse


class ProductResponse(BaseModel):
    id: str
    name: str
    category: str
    price_gbp: int
    waterproof: bool
    weight_grams: int
    colours: list[str]
    sizes: list[str]
    fit: str
    description: str


class DemoMetrics(BaseModel):
    history_events: int
    estimated_full_history_tokens: int
    memory_items: int
    memory_context_tokens: int
    history_context_reduction_percent: float
    model_input_tokens: int | None = None
    model_output_tokens: int | None = None
    memory_prepare_ms: float
    product_search_ms: float
    model_latency_ms: float | None = None
    total_latency_ms: float


class ChatCompletedResponse(BaseModel):
    status: Literal["completed"] = "completed"
    message: ChatMessage
    memory: MemoryContextResponse
    products: list[ProductResponse]
    metrics: DemoMetrics


class ChatInspectResponse(BaseModel):
    status: Literal["model_unavailable"] = "model_unavailable"
    memory: MemoryContextResponse
    products: list[ProductResponse]
    metrics: DemoMetrics
    detail: str = "Set OPENAI_API_KEY to run the AI response."


ChatResponse = ChatCompletedResponse | ChatInspectResponse


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


class ResetResponse(BaseModel):
    status: Literal["reset"] = "reset"
    ready: bool
