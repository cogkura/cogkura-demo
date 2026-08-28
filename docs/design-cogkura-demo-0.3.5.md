# CogKura Demo 0.3.5 — CogKura 0.15.3

Status: implemented in this repository.

See [0.3.4 / 0.15.2](design-cogkura-demo-0.3.4.md) and the [findings handoff](findings-customer-decision-context.md).

## Goal

Adopt CogKura `0.15.3` (`cogkura>=0.15.3,<0.16.0`) without repairing recall in demo code.

## Package change

0.15.3 adds cardinality-one reconciliation by evidence chronology, evidence-linked semantic relevance, and authoritative current semantic admission. Global retrieval threshold and soft-admission defaults are unchanged.

Inspect-only Compare on the waterproof-jacket prompt remains **1/5** labelled coverage (`jacket_size:current:M`), 2 units, ~17 tokens — same outcome as 0.15.2 on this fixture.

Live **Update size** now reconciles the new large claim against active medium as **contested** overlap (M has open `valid_from` without `valid_until`; the live statement sets `valid_from` on L). Same-turn context still includes the live episode; semantic snapshot shows both `contested`.

## Application behaviour

Unchanged: `prepare_context()` is the only CogKura read path; `learn()` is skipped when the stored turn context has no recall results.

## Non-goals

- Lowering the retrieval threshold or otherwise boosting CogKura ranking in this repo
- Changing gold evidence, BM25, or Compare fairness rules
- Closing contested M/L by editing fixture validity windows in this release
