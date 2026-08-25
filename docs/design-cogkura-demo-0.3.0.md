# CogKura Demo 0.3.0 — memory strategy comparison

Status: implemented in this repository.

## Goal

Add a read-only **Compare** view beside **Live Memory** (0.2.0 unchanged). The same customer question runs through three context strategies:

- **Full History** — all events, chronological, unbounded
- **Search (BM25)** — lexical retrieval over the same history, 750-token budget
- **CogKura** — existing `prepare_context()` path, 750-token budget

No purchases, returns, observations, or `learn()` in Compare. Only the customer-context strategy changes.

## Fairness constraints

- Comparison LLM calls use identical `system_prompt`, `user_message`, and product catalogue. Only `customer_context` differs.
- Comparison calls omit CogKura assessment flags (empty for all three). Live Memory keeps current flag behaviour.
- Search and CogKura share the same token budget (`SEARCH_CONTEXT_BUDGET_TOKENS` defaults to `COGKURA_MEMORY_BUDGET_TOKENS`).
- Full History is Compare-only. Live Memory must still not send full history to the model.
- Do not tune baselines to win. Search cannot index evaluation metadata. Evaluation ground truth comes from application events, not CogKura scores.

## Context strategies

`apps/api/src/cogkura_demo/context_strategies/`:

- `full_history.py` — sorted `render_full_history()` reused for prompt, tokens, and Live Memory baseline estimate
- `bm25.py` — `rank-bm25` over history corpus; query is `goal + message`; pack within budget in retrieval-rank order
- `cogkura.py` — thin adapter over `DemoMemory.prepare_customer_context(..., as_of=snapshot.as_of)`

`DemoSession.snapshot()` returns immutable `ComparisonSnapshot` with `history_version` bumped on live mutations and reset.

## Evaluation

`data/alex/comparison.json` defines static expected/excluded concepts plus a dynamic `jacket_size` semantic slot resolved from snapshot history (latest affirm = expected; earlier values = stale).

`ComparisonEvaluator` maps context units to concepts via `source_event_ids`. CogKura units resolve `observation_evidence_ids` (internal observation UUIDs) to commerce `source_record_id` values (`evt-018`, …) before scoring. Unresolved evidence stays unclassified.

Metrics: relevant concept coverage, excluded concepts present, unit counts, optional tokens per relevant concept. No LLM judge and no winner banner.

## API

`POST /api/compare`:

```json
{ "message": "...", "generate_answers": true }
```

Under `DemoState._lock`: snapshot → three prepares → evaluate → optional three sequential LLM calls (Full History, Search, CogKura).

`record_context_use` only after a successful CogKura generated answer. Inspect-only (`generate_answers=false` or no API key) still returns contexts and relevance.

## UI

Segmented nav: **Live Memory | Compare**. Compare state is separate from chat state. Reset clears both.

Summary table first (tokens, units, relevant x/y, stale, model input). Full History context collapsed by default. Search inspector shows BM25 score; CogKura reuses memory diagnostics patterns.

## Non-goals

- Vector search
- Concurrent compare requests (0.3.0 holds the demo lock for the whole request)
- Merging Compare into chat turn state
