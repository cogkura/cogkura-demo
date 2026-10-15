# CogKura Demo 0.3.17 — CogKura 0.17.7

Status: implemented in this repository.

See [0.3.16 / 0.16.5](design-cogkura-demo-0.3.16.md) and the [findings handoff](findings-customer-decision-context.md).

## Goal

Adopt CogKura `0.17.7` (`cogkura>=0.17.7,<0.18.0`) without repairing recall in demo code and without turning on transient interference or persistent inhibition.

## Package change

0.17 is interference and inhibition. Through 0.17.7:

- **0.17.0** — observational cue-competition diagnostics on `inspect_recall`. Ranking, recall, and `prepare_context().render()` unchanged.
- **0.17.1 / 0.17.2** — opt-in transient interference (`CompetitionConfig.apply_interference`, default `false`) limited to behaviourally eligible pairs.
- **0.17.3 / 0.17.4** — retrieval-induced inhibitory traces and optional application (`InhibitionConfig.enabled` and `apply_to_recall`, both default `false`).
- **0.17.5** — inspect-only interference observability on `inspect_recall` and `MemoryAssessment.interference`. Recall results unchanged.
- **0.17.6 / 0.17.6.1** — transient-interference reachability and co-consumption exclusion. `apply_interference` stays off by default.
- **0.17.7** — architecture freeze of that retrieval contract. No formula, weight, eligibility, default, or schema change.

The demo constructs `Memory` without `competition_config` or `inhibition_config`, so both switches stay off. Compare and Live Memory therefore take the same retrieval path as 0.16.5. `MemoryAssessment.interference` is not mapped in the demo API.

## Compare

Inspect-only Compare on the waterproof-jacket prompt is unchanged versus 0.3.16 / 0.16.5:

| Strategy | Tokens | Units | Labelled coverage | Stale labelled concepts | Units with stale evidence |
|----------|--------|-------|-------------------|-------------------------|---------------------------|
| Full History | 2335 | 134 | 5/5 | 2 | 8 |
| Search (BM25) | 703 | 34 | 4/5 | 2 | 5 |
| CogKura | **40** | **5** | **5/5** | **1** (`jacket_size:stale:L`) | **1** |

Without taxonomy (`seed_taxonomy=False`), labelled coverage stays **3/5** at 3 chunks / 19 tokens.

## Application behaviour

Unchanged read path: `prepare_context()` only. Evidence policy from 0.3.13 is unchanged. The demo does not record inhibitory traces or apply interference.

## Non-goals

- Enabling `apply_interference` or `apply_to_recall`
- Mapping interference metamemory in the UI
- Emitting encoding or retrieval context
- Changing gold, query, taxonomy, BM25, Full History, or evidence policy
- Closing contested live M/L reconsolidation
