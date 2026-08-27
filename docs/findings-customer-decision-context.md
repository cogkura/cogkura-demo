# Findings — customer decision context (waterproof hiking jacket)

Handoff to CogKuraBench and CogKura core. This document records what the demo proves after fixture normalisation in 0.3.2. It does not propose a core algorithm fix.

## Run metadata

| Field | Value |
|-------|-------|
| Demo version | 0.3.2 (pending release; captured on working tree after cardinality fix) |
| Demo git commit | `45442c96901cf364751b7df560c35dcec6ae1a79` + fixture changes |
| CogKura version | `0.15.0` |
| CogKura pin | `cogkura>=0.15.0,<0.16.0` |
| Scenario | `waterproof-hiking-jacket` |
| Customer | Alex Morgan (`alex`) |
| `as_of` / `valid_at` | `2026-08-01T12:00:00Z` |
| Prompt budget | 750 tokens |
| Semantic consolidator | `ComplementaryLearningSemanticConsolidator(minimum_supporting_episodes=1)` |
| Compare mode | Inspect-only (`generate_answers=false`) |
| Live mutations before run | None (clean reset) |

## Query and goal

**Query:**

> I'm looking for a waterproof jacket for a hiking trip to Scotland next month. What would you recommend?

**Goal:**

> Help Alex choose an appropriate waterproof hiking jacket.

## Comparison summary (post-0.3.2 fixture fix)

| Strategy | Tokens | Units | Labelled coverage | Stale concepts | Stale units | Unclassified |
|----------|--------|-------|-------------------|----------------|-------------|--------------|
| Full History | 2335 | 134 | 5/5 | 2 | 8 | 99 |
| Search (BM25) | 703 | 34 | 4/5 | 2 | 5 | 4 |
| CogKura | 248 | 8 | **2/5** | 0 | 0 | 2 |

Search: `budget_constrained=true`, `unit_cap_reached=false`.

Compared to pre-fix 0.3.1 baseline (CogKura 3/5), labelled coverage **decreased** after correcting `activity_interest` and `product_fit_issue` cardinality. That is a valid outcome: the fixture now models coexistence correctly; the miss still reproduces and may have shifted.

## Expected concepts — CogKura

**Found (2/5):**

- `hiking_interest`
- `jacket_size:current:M`

**Missing (3/5):**

- `outerwear_weight_preference:lightweight` — gold evidence `evt-018`, `evt-019`
- `northpeak_fit_issue` — gold evidence `evt-022`, `evt-023`
- `colour_preference:neutral` — gold evidence `evt-030`

**Stale concepts in working memory:** none (0 stale concepts, 0 stale units). CogKura continues to suppress application-labelled stale skiing and old jacket-size evidence from the bounded context.

## Working-memory concept slot occupancy

Units counted by labelled expected concept matched (one unit may match one concept; hiking episodes overlap):

| Concept | Selected units |
|---------|----------------|
| `hiking_interest` | 5 |
| `jacket_size:current:M` | 1 |
| `outerwear_weight_preference:lightweight` | 0 |
| `northpeak_fit_issue` | 0 |
| `colour_preference:neutral` | 0 |

Five of eight slots support hiking. No slot carries the strong lightweight-preference or NorthPeak-fit evidence.

## All eight selected CogKura memories

| Rank | Kind | Statement (abbrev.) | Score | Activation | Source events | Classification |
|------|------|---------------------|-------|------------|---------------|----------------|
| 1 | semantic | alex jacket size m | 0.999 | 3.774 | `evt-031` | relevant |
| 2 | semantic | alex activity interest hiking | 0.999 | 3.724 | `evt-013` | relevant |
| 3 | episode | Scotland waterproof hiking browse cluster | 0.999 | 3.841 | `evt-032`–`039` | relevant |
| 4 | episode | Compared waterproof shells including NorthPeak | 0.999 | 3.732 | `evt-020` | unclassified |
| 5 | episode | Early hiking browse cluster | 0.999 | 3.724 | `evt-001`–`012` | relevant |
| 6 | episode | Purchased hiking trousers | 0.999 | 3.724 | `evt-014` | relevant |
| 7 | episode | Purchased hiking boots | 0.999 | 3.724 | `evt-013` | relevant |
| 8 | episode | Browsed lightweight jacket listings | 0.999 | 3.732 | `evt-015`–`017` | unclassified |

Provenance: all eight units `resolved` (`evt-…` IDs mapped).

## Topic-adjacent / weaker context (non-gold)

These selected memories are useful but do not satisfy the conservative gold labels:

- **`evt-015`–`017`** — lightweight jacket browsing shows interest, not established `outerwear_weight_preference:lightweight` (gold requires `evt-018` purchase + `evt-019` review).
- **`evt-020`** — NorthPeak shell comparison shows consideration, not `northpeak_fit_issue` (gold requires `evt-022` return + `evt-023` support).

## What the demo proves

After correcting semantic cardinality (`activity_interest` and `product_fit_issue` → `many`), CogKura's final bounded context at 750 tokens **still does not include** the strong lightweight-preference and NorthPeak-fit evidence (`evt-018`/`evt-019`, `evt-022`/`evt-023`). Colour preference (`evt-030`) is also absent from the eight selected memories.

The demo does **not** establish whether those concepts are absent from broad recall or retrievable but dropped during working-memory selection. CogKuraBench should distinguish those stages.

## What the demo does not claim

- That the recall algorithm is definitively broken
- That working-memory diversity alone is the root cause
- Any recommended ranking or consolidation change in `cogkura-demo`

## Next step

Port this scenario into CogKuraBench with the same query, goal, clock, budget, and gold evidence. Investigate why `prepare_context()` working memory favours hiking episodic mass over decision-critical preference and fit-issue memories.
