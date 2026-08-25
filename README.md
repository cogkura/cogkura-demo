# CogKura Demo

**CogKura Demo shows an AI e-commerce assistant using cognitive memory to understand a customer without sending their complete historical record to the LLM on every request.**

This repository is a public interactive demonstration of [CogKura](https://github.com/cogkura/cogkura) as the memory layer for an AI application. The first scenario models a shopping and support assistant for fictional retailer **Northstar Outfitters** and customer **Alex Morgan**.

## What it demonstrates

```text
customer history → ObservationInput → CogKura → prepare_context() → MemoryContext → AI agent → personalised answer
```

- Persistent customer knowledge across many historical events
- Relevant recall via bounded working memory (not full history in every prompt)
- Explainability: inspect which memories CogKura selected
- Honest token comparison between full-history estimate and CogKura memory context
- **0.2.0:** live memory mutations (size update), purchase/return simulation, HELPFUL/UNHELPFUL learning diagnostics
- **0.3.0:** read-only **Compare** view — same question through Full History, Search (BM25), and CogKura with deterministic relevance metrics

For systematic evaluation and regression measurement, see [CogKuraBench](https://github.com/cogkura/cogkura-bench). Compare relevance metrics in this demo are illustrative and application-defined until captured in a benchmark run.

## 0.2.0 live flow

1. Run the example jacket prompt (or inspect-only without an API key).
2. Click **Update size** to reconsolidate `jacket_size` in the same turn.
3. Use **Simulate customer outcome** to purchase (HELPFUL) or return (UNHELPFUL).
4. Watch memory changes, learning counters, and live timeline entries update.

See [docs/design-cogkura-demo-0.2.0.md](docs/design-cogkura-demo-0.2.0.md) for validity-window and consolidator decisions.

## 0.3.0 Compare

Use the **Compare** tab to run the same customer question through three memory strategies without mutating session state:

1. **Full History** — every event, chronological, unbounded
2. **Search (BM25)** — lexical retrieval within a 750-token budget
3. **CogKura** — bounded working memory via `prepare_context()`

The summary table shows tokens, units, relevant concept coverage, and stale evidence. Optional model answers use the same prompt for all three strategies; only `customer_context` changes.

After a live size update in **Live Memory**, run the same jacket prompt in **Compare** to see how Full History retains both medium and large evidence while evaluation marks the older size as stale.

See [docs/design-cogkura-demo-0.3.0.md](docs/design-cogkura-demo-0.3.0.md) for fairness constraints and evaluation design.

## Architecture

```mermaid
flowchart LR
    User[Demo user]
    subgraph Web[Next.js]
        UI[Demo UI]
    end
    subgraph API[FastAPI]
        Agent[Support agent]
        Product[Product catalogue]
        Scenario[Scenario data]
    end
    subgraph Memory[CogKura]
        Prepare[prepare_context]
    end
    LLM[OpenAI Responses API]
    User --> UI --> Agent
    Scenario --> Memory
    Agent --> Prepare --> Agent
    Agent --> Product
    Agent --> LLM --> Agent
    Agent --> UI
```

CogKura runs entirely in the Python backend. The OpenAI API key never reaches Next.js.

## Quick start

```bash
cp .env.example .env
# Set OPENAI_API_KEY and OPENAI_MODEL in .env (optional for memory inspection)

uv sync --project apps/api --dev --locked
npm ci --prefix apps/web

make dev
```

- API: http://localhost:8000
- Web: http://localhost:3000

Run the API with a single worker (`--workers 1`). In-memory CogKura state is process-local.

## Try this prompt

> I'm looking for a waterproof jacket for a hiking trip to Scotland next month. What would you recommend?

Click **Run example** in the UI, or type your own message.

## Verification

```bash
./scripts/verify.sh
```

## Links

- [CogKura](https://github.com/cogkura/cogkura)
- [CogKuraBench](https://github.com/cogkura/cogkura-bench)
- [cogkura.com](https://cogkura.com)

## License

Apache-2.0. See [LICENSE](LICENSE).
