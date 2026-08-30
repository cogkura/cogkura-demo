# CogKura Demo 0.3.7 — CogKura 0.15.5

Status: implemented in this repository.

See [0.3.6 / 0.15.4](design-cogkura-demo-0.3.6.md) and the [findings handoff](findings-customer-decision-context.md).

## Goal

Adopt CogKura `0.15.5` (`cogkura>=0.15.5,<0.16.0`) without repairing recall in demo code.

## Package change

0.15.5 introduces canonical retrieval features (stopword filtering, conservative morphology) and inspectable matched-feature / association-path diagnostics. Stopword-only overlaps (`for`, `to`, `a`) no longer admit semantics. Colour evidence now matches via `jacket` / `jackets`.

Inspect-only Compare on the waterproof-jacket prompt: CogKura **2/5** labelled coverage (current size M, colour preference), 6 units, ~81 tokens. Hiking is current-admitted then **collapsed**; skiing enters working memory (stale labelled concept). Lightweight and NorthPeak remain `filtered_insufficient_relevance` (relevance 0, empty association path). Selector selected all 6 recalled items. Live size update still yields contested M/L overlap.

## Application behaviour

Unchanged: `prepare_context()` is the only CogKura read path; `learn()` is skipped when the stored turn context has no recall results.

## Non-goals

- Lowering the retrieval threshold or otherwise boosting CogKura ranking in this repo
- Changing gold evidence, BM25, or Compare fairness rules
- Preventing hiking/skiing collapse in demo code
