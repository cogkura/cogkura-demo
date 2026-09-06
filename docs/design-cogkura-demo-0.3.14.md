# CogKura Demo 0.3.14 — CogKura 0.15.12

Status: implemented in this repository.

See [0.3.13 evidence-aware ingestion](design-cogkura-demo-0.3.13.md) and the [findings handoff](findings-customer-decision-context.md).

## Goal

Adopt CogKura `0.15.12` (`cogkura>=0.15.12,<0.16.0`) without repairing recall in demo code.

## Package change

0.15.11 serializes `SEMANTIC_WITH_SUPPORT` chunks that have a structured predicate/object as the semantic statement only. Support episodes stay attached for provenance and `record_context_use`. Retrieval, current admission, relationship traversal, and relevance thresholds are unchanged.

0.15.12 is architecture-freeze hardening for the 0.15 line: contract tests, observational `prepare_context` benchmarks, and documentation. No changes to retrieval, reconciliation, or working-memory selection.

## Compare

Inspect-only Compare on the waterproof-jacket prompt with 0.3.11 retailer taxonomy and 0.3.13 episode-only browse:

| Strategy | Tokens | Units | Labelled coverage | Stale labelled concepts | Units with stale evidence |
|----------|--------|-------|-------------------|-------------------------|---------------------------|
| Full History | 2335 | 134 | 5/5 | 2 | 8 |
| Search (BM25) | 703 | 34 | 4/5 | 2 | 5 |
| CogKura | **40** | **5** | **5/5** | **1** (`jacket_size:stale:L`) | **1** |

0.3.13 on 0.15.10 was 89 tokens / 5 chunks / 5/5. Token drop is 0.15.11 serialization: rendered context is five semantic statements. Support episode text (including lightweight `size L`) remains on inspector members and still maps `evt-018` into evaluation. `skiing_interest` is not selected.

Without taxonomy (`seed_taxonomy=False`), labelled coverage stays **3/5** at 3 chunks / 19 tokens.

## Application behaviour

Unchanged read path: `prepare_context()` only. The demo still maps `chunk.serialized_text` for the model/prompt inspector and member statements for provenance. `max_items=8` unchanged. Evidence policy from 0.3.13 is unchanged.

## Non-goals

- Changing gold, query, taxonomy, BM25, Full History, or evidence policy
- Hiding inspector support members that mention size L
- Closing contested live M/L reconsolidation
