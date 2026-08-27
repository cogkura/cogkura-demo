# CogKura Demo 0.3.3 — CogKura 0.15.1

Status: implemented in this repository.

See [0.3.2 fixture normalisation](design-cogkura-demo-0.3.2.md) and the [findings handoff](findings-customer-decision-context.md).

## Goal

Adopt CogKura `0.15.1` (`cogkura>=0.15.1,<0.16.0`) without repairing recall in demo code.

## Package change

0.15.1 derives declarative activation from episode `ended_at` and semantic support evidence instead of synthesising recency from storage `created_at`. Batch seed of Alex's history at `2026-08-01T12:00:00Z` therefore no longer looks recently encoded.

Inspect-only Compare on the waterproof-jacket prompt: Full History and Search unchanged; CogKura **0/5** labelled coverage and **0** context tokens (`no_retrieved_memory`). Closest seed candidates sit below the default retrieval threshold (`-3.0`). Live events at the session clock remain recent enough to recall.

## Application behaviour

- `prepare_context()` is still the only CogKura read path.
- Purchase/return still observe and process at `session.clock.current`.
- `learn()` runs only when the stored turn context has recall results. Empty seed context is not a demo crash.

## Non-goals

- Lowering the retrieval threshold or otherwise boosting CogKura ranking in this repo
- Changing gold evidence, BM25, or Compare fairness rules
