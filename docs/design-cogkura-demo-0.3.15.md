# CogKura Demo 0.3.15 — CogKura 0.16.4

Status: implemented in this repository.

See [0.3.14 / 0.15.12](design-cogkura-demo-0.3.14.md) and the [findings handoff](findings-customer-decision-context.md).

## Goal

Adopt CogKura `0.16.4` (`cogkura>=0.16.4,<0.17.0`) without repairing recall in demo code and without adding encoding or retrieval context to observations.

## Package change

0.16 is Encoding Specificity. Through 0.16.4:

- **0.16.0** — optional `ObservationContext` / `MemoryContextSignature` on observations and episodes. Retrieval unchanged when encoding context is populated.
- **0.16.1** — optional `retrieval_context=` on recall APIs. Recall unchanged when retrieval context is populated.
- **0.16.2 / 0.16.3** — episodic and semantic context reinstatement when retrieval context is supplied. No-context calls preserve prior retrieval behaviour.
- **0.16.4** — inspect-only contextual observability (`RetrievalContextDiagnostics`, additive `MemoryAssessment.context`). Scoring, working-memory selection, and `prepare_context().render()` unchanged vs 0.16.3.

This demo still omits `ObservationContext` and `retrieval_context`. Compare and Live Memory therefore take the no-context path.

## Compare

Inspect-only Compare on the waterproof-jacket prompt is unchanged versus 0.3.14 / 0.15.12:

| Strategy | Tokens | Units | Labelled coverage | Stale labelled concepts | Units with stale evidence |
|----------|--------|-------|-------------------|-------------------------|---------------------------|
| Full History | 2335 | 134 | 5/5 | 2 | 8 |
| Search (BM25) | 703 | 34 | 4/5 | 2 | 5 |
| CogKura | **40** | **5** | **5/5** | **1** (`jacket_size:stale:L`) | **1** |

Without taxonomy (`seed_taxonomy=False`), labelled coverage stays **3/5** at 3 chunks / 19 tokens.

## Application behaviour

Unchanged read path: `prepare_context()` only. Evidence policy from 0.3.13 is unchanged. The demo does not yet surface `MemoryAssessment.context` or inspect `context.state`.

## Non-goals

- Emitting encoding or retrieval context from commerce events or the jacket query
- Changing gold, query, taxonomy, BM25, Full History, or evidence policy
- Closing contested live M/L reconsolidation
- Displaying 0.16.4 contextual metamemory in the UI
