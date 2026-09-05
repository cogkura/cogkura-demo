export type CustomerSummary = {
  id: string;
  name: string;
  customer_since: string;
  order_count: number;
  return_count: number;
};

export type TimelineEvent = {
  id: string;
  label: string;
  detail: string;
  occurred_at: string;
  kind?: string;
  is_live?: boolean;
};

export type ScenarioInfo = {
  id: string;
  name: string;
  suggested_prompt: string;
  goal: string;
  size_update_message?: string | null;
};

export type HistorySummary = {
  events: number;
  estimated_tokens: number;
};

export type CatalogueSummary = {
  product_count: number;
  waterproof_jacket_count: number;
};

export type DemoStateResponse = {
  customer: CustomerSummary;
  scenario: ScenarioInfo;
  history: HistorySummary;
  timeline: TimelineEvent[];
  catalogue: CatalogueSummary;
  model_available: boolean;
  ready: boolean;
  current_time?: string;
};

export type RelationshipEdge = {
  relationship_id: string;
  relation_type: string;
  direction: string;
  source_entity_id: string;
  target_entity_id: string;
  weight: number;
  provenance?: string | null;
};

export type AssociationPath = {
  matched_features: string[];
  seed_episode_id?: string | null;
  seed_entity_id?: string | null;
  bridge_entity_id?: string | null;
  related_episode_id?: string | null;
  hop_kind: string;
  weight: number;
  hop_count: number;
  seed_relevance: number;
  relationship_edges: RelationshipEdge[];
};

export type ChunkMember = {
  statement: string;
  memory_kind: string;
  memory_key: string;
  role: "primary" | "support";
};

export type MemoryItem = {
  statement: string;
  memory_kind: string;
  score: number | null;
  activation: number | null;
  retrieval_reason: string | null;
  selection_reason: string | null;
  rank: number | null;
  estimated_tokens: number | null;
  memory_key?: string | null;
  revision_key?: string | null;
  learned_utility?: number | null;
  association_path?: AssociationPath | null;
  relevance_tier?: string | null;
  structured_association_fit?: number | null;
  chunk_kind?: string | null;
  member_count?: number | null;
  members_omitted?: number | null;
  members?: ChunkMember[];
};

export type MemoryAssessment = {
  flags: string[];
};

export type MemoryContext = {
  rendered: string;
  estimated_tokens: number;
  items: MemoryItem[];
  assessment: MemoryAssessment;
};

export type Product = {
  id: string;
  name: string;
  category: string;
  price_gbp: number;
  waterproof: boolean;
  weight_grams: number;
  colours: string[];
  sizes: string[];
  fit: string;
  description: string;
};

export type DemoMetrics = {
  history_events: number;
  estimated_full_history_tokens: number;
  memory_items: number;
  memory_context_tokens: number;
  history_context_reduction_percent: number;
  model_input_tokens: number | null;
  model_output_tokens: number | null;
  memory_prepare_ms: number;
  product_search_ms: number;
  model_latency_ms: number | null;
  total_latency_ms: number;
  memory_process_ms?: number | null;
};

export type MemoryValueChange = {
  predicate: string;
  before: string | null;
  after: string | null;
  kind: string;
};

export type ProcessingSummary = {
  created: number;
  updated: number;
  reinforced: number;
  conflicts: number;
  superseded: number;
  revisions_created: number;
  revisions_updated: number;
};

export type LiveEventSummary = {
  type: string;
  content: string;
  product_id?: string | null;
  reason?: string | null;
};

export type MemoryMutation = {
  event: LiveEventSummary;
  memory_changes: MemoryValueChange[];
  processing: ProcessingSummary;
};

export type LearningChange = {
  outcome: string;
  helpful: number;
  unhelpful: number;
  incorrect: number;
  memories_reinforced: number;
  associations_reinforced: number;
  association_items_skipped: number;
  reactivated: number;
};

export type DemoOrder = {
  id: string;
  product_id: string;
  turn_id: string;
  purchased_at: string;
  returned_at?: string | null;
};

