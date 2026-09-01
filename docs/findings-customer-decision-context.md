# Findings — customer decision context (waterproof hiking jacket)

Handoff to CogKuraBench and CogKura core. This document records what the demo proves. It does not propose a core algorithm fix.

## 0.3.11 structured product context (demo 0.3.11, CogKura 0.15.8)

| Field | Value |
|-------|-------|
| Demo version | `0.3.11` |
| CogKura version | `0.15.8` |
| CogKura pin | `cogkura>=0.15.8,<0.16.0` |
| Scenario / clock / budget | Unchanged from the 0.3.2 run below |
| Taxonomy | 15 entities, 14 `is_a` relationships (catalogue-derived + `retailer-taxonomy.json`) |

Inspect-only Compare after seeding retailer catalogue relationships (Run C):

| Strategy | Tokens | Units | Labelled coverage |
|----------|--------|-------|-------------------|
| Full History | 2335 | 134 | 5/5 |
| Search (BM25) | 703 | 34 | 4/5 |
| CogKura | **89** | **8** | **3/5** |

Found (selected context): `jacket_size:current:M`, `hiking_interest`, `colour_preference:neutral`. Missing (selected context): lightweight outerwear, NorthPeak fit. Stale: `skiing_interest`. Broad recall now reaches both missing concepts via `structured_relation` (`relationship_seed_count=2`, `relationship_paths_used=3`): `outerwear_weight_preference=lightweight` via `breeze-windbreaker is_a jacket`; `product_fit_issue=northpeak-alpine-shell:sleeves_too_short` via `northpeak-alpine-shell is_a waterproof-jacket`. Both are **recalled** and **not selected** at `max_items=8`. Customer history text, gold labels, Full History, and BM25 corpus unchanged.

## 0.15.8 addendum (demo 0.3.10, legacy data — Run B)

| Field | Value |
|-------|-------|
| Demo version | `0.3.10` |
| CogKura version | `0.15.8` |
| CogKura pin | `cogkura>=0.15.8,<0.16.0` |
| Scenario / clock / budget | Unchanged from the 0.3.2 run below |

Inspect-only Compare after the 0.15.8 bump:

| Strategy | Tokens | Units | Labelled coverage |
|----------|--------|-------|-------------------|
| Full History | 2335 | 134 | 5/5 |
| Search (BM25) | 703 | 34 | 4/5 |
| CogKura | **89** | **8** | **3/5** |

Found: `jacket_size:current:M`, `hiking_interest`, `colour_preference:neutral`. Missing: lightweight outerwear, NorthPeak fit. Stale: `skiing_interest` (ski-browse episode still selected). Inspection: 35 considered, 10 returned (0 above threshold; 6 `semantic_current_admission`, 4 `semantic_slot_admission`), 0 collapsed, 2 insufficient relevance, 23 below threshold. `association_seed_count=2` (both `below_threshold`); `association_paths_used=0`. `relationship_seed_count=0`; `relationship_paths_used=0`; `structured_association_fit=0` on all candidates. The demo does not put `metadata["relationships"]` on observations, so structured graph hops have nothing to traverse. Hiking returns at `direct_value` (`hiking`); skiing at `evidence_association` (`jacket`). Colour navy/black/grey all returned. Lightweight and NorthPeak: relevance 0, tier `contextual`. Selector: 10 candidates, 8 selected (`max_items`). Live size update remains contested M/L.

The demo does not lower the threshold, retune ranking, or add relationship metadata to boost recall.

## 0.15.7 addendum (demo 0.3.9)

| Field | Value |
|-------|-------|
| Demo version | `0.3.9` |
| CogKura version | `0.15.7` |
| CogKura pin | `cogkura>=0.15.7,<0.16.0` |
| Scenario / clock / budget | Unchanged from the 0.3.2 run below |

Inspect-only Compare after the 0.15.7 bump:

| Strategy | Tokens | Units | Labelled coverage |
|----------|--------|-------|-------------------|
| Full History | 2335 | 134 | 5/5 |
| Search (BM25) | 703 | 34 | 4/5 |
| CogKura | **89** | **8** | **3/5** |

Found: `jacket_size:current:M`, `hiking_interest`, `colour_preference:neutral`. Missing: lightweight outerwear, NorthPeak fit. Stale: `skiing_interest` (ski-browse episode still selected). Inspection: 35 considered, 10 returned (0 above threshold; 6 `semantic_current_admission`, 4 `semantic_slot_admission`), 0 collapsed, 2 insufficient relevance, 23 below threshold. `association_seed_count=2` (hiking-browse cluster and Scotland waterproof-hiking episode, both `below_threshold`); `association_paths_used=0`. Hiking returns at `direct_value` (`hiking`); skiing at `evidence_association` (`jacket`). Colour navy/black/grey all returned. Lightweight and NorthPeak: relevance 0, tier `contextual`. Selector: 10 candidates, 8 selected (`max_items`). Live size update remains contested M/L.

The demo does not lower the threshold or retune ranking.

## 0.15.6 addendum (demo 0.3.8)

| Field | Value |
|-------|-------|
| Demo version | `0.3.8` |
| CogKura version | `0.15.6` |
| CogKura pin | `cogkura>=0.15.6,<0.16.0` |
| Scenario / clock / budget | Unchanged from the 0.3.2 run below |

Inspect-only Compare after the 0.15.6 bump:

