# CogKura Demo — agent guide

Primary entry point for coding agents working in this repository.

## What this repo is

Public interactive demo of CogKura as the memory layer for an AI e-commerce assistant (Northstar Outfitters / Alex Morgan scenario).

CogKura owns memory. The demo owns synthetic commerce data, observations, catalogue, LLM calls, and UI.

## Layout

```text
apps/api/src/cogkura_demo/   # FastAPI backend
apps/web/                    # Next.js frontend
data/alex/                   # customer, history, scenario, interactions JSON
data/catalogue.json          # product catalogue
docs/                        # design notes
```

## Validation (match CI)

```bash
uv sync --project apps/api --dev --locked
uv run --project apps/api ruff check apps/api
uv run --project apps/api ruff format --check apps/api
uv run --project apps/api mypy apps/api/src
uv run --project apps/api pytest apps/api/tests

npm ci --prefix apps/web
npm run lint --prefix apps/web
npm run typecheck --prefix apps/web
npm run build --prefix apps/web
```

Or: `./scripts/verify.sh`

## Architecture constraints

### CogKura is the memory layer

Do not implement cognitive retrieval in this repo. Use `Memory.prepare_context()` for the application read path. Do not replace it with custom `recall()` + `select_working_memory()` composition for the main flow.

### The LLM is the reasoning layer

Do not hard-code recommendation answers. CogKura supplies memory context; the model decides.

### Source data is application-owned

Map commerce events to `ObservationInput` deterministically. Put structured facts in `metadata["semantic_facts"]` with explicit cardinality: `one` for single-slot predicates (e.g. `jacket_size`, `outerwear_weight_preference`); `many` for multi-value predicates (e.g. `activity_interest`, `product_fit_issue`). Apply `evidence_policy.semantic_facts_for_observation()` in `event_to_observation()`: browse and support interactions stay episodic even if the fixture authors semantic facts. Do not invent facts from query text or gold labels.

### Product search is not memory

Catalogue data stays separate from CogKura memories.

### Do not send full history to the model

Only bounded `MemoryContext.render()` supplies historical customer knowledge to the LLM.

### One MemoryContext per turn

The same context powers the LLM prompt, API memory panel, and token metrics.

### Metrics honesty

Distinguish estimated full-history tokens, CogKura `context.estimated_tokens`, and actual OpenAI usage.

### record_context_use timing

Call only after a successful model response that consumed the context. Not for inspect-only (missing API key) runs.

### Reset

Rebuild with a fresh `Memory()` instance and re-seed; do not undo individual activation references.

### Live session (0.2.0)

- `DemoSession` + `DemoClock` own live events, orders, turn records, and idempotent client event IDs.
- Thread `session.clock.current` into `process`, `prepare_context` (`as_of` / `valid_at`), `record_context_use(referenced_at=...)`, and `learn(occurred_at=...)`. Never use `datetime.now()` for cognitive events.
- Configured customer statements map through `DemoInteractionMapper` and observe/process in the same turn before `prepare_context`.
- `POST /api/events` applies purchase/return observations and HELPFUL/UNHELPFUL learning against the stored turn context. Skip `learn()` when that context has no recall results.
- Construct `Memory` with `ComplementaryLearningSemanticConsolidator(minimum_supporting_episodes=1)`.
- Serialise validity timestamps in UTC in `event_to_observation()`.

### Compare mode (0.3.0+)

- Read-only: no observations, purchases, returns, or `learn()` on `POST /api/compare`.
- Use `context_strategies/` for Full History, Search (BM25), and CogKura adapters. CogKura Compare path must call `prepare_customer_context()` / `prepare_context()`, not custom `recall()` composition.
- `DemoSession.snapshot()` supplies immutable history for all three strategies; bump `history_version` on live mutations and reset.
- Comparison LLM calls use neutral `customer_context` only (empty `assessment_flags`). Live Memory keeps assessment flags.
- Compare must not call `observe()`, `process()`, `learn()`, or `record_context_use()`. Live Memory still calls `record_context_use()` after a successful model response.
- Evaluation ground truth is application-owned (`data/alex/comparison.json` + dynamic semantic slots). Do not use CogKura scores or BM25 ranks as truth.
- Never add evidence because a strategy happened to retrieve it. Evidence is chosen from source semantics first.
- Current and historical semantic values are distinct concept IDs (`jacket_size:current:L` vs `jacket_size:stale:L`). A historical assertion of the same value must not satisfy current-state coverage.
- Map CogKura `observation_evidence_ids` to commerce `source_record_id` before scoring; those IDs are observation UUIDs, not `evt-…` event ids.
- Do not tune Search/BM25 to beat CogKura. Search must not index evaluation metadata. Search budget fairness must be observable (`budget_constrained`, `unit_cap_reached`).
- Do not repair CogKura recall in demo code. Genuine retrieval failures become CogKura/CogKuraBench findings.
- Full History is Compare-only; Live Memory must still not send full history to the model.
- Hold `DemoState._lock` for the whole compare request.

### API boundary

Return Pydantic demo models from FastAPI, not CogKura internal types.

## Do not

- Commit `.env` or API keys
- Expose `OPENAI_API_KEY` to Next.js
- Add LangChain, LlamaIndex, agent frameworks, or a database
- Move demo-specific logic into the cogkura package

## Do not commit unless asked