export type ChatCompletedResponse = {
  status: "completed";
  turn_id: string;
  message: {
    role: "assistant";
    content: string;
  };
  memory: MemoryContext;
  products: Product[];
  metrics: DemoMetrics;
  mutation?: MemoryMutation | null;
  recommended_product_ids: string[];
};

export type ChatInspectResponse = {
  status: "model_unavailable";
  turn_id: string;
  memory: MemoryContext;
  products: Product[];
  metrics: DemoMetrics;
  detail: string;
  mutation?: MemoryMutation | null;
  recommended_product_ids: string[];
};

export type ChatResponse = ChatCompletedResponse | ChatInspectResponse;

export type PurchaseEventRequest = {
  event_type: "purchase";
  product_id: string;
  turn_id: string;
  client_event_id: string;
};

export type ReturnEventRequest = {
  event_type: "product_return";
  order_id: string;
  reason_id: string;
  client_event_id: string;
};

export type EventRequest = PurchaseEventRequest | ReturnEventRequest;

export type EventResponse = {
  status: "recorded" | "duplicate";
  event: LiveEventSummary;
  order?: DemoOrder | null;
  learning?: LearningChange | null;
  memory_changes: MemoryValueChange[];
  processing?: ProcessingSummary | null;
};

export type ResetResponse = {
  status: "reset";
  ready: boolean;
};

export type ReturnReasonOption = {
  id: string;
  label: string;
};

export type ComparisonMode = "full_history" | "search" | "cogkura";

export type ComparisonContextUnit = {
  id: string;
  text: string;
  source_event_ids: string[];
  score: number | null;
  kind: string | null;
  activation?: number | null;
  retrieval_reason?: string | null;
  association_path?: AssociationPath | null;
  relevance_tier?: string | null;
  structured_association_fit?: number | null;
  chunk_kind?: string | null;
  member_count?: number | null;
  members_omitted?: number | null;
  members?: ChunkMember[];
};

export type ComparisonContext = {
  rendered: string;
  estimated_tokens: number;
  units: ComparisonContextUnit[];
};

export type UnitEvaluation = {
  unit_id: string;
  expected_concepts: string[];
  excluded_concepts: string[];
  classification: "relevant" | "stale" | "relevant_and_stale" | "unclassified";
  provenance_status: "resolved" | "unresolved" | "n_a";
};

export type RelevanceMetrics = {
  expected_concepts_total: number;
  expected_concepts_found: number;
  relevant_concept_coverage: number;
  excluded_concepts_present: number;
  relevant_units: number;
  stale_units: number;
  stale_evidence_units?: number;
  unclassified_units: number;
  tokens_per_relevant_concept: number | null;
  concepts_found: string[];
  concepts_missing: string[];
  stale_concepts_found: string[];
  concept_labels: Record<string, string>;
  unit_evaluations: UnitEvaluation[];
};

export type ContextStrategyDiagnostics = {
  budget_tokens: number | null;
  used_tokens: number | null;
  remaining_tokens: number | null;
  selected_units: number | null;
  candidate_units: number | null;
  unit_cap: number | null;
  unit_cap_reached: boolean | null;
  budget_constrained: boolean | null;
  corpus_events: number | null;
  prompt_budget_tokens: number | null;
};

export type ComparisonMetrics = {
  context_tokens: number;
  context_units: number;
  context_prepare_ms: number;
  model_input_tokens: number | null;
  model_output_tokens: number | null;
  model_latency_ms: number | null;
};

export type ComparisonResult = {
  mode: ComparisonMode;
  label: string;
  answer: string | null;
  context: ComparisonContext;
  relevance: RelevanceMetrics;
  metrics: ComparisonMetrics;
  diagnostics: ContextStrategyDiagnostics | null;
  error: string | null;
};

export type ComparisonSnapshot = {
  id: string;
  as_of: string;
  history_events: number;
  history_version: number;
};

export type ComparisonResponse = {
  snapshot: ComparisonSnapshot;
  message: string;
  products: Product[];
  results: ComparisonResult[];
};

export type ComparisonRequest = {
  message: string;
  generate_answers?: boolean;
};