| Strategy | Tokens | Units | Labelled coverage |
|----------|--------|-------|-------------------|
| Full History | 2335 | 134 | 5/5 |
| Search (BM25) | 703 | 34 | 4/5 |
| CogKura | **89** | **8** | **3/5** |

Found: `jacket_size:current:M`, `hiking_interest`, `colour_preference:neutral`. Missing: lightweight outerwear, NorthPeak fit. Stale: `skiing_interest` (ski-browse episode still selected). Inspection: 35 considered, 10 returned (0 above threshold; 6 `semantic_current_admission`, 4 `semantic_slot_admission`), 0 collapsed, 2 insufficient relevance, 23 below threshold. Hiking returns at `direct_value` (`hiking`); skiing at `evidence_association` (`jacket`) without collapsing hiking. Colour navy/black/grey all returned (`jacket` evidence). Lightweight and NorthPeak: relevance 0, tier `contextual`. Selector: 10 candidates, 8 selected (`max_items`). Live size update remains contested M/L.

The demo does not lower the threshold or retune ranking.

## 0.15.5 addendum (demo 0.3.7)

| Field | Value |
|-------|-------|
| Demo version | `0.3.7` |
| CogKura version | `0.15.5` |
| CogKura pin | `cogkura>=0.15.5,<0.16.0` |
| Scenario / clock / budget | Unchanged from the 0.3.2 run below |

Inspect-only Compare after the 0.15.5 bump:

| Strategy | Tokens | Units | Labelled coverage |
|----------|--------|-------|-------------------|
| Full History | 2335 | 134 | 5/5 |
| Search (BM25) | 703 | 34 | 4/5 |
| CogKura | **81** | **6** | **2/5** |

Found: `jacket_size:current:M`, `colour_preference:neutral`. Missing: hiking interest, lightweight outerwear, NorthPeak fit. Stale: `skiing_interest` (1 stale unit). Canonical query features: `hiking, jacket, looking, month, next, recommend, scotland, trip, waterproof`. Inspection: 35 considered, 6 returned (0 above threshold; 3 `semantic_current_admission`, 3 `semantic_slot_admission`), 4 collapsed, 2 insufficient relevance, 23 below threshold. Hiking semantic is current-admitted (`matched_direct_features=hiking`) then collapsed; skiing is returned via evidence feature `jacket`. Colour grey returned via evidence feature `jacket`; navy/black collapsed. Lightweight and NorthPeak: relevance 0, empty matched features, `association_path=None`. Selector: 6/6 selected. Live size update remains contested M/L.

The demo does not lower the threshold or retune ranking.

## 0.15.4 addendum (demo 0.3.6)

| Field | Value |
|-------|-------|
| Demo version | `0.3.6` |
| CogKura version | `0.15.4` |
| CogKura pin | `cogkura>=0.15.4,<0.16.0` |
| Scenario / clock / budget | Unchanged from the 0.3.2 run below |

Inspect-only Compare after the 0.15.4 bump:

| Strategy | Tokens | Units | Labelled coverage |
|----------|--------|-------|-------------------|
| Full History | 2335 | 134 | 5/5 |
| Search (BM25) | 703 | 34 | 4/5 |
| CogKura | **51** | **6** | **3/5** |

Found: `jacket_size:current:M`, `hiking_interest`, `colour_preference:neutral`. Missing: lightweight outerwear, NorthPeak fit. Inspection: 35 considered, 6 returned (0 above threshold; 3 `semantic_current_admission`, 3 `semantic_slot_admission`), 2 collapsed, 3 insufficient relevance, 24 below threshold. Selector: 6 candidates, 0 goal-filtered, 0 inhibited, 0 budget-skipped, 6 selected. Live size update remains contested M/L.

The demo does not lower the threshold or retune ranking.

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

Port this scenario into CogKuraBench with the same query, goal, clock, budget, and gold evidence. On 0.15.0, investigate why `prepare_context()` working memory favoured hiking episodic mass over decision-critical preference and fit-issue memories. On 0.15.1, investigate why seed-history activation from evidence chronology falls entirely below threshold at `as_of=2026-08-01`. On 0.15.2, lexical soft admission recovers current size M; investigate why hiking, lightweight, NorthPeak fit, and colour still fail lexical relevance or the soft-admission floor. On 0.15.3, Compare is unchanged at 1/5; investigate evidence-linked admission for the remaining predicates and contested overlap on live size updates. On 0.15.4, Compare is 3/5; investigate why lightweight and NorthPeak fit still fail current admission. On 0.15.5, Compare is 2/5: hiking current-admits then collapses against skiing; lightweight and NorthPeak still have relevance 0 and no association path. On 0.15.6, Compare is 3/5 with hiking restored; investigate remaining lightweight/NorthPeak misses and stale skiing still occupying a working-memory slot. On 0.15.7, Compare is unchanged at 3/5: association seeds exist but `association_paths_used=0`, so entity-indexed hops do not recover lightweight or NorthPeak. On 0.15.8, Compare is unchanged at 3/5 with legacy data (`relationship_seed_count=0`). On 0.3.11 structured product context, broad recall reaches NorthPeak fit and lightweight preference via `structured_relation` paths but working memory still selects 8/10 recalled items (3/5 labelled coverage). Next Core work: working-memory coverage and redundancy at `max_items=8`.
