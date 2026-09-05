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
    kind: Literal["seed", "customer_statement", "purchase", "return", "live"] = "seed"
    is_live: bool = False


class ScenarioInfo(BaseModel):
    id: str
    name: str
    suggested_prompt: str
    goal: str
    size_update_message: str | None = None


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
    current_time: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


class ChatMessage(BaseModel):
    role: Literal["assistant"] = "assistant"
    content: str


class RelationshipEdgeResponse(BaseModel):
    relationship_id: str
    relation_type: str
    direction: str
    source_entity_id: str
    target_entity_id: str
    weight: float
    provenance: str | None = None


class AssociationPathResponse(BaseModel):
    matched_features: list[str] = Field(default_factory=list)
    seed_episode_id: str | None = None
    seed_entity_id: str | None = None
    bridge_entity_id: str | None = None
    related_episode_id: str | None = None
    hop_kind: str
    weight: float
    hop_count: int
    seed_relevance: float
    relationship_edges: list[RelationshipEdgeResponse] = Field(default_factory=list)


class ChunkMemberResponse(BaseModel):
    statement: str
    memory_kind: str
    memory_key: str
    role: Literal["primary", "support"]


class MemoryItemResponse(BaseModel):
    statement: str
    memory_kind: str
    score: float | None = None
    activation: float | None = None
    retrieval_reason: str | None = None
    selection_reason: str | None = None
    rank: int | None = None
    estimated_tokens: int | None = None
    memory_key: str | None = None
    revision_key: str | None = None
    learned_utility: float | None = None
    source_event_ids: list[str] = Field(default_factory=list)
    raw_observation_ids: list[str] = Field(default_factory=list)
    association_path: AssociationPathResponse | None = None
    relevance_tier: str | None = None
    structured_association_fit: float | None = None
    chunk_kind: str | None = None
    member_count: int | None = None
    members_omitted: int | None = None
    members: list[ChunkMemberResponse] = Field(default_factory=list)


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
    memory_process_ms: float | None = None


class MemoryValueChangeResponse(BaseModel):
    predicate: str
    before: str | None
    after: str | None
    kind: str = "current_value_changed"


class ProcessingSummaryResponse(BaseModel):
    created: int = 0
    updated: int = 0
    reinforced: int = 0
    conflicts: int = 0
    superseded: int = 0
    revisions_created: int = 0
    revisions_updated: int = 0


class LiveEventSummary(BaseModel):
    type: str
    content: str
    product_id: str | None = None
    reason: str | None = None


class MemoryMutationResponse(BaseModel):
    event: LiveEventSummary
    memory_changes: list[MemoryValueChangeResponse]
    processing: ProcessingSummaryResponse


class LearningChangeResponse(BaseModel):
    outcome: str
    helpful: int
    unhelpful: int
    incorrect: int
    memories_reinforced: int
    associations_reinforced: int
    association_items_skipped: int
    reactivated: int


class DemoOrderResponse(BaseModel):
    id: str
    product_id: str
    turn_id: str
    purchased_at: str
    returned_at: str | None = None


class PurchaseEventRequest(BaseModel):
    event_type: Literal["purchase"] = "purchase"
    product_id: str
    turn_id: str
    client_event_id: str


class ReturnEventRequest(BaseModel):
    event_type: Literal["product_return"] = "product_return"
    order_id: str
    reason_id: str
    client_event_id: str


EventRequest = PurchaseEventRequest | ReturnEventRequest


class EventResponse(BaseModel):
    status: Literal["recorded", "duplicate"] = "recorded"
    event: LiveEventSummary
    order: DemoOrderResponse | None = None
    learning: LearningChangeResponse | None = None
    memory_changes: list[MemoryValueChangeResponse] = Field(default_factory=list)
    processing: ProcessingSummaryResponse | None = None


class SemanticMemorySnapshot(BaseModel):
    memory_key: str
    slot_key: str
    revision_key: str
    revision_number: int
    statement: str
    predicate: str
    object_value: str
    status: str
    valid_from: str | None = None
    valid_until: str | None = None


