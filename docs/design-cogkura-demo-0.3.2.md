# CogKura Demo 0.3.2 — fixture normalisation

Status: implemented in this repository.

See [0.3.1 comparison hardening](design-cogkura-demo-0.3.1.md) for evaluation fixes and [findings handoff](findings-customer-decision-context.md) for the post-fix CogKura comparison result.

## Goal

Correct two semantic-fact modelling inconsistencies in the Alex seed fixture, then confirm whether the observed CogKura lightweight/NorthPeak miss still reproduces. This is **not** a retrieval optimisation release.

## Fixture changes

In [data/alex/history.json](../data/alex/history.json), cardinality only:

- `evt-013` `activity_interest` / hiking: `one` → `many`
- `evt-024` `activity_interest` / skiing: `one` → `many`
- `evt-022` `product_fit_issue` / NorthPeak sleeves: `one` → `many`

Matching updates in [scripts/generate_history.py](../scripts/generate_history.py). Live return path already used `product_fit_issue` + `many` for `hood-too-restrictive`.

Unchanged: gold evidence in `comparison.json`, BM25, evaluator, Compare read-only, query, goal, 750-token budget.

## Tests

[apps/api/tests/test_fixture_cardinality.py](../apps/api/tests/test_fixture_cardinality.py):

- Seed/runtime `product_fit_issue` cardinality
- Hiking + skiing activity interests coexist after bootstrap
- NorthPeak + RidgeShell fit issues coexist after live return

## Post-fix comparison (clean reset)

| Strategy | Coverage |
|----------|----------|
| Full History | 5/5 |
| Search | 4/5 |
| CogKura | **2/5** |

CogKura selected 8 memories (~248 tokens). Five units support `hiking_interest`; none carry lightweight preference, NorthPeak fit, or colour preference gold evidence. Two units are topic-adjacent non-gold context (`evt-020`, `evt-015`–`017`). Stale concepts remain suppressed (0 stale units).

Coverage decreased vs pre-fix 0.3.1 (3/5) because consolidation changed; the fixture was not retuned after observing the result.

## Non-goals

- CogKura ranking changes in this repo
- Gold evidence expansion to browse events
- Demo-side retrieval boosts
