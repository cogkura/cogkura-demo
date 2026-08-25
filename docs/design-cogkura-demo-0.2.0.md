# CogKura Demo 0.2.0 — live memory adaptation

Status: implemented in this repository.

## Goal

Extend the 0.1.0 read-only demo with a mutable in-memory session so scripted customer statements reconsolidate facts in the same chat turn, and purchases/returns apply CogKura HELPFUL/UNHELPFUL learning against the original recommendation context.

## CogKura 0.15 constraints that shaped the design

### `observed_at` is not world validity

Cardinality-one semantic facts need explicit `valid_from` / `valid_until` on seed and live observations. Historical `jacket_size=L` facts in `data/alex/history.json` close at the June 2026 size change; current `jacket_size=M` opens from that date with no `valid_until`.

### `minimum_supporting_episodes=2` by default

A single live size statement would otherwise be dropped during consolidation. The demo constructs `Memory` with `ComplementaryLearningSemanticConsolidator(minimum_supporting_episodes=1)`.

### Live size update

`data/alex/interactions.json` maps the exact statement `Actually, I'm back to a large now.` to a new `jacket_size=l` fact with `valid_from` at the live event time. CogKura reconciles this against the open `jacket_size=m` slot at retrieval time.

`event_to_observation()` serialises validity timestamps in UTC (`astimezone(UTC)`), not local wall time, so `valid_from` aligns with `DemoClock` and `prepare_context(..., valid_at=session.current_time)`.

### `learned_utility` location

Utility scores are read from `WorkingMemoryItem.components.learned_utility`, not `RecallResult`. Revision history for UI diffs uses `list_semantic_memories()` snapshots.

## Session model

- `DemoClock` starts at `DEMO_AS_OF`; each durable mutation advances one day.
- `DemoSession` owns seed bundle, `live_events`, `turn_records`, `live_orders`, `memory_changes`, idempotent `client_event_id`s, and turn counter.
- Combined `history`, order/return counts, and timeline include live deltas.
- Reset rebuilds `Memory()`, clock, and session collections, then re-seeds from JSON.

## API

- `POST /api/chat` — same-turn observe/process for configured statements before `prepare_context`; returns `turn_id`, optional `mutation`, `recommended_product_ids`.
- `POST /api/events` — discriminated `purchase` / `product_return` with HELPFUL/UNHELPFUL learning, idempotent on `client_event_id`.
- `GET /api/demo` — live counts, combined timeline (`kind`, `is_live`), `current_time`, `size_update_message`.

## Learning

- Purchase → `LearningOutcome.HELPFUL` on memories from `turn.context.recall_results`.
- Return → `LearningOutcome.UNHELPFUL` on the original recommendation context (not `INCORRECT`).
- `hood-too-restrictive` return reason adds a `product_fit_issue` semantic fact (`cardinality: many`).

## Inspect-only mode

Without `OPENAI_API_KEY`, chat still mutates memory, stores `AgentTurnRecord`, and supports purchase/return simulation. `record_context_use` is not called.

## Non-goals

No database, no agent frameworks, no custom retrieval or reconsolidation logic in the demo package.
