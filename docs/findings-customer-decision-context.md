# Findings — customer decision context (waterproof hiking jacket)

Handoff to CogKuraBench and CogKura core. This document records what the demo proves. It does not propose a core algorithm fix.

## 0.15.3 addendum (demo 0.3.5)

| Field | Value |
|-------|-------|
| Demo version | `0.3.5` |
| CogKura version | `0.15.3` |
| CogKura pin | `cogkura>=0.15.3,<0.16.0` |
| Scenario / clock / budget | Unchanged from the 0.3.2 run below |

Inspect-only Compare after the 0.15.3 bump:

| Strategy | Tokens | Units | Labelled coverage |
|----------|--------|-------|-------------------|
| Full History | 2335 | 134 | 5/5 |
| Search (BM25) | 703 | 34 | 4/5 |
| CogKura | **17** | **2** | **1/5** |

Same seed Compare outcome as 0.15.2: current jacket size M only. Live size update (`Actually, I'm back to a large now.`) now yields **contested** M and L semantics (overlapping validity) rather than a clean `ACTIVE` L supersession.

## 0.15.2 addendum (demo 0.3.4)

| Field | Value |
|-------|-------|
| Demo version | `0.3.4` |
| CogKura version | `0.15.2` |
| CogKura pin | `cogkura>=0.15.2,<0.16.0` |
| Scenario / clock / budget | Unchanged from the 0.3.2 run below |

Inspect-only Compare after the 0.15.2 bump:

| Strategy | Tokens | Units | Labelled coverage |
|----------|--------|-------|-------------------|
| Full History | 2335 | 134 | 5/5 |
| Search (BM25) | 703 | 34 | 4/5 |
| CogKura | **17** | **2** | **1/5** |

CogKura `prepare_context()` returns current jacket size M (`evt-031` semantic + supporting episode) via lexical soft admission. Assessment flags: `low_retrieval_strength`, `low_provenance_diversity`. Neither unit is stale. Missing labelled concepts: hiking interest, lightweight outerwear, NorthPeak fit, colour preference.

Inspection of the same cue: 2 returned (soft-admitted, neither passed the global threshold), 1 `filtered_below_soft_floor`, 6 `filtered_insufficient_relevance`, 26 `below_threshold`. Global `retrieval_threshold` remains `-3.0`.

The demo does not lower the threshold or retune ranking.

## 0.15.1 addendum (demo 0.3.3)

| Field | Value |
|-------|-------|
| Demo version | `0.3.3` |
| CogKura version | `0.15.1` |
| CogKura pin | `cogkura>=0.15.1,<0.16.0` |
| Scenario / clock / budget | Unchanged from the 0.3.2 run below |

Inspect-only Compare after the 0.15.1 bump:

| Strategy | Tokens | Units | Labelled coverage |
|----------|--------|-------|-------------------|
| Full History | 2335 | 134 | 5/5 |
| Search (BM25) | 703 | 34 | 4/5 |
| CogKura | **0** | **0** | **0/5** |

CogKura `prepare_context()` returns `no_retrieved_memory`. Inspection of the same cue shows every seed candidate `below_threshold` (highest activation about `-3.34` vs threshold `-3.0`). Traces use historical evidence times (`encoded` / `supported`), not batch materialisation. That matches CogKura 0.15.1's evidence-chronology change. The 0.3.2 / 0.15.0 working-memory occupancy table below is the last non-empty CogKura context captured on this fixture.

The demo does not lower the threshold or retune ranking.

## Run metadata (0.3.2 / CogKura 0.15.0)

| Field | Value |
|-------|-------|
| Demo version | 0.3.2 |
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

Port this scenario into CogKuraBench with the same query, goal, clock, budget, and gold evidence. On 0.15.0, investigate why `prepare_context()` working memory favoured hiking episodic mass over decision-critical preference and fit-issue memories. On 0.15.1, investigate why seed-history activation from evidence chronology falls entirely below threshold at `as_of=2026-08-01`. On 0.15.2, lexical soft admission recovers current size M; investigate why hiking, lightweight, NorthPeak fit, and colour still fail lexical relevance or the soft-admission floor. On 0.15.3, Compare is unchanged at 1/5; investigate evidence-linked admission for the remaining predicates and contested overlap on live size updates.
