# CogKura Demo 0.3.16 — CogKura 0.16.5

Status: implemented in this repository.

See [0.3.15 / 0.16.4](design-cogkura-demo-0.3.15.md) and the [findings handoff](findings-customer-decision-context.md).

## Goal

Adopt CogKura `0.16.5` (`cogkura>=0.16.5,<0.17.0`) without repairing recall in demo code and without adding encoding or retrieval context to observations.

## Package change

0.16.5 freezes the 0.16 contextual-memory contracts and hardens contextual metamemory diagnostics:

- `RetrievalContextState.CONTEXT_CONFLICT` and `ContextObservabilityReason.NO_CONTEXTUAL_MATCH` for comparable contextual evidence with zero positive matches.
- Semantic support reasons distinguish unavailable support, absent retrieval context, and unevaluated internal evidence.
- Frozen retrieval-level metamemory decision tree: not provided → unavailable → conflict → underspecified → sufficient.
- No retrieval context no longer counts semantic supports as unavailable.

Scoring, reinstatement formulae, working-memory selection, and `prepare_context().render()` are unchanged for identical inputs. There is no storage migration.

This demo still omits `ObservationContext` and `retrieval_context`. Compare and Live Memory therefore take the no-context path. The 0.16.5 diagnostic tightening is unused until the demo emits retrieval context or maps `MemoryAssessment.context`.

## Compare

Inspect-only Compare on the waterproof-jacket prompt is unchanged versus 0.3.15 / 0.16.4:

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
- Displaying 0.16 contextual metamemory in the UI