class ChatCompletedResponse(BaseModel):
    status: Literal["completed"] = "completed"
    turn_id: str
    message: ChatMessage
    memory: MemoryContextResponse
    products: list[ProductResponse]
    metrics: DemoMetrics
    mutation: MemoryMutationResponse | None = None
    recommended_product_ids: list[str] = Field(default_factory=list)


class ChatInspectResponse(BaseModel):
    status: Literal["model_unavailable"] = "model_unavailable"
    turn_id: str
    memory: MemoryContextResponse
    products: list[ProductResponse]
    metrics: DemoMetrics
    detail: str = "Set OPENAI_API_KEY to run the AI response."
    mutation: MemoryMutationResponse | None = None
    recommended_product_ids: list[str] = Field(default_factory=list)


ChatResponse = ChatCompletedResponse | ChatInspectResponse


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


class ResetResponse(BaseModel):
    status: Literal["reset"] = "reset"
    ready: bool


class ComparisonRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    generate_answers: bool = True


class ComparisonSnapshotResponse(BaseModel):
    id: str
    as_of: str
    history_events: int
    history_version: int


class ComparisonContextUnitResponse(BaseModel):
    id: str
    text: str
    source_event_ids: list[str]
    score: float | None = None
    kind: str | None = None
    activation: float | None = None
    retrieval_reason: str | None = None
    association_path: AssociationPathResponse | None = None
    relevance_tier: str | None = None
    structured_association_fit: float | None = None
    chunk_kind: str | None = None
    member_count: int | None = None
    members_omitted: int | None = None
    members: list[ChunkMemberResponse] = Field(default_factory=list)


class ComparisonContextResponse(BaseModel):
    rendered: str
    estimated_tokens: int
    units: list[ComparisonContextUnitResponse]


class ContextStrategyDiagnosticsResponse(BaseModel):
    budget_tokens: int | None = None
    used_tokens: int | None = None
    remaining_tokens: int | None = None
    selected_units: int | None = None
    candidate_units: int | None = None
    unit_cap: int | None = None
    unit_cap_reached: bool | None = None
    budget_constrained: bool | None = None
    corpus_events: int | None = None
    prompt_budget_tokens: int | None = None


class UnitEvaluation(BaseModel):
    unit_id: str
    expected_concepts: list[str] = Field(default_factory=list)
    excluded_concepts: list[str] = Field(default_factory=list)
    classification: Literal["relevant", "stale", "relevant_and_stale", "unclassified"]
    provenance_status: Literal["resolved", "unresolved", "n_a"] = "n_a"


class RelevanceMetrics(BaseModel):
    expected_concepts_total: int
    expected_concepts_found: int
    relevant_concept_coverage: float
    excluded_concepts_present: int
    relevant_units: int
    stale_units: int
    stale_evidence_units: int = 0
    unclassified_units: int
    tokens_per_relevant_concept: float | None = None
    concepts_found: list[str] = Field(default_factory=list)
    concepts_missing: list[str] = Field(default_factory=list)
    stale_concepts_found: list[str] = Field(default_factory=list)
    concept_labels: dict[str, str] = Field(default_factory=dict)
    unit_evaluations: list[UnitEvaluation] = Field(default_factory=list)


class ComparisonMetrics(BaseModel):
    context_tokens: int
    context_units: int
    context_prepare_ms: float
    model_input_tokens: int | None = None
    model_output_tokens: int | None = None
    model_latency_ms: float | None = None


class ComparisonResultResponse(BaseModel):
    mode: Literal["full_history", "search", "cogkura"]
    label: str
    answer: str | None = None
    context: ComparisonContextResponse
    relevance: RelevanceMetrics
    metrics: ComparisonMetrics
    diagnostics: ContextStrategyDiagnosticsResponse | None = None
    error: str | None = None


class ComparisonResponse(BaseModel):
    snapshot: ComparisonSnapshotResponse
    message: str
    products: list[ProductResponse]
    results: list[ComparisonResultResponse]
