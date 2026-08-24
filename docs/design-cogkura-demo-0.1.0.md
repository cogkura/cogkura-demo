# CogKura Demo 0.1.0 design note

This document records the 0.1.0 demo architecture for the Northstar Outfitters / Alex Morgan scenario.

See [README.md](../README.md) for how to run the demo and [AGENTS.md](../AGENTS.md) for implementation constraints.

## Objective

Prove one complete path:

```text
customer history → ObservationInput → CogKura → process() → prepare_context() → MemoryContext → AI agent → personalised answer
```

## Key decisions

- **CogKura 0.15.x** from PyPI; in-memory `Memory()` with frozen `DEMO_AS_OF=2026-08-01T12:00:00Z`
- **Single `MemoryContext` per turn** for LLM prompt, API diagnostics, and metrics
- **No full history to the model**; only `context.render()`
- **Product catalogue** is application-owned and separate from memory
- **Missing OpenAI key**: `POST /api/chat` returns inspect-only success (`model_unavailable`) with memory and metrics; no `record_context_use()`
- **Token estimates**: shared tiktoken encoding for full-history baseline and CogKura budget
- **Reset**: fresh `Memory()` instance and full re-seed under an async lock
- **Single Uvicorn worker**; process-local state

## Repository layout

```text
apps/api/     FastAPI + CogKura integration
apps/web/     Next.js demo UI
data/alex/    customer, history, scenario JSON
data/catalogue.json
```

## API

- `GET /health`
- `GET /api/demo`
- `POST /api/chat`
- `POST /api/reset`

## Scenario facts (minimum)

- Hiking interest
- Lightweight outerwear preference
- NorthPeak Alpine Shell return (sleeves too short)
- Neutral colour preference (black, navy, grey)
- Current jacket size M (historic L purchases remain in history)
- Stale skiing browsing noise

## Non-goals (0.1.0)

No database, auth, Shopify, vector DB comparison modes, agent frameworks, or live learning from demo interactions.
