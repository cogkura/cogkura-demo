# CogKura Demo 0.3.6 — CogKura 0.15.4

Status: implemented in this repository.

See [0.3.5 / 0.15.3](design-cogkura-demo-0.3.5.md) and the [findings handoff](findings-customer-decision-context.md).

## Goal

Adopt CogKura `0.15.4` (`cogkura>=0.15.4,<0.16.0`) without repairing recall in demo code.

## Package change

0.15.4 treats `valid_at` as current-at-snapshot time rather than historical query intent. Authoritative current admission can use distinctive token overlap; evidence-linked relevance saturates across supporting episodes; one-hop association can reach related semantics.

Inspect-only Compare on the waterproof-jacket prompt: Full History and Search unchanged; CogKura **3/5** labelled coverage (current size M, hiking interest, colour preference), 6 units, ~51 tokens. Missing: lightweight outerwear and NorthPeak fit. Selector selected all 6 recalled items (no goal filter, inhibition, or budget skip). Live size update still yields contested M/L overlap.

## Application behaviour

Unchanged: `prepare_context()` is the only CogKura read path; `learn()` is skipped when the stored turn context has no recall results.

## Non-goals

- Lowering the retrieval threshold or otherwise boosting CogKura ranking in this repo
- Changing gold evidence, BM25, or Compare fairness rules
- Closing contested M/L by editing fixture validity windows in this release
