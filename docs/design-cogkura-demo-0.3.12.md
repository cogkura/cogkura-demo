# CogKura Demo 0.3.12 — Live Memory Chunking Compatibility

Status: implemented in this repository.

See [0.3.11 / 0.15.8 structured product context](design-cogkura-demo-0.3.11.md) and the [findings handoff](findings-customer-decision-context.md).

## Goal

Upgrade to CogKura `0.15.10` (`cogkura>=0.15.10,<0.16.0`) so Live Memory flows succeed with working-memory chunking enabled. No Demo workaround.

## Package change

0.15.9 introduced deterministic chunking and coverage-aware selection. A support episode could outrank its semantic inside `semantic_with_support` chunks, and `_serialize_semantic_chunk` incorrectly assumed `members[0]` was the semantic primary.

0.15.10 fixes explicit semantic structural primary for `SEMANTIC_WITH_SUPPORT` chunks, independent of member relevance ordering.

## Compare baseline (unchanged on 0.15.10)

Inspect-only Compare on the waterproof-jacket prompt with 0.3.11 retailer taxonomy:

| Strategy | Tokens | Units | Labelled coverage |
|----------|--------|-------|-------------------|
| Full History | 2335 | 134 | 5/5 |
| Search (BM25) | 703 | 34 | 4/5 |
| CogKura | **135** | **6** | **5/5** |

NorthPeak fit and lightweight preference remain **recalled and selected**. Colour navy/black/grey is one collection chunk. Stale skiing remains selected. `relationship_paths_used=3`.

Without taxonomy (`seed_taxonomy=False`), labelled coverage stays **3/5** at 4 chunks / 90 tokens.

## Live Memory (restored)

With chunking still enabled (`WorkingMemoryConfig.enable_chunking=True` by default):

- size update (`Actually, I'm back to a large now.`) — `prepare_context()` succeeds
- short cue (`Need a waterproof jacket.`) — chunked context prepared
- jacket prompt after size update — succeeds (6 chunks, ~122 tokens)
- purchase after size update — succeeds
- reset after size update — 134 events restored

Contested M/L semantic state after live size update remains visible. That is a separate reconsolidation finding, not a 0.3.12 failure.

## Application behaviour

Unchanged read path: `prepare_context()` only. The demo maps `WorkingMemoryItem.chunk.serialized_text` and member evidence IDs for Compare/Live Memory inspectors. `max_items=8` unchanged.

## Non-goals

- Disabling chunking or catching `AssertionError`
- Special-casing size-update text or reordering chunk members
- Changing taxonomy, gold, query, BM25, Full History, or contested M/L display
