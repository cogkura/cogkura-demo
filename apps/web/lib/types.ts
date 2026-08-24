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
};

export type ScenarioInfo = {
  id: string;
  name: string;
  suggested_prompt: string;
  goal: string;
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
};

export type ChatCompletedResponse = {
  status: "completed";
  message: {
    role: "assistant";
    content: string;
  };
  memory: MemoryContext;
  products: Product[];
  metrics: DemoMetrics;
};

export type ChatInspectResponse = {
  status: "model_unavailable";
  memory: MemoryContext;
  products: Product[];
  metrics: DemoMetrics;
  detail: string;
};

export type ChatResponse = ChatCompletedResponse | ChatInspectResponse;

export type ResetResponse = {
  status: "reset";
  ready: boolean;
};
