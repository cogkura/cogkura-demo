# CogKura Demo 0.3.9 — CogKura 0.15.7

Status: implemented in this repository.

See [0.3.8 / 0.15.6](design-cogkura-demo-0.3.8.md) and the [findings handoff](findings-customer-decision-context.md).

## Goal

Adopt CogKura `0.15.7` (`cogkura>=0.15.7,<0.16.0`) without repairing recall in demo code.

## Package change

0.15.7 adds candidate-set association indexes, entity recovery from seed text, and entity-indexed episode-to-episode hops, with inspectable association roles and path diagnostics.

Inspect-only Compare on the waterproof-jacket prompt is unchanged versus 0.15.6: CogKura **3/5** labelled coverage (current size M, hiking interest, colour preference), 8 units, ~89 tokens. Two association seeds are marked (hiking-browse cluster; Scotland waterproof-hiking episode) but both sit below threshold and `association_paths_used=0`, so hops do not pull lightweight or NorthPeak into recall. Skiing episode remains in context (stale). Live size update still yields contested M/L overlap.

## Application behaviour

Unchanged: `prepare_context()` is the only CogKura read path; `learn()` is skipped when the stored turn context has no recall results.

## Non-goals

- Lowering the retrieval threshold or otherwise boosting CogKura ranking in this repo
- Changing gold evidence, BM25, or Compare fairness rules
- Closing contested M/L or suppressing stale skiing in demo code
