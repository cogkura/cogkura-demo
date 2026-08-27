# CogKura Demo 0.3.4 — CogKura 0.15.2

Status: implemented in this repository.

See [0.3.3 / 0.15.1](design-cogkura-demo-0.3.3.md) and the [findings handoff](findings-customer-decision-context.md).

## Goal

Adopt CogKura `0.15.2` (`cogkura>=0.15.2,<0.16.0`) without repairing recall in demo code.

## Package change

0.15.2 adds lexical semantic slot matching for plain-language string cues, with a bounded soft-admission floor. Long-lived `ACTIVE` facts such as current jacket size can enter working memory without lowering the global retrieval threshold.

Inspect-only Compare on the waterproof-jacket prompt: Full History and Search unchanged; CogKura **1/5** labelled coverage (`jacket_size:current:M`), 2 units, ~17 tokens. Hiking, lightweight, NorthPeak fit, and colour preference remain missing. Inspection: 2 returned (soft-admitted), 1 below soft floor, 6 insufficient lexical relevance, 26 below threshold.

## Application behaviour

Unchanged from 0.3.3: `prepare_context()` is the only CogKura read path; `learn()` is skipped when the stored turn context has no recall results.

## Non-goals

- Lowering the retrieval threshold or otherwise boosting CogKura ranking in this repo
- Changing gold evidence, BM25, or Compare fairness rules
