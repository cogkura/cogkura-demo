# CogKura Demo 0.3.8 — CogKura 0.15.6

Status: implemented in this repository.

See [0.3.7 / 0.15.5](design-cogkura-demo-0.3.7.md) and the [findings handoff](findings-customer-decision-context.md).

## Goal

Adopt CogKura `0.15.6` (`cogkura>=0.15.6,<0.16.0`) without repairing recall in demo code.

## Package change

0.15.6 keeps `cardinality=many` object values distinct at recall time and ranks eligible candidates by relevance specificity. Hiking no longer collapses into skiing when ski-jacket evidence is stronger.

Inspect-only Compare on the waterproof-jacket prompt: CogKura **3/5** labelled coverage (current size M, hiking interest, colour preference), 8 units, ~89 tokens. Navy/grey/black colour facts all return. Skiing episode remains in context (stale). Lightweight and NorthPeak stay `filtered_insufficient_relevance`. Recall returned 10; selector kept 8 (`max_items`). Live size update still yields contested M/L overlap.

## Application behaviour

Unchanged: `prepare_context()` is the only CogKura read path; `learn()` is skipped when the stored turn context has no recall results.

## Non-goals

- Lowering the retrieval threshold or otherwise boosting CogKura ranking in this repo
- Changing gold evidence, BM25, or Compare fairness rules
- Closing contested M/L or suppressing stale skiing in demo code
