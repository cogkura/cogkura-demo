# CogKura Demo 0.3.10 — CogKura 0.15.8

Status: implemented in this repository.

See [0.3.9 / 0.15.7](design-cogkura-demo-0.3.9.md) and the [findings handoff](findings-customer-decision-context.md).

## Goal

Adopt CogKura `0.15.8` (`cogkura>=0.15.8,<0.16.0`) without repairing recall in demo code.

## Package change

0.15.8 adds application-supplied entity→entity relationships (`metadata["relationships"]`), query concept seeding, and bounded graph traversal with a `STRUCTURED_RELATION` relevance tier.

Inspect-only Compare on the waterproof-jacket prompt is unchanged versus 0.15.7: CogKura **3/5** labelled coverage (current size M, hiking interest, colour preference), 8 units, ~89 tokens. `relationship_seed_count=0` and `relationship_paths_used=0` because this demo does not emit relationship metadata. Association seeds remain 2 with `association_paths_used=0`. Lightweight and NorthPeak stay `filtered_insufficient_relevance`. Skiing episode remains in context (stale). Live size update still yields contested M/L overlap.

## Application behaviour

Unchanged: `prepare_context()` is the only CogKura read path; `learn()` is skipped when the stored turn context has no recall results. Observations still carry `semantic_facts` only.

## Non-goals

- Adding `metadata["relationships"]` to seed history to exercise structured hops
- Lowering the retrieval threshold or otherwise boosting CogKura ranking in this repo
- Changing gold evidence, BM25, or Compare fairness rules
- Closing contested M/L or suppressing stale skiing in demo code
