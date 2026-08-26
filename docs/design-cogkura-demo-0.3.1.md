# CogKura Demo 0.3.1 — comparison evaluation hardening

Status: implemented in this repository.

See [0.3.0 design](design-cogkura-demo-0.3.0.md) for the original Compare feature.

## Goal

Make labelled coverage trustworthy before changing the memory system. 0.3.0 token measurements were already meaningful; evaluator gaps made **3/5** hard to interpret.

0.3.1 does **not** target a particular score. It strengthens measurement so retrieval quality can be distinguished from evaluator coverage and from current-vs-historical semantic state.

## Evidence expansion

`data/alex/comparison.json` now maps application-owned source events honestly:

- **lightweight:** `evt-018`, `evt-019` (not lightweight browse sessions)
- **NorthPeak fit:** `evt-022`, `evt-023`
- **hiking:** `evt-001`–`evt-012`, `evt-013`, `evt-014`, `evt-019`, `evt-032`–`evt-039`
- **skiing (stale):** `evt-024`–`evt-029`
- **colour:** `evt-030` only

Config validation on load: evidence IDs must exist in seed history; no static expected/excluded overlap; no empty or duplicate evidence within a concept.

## Semantic-state identity

Dynamic `jacket_size` concepts use explicit evaluation state:

- `jacket_size:current:M` / `jacket_size:current:L`
- `jacket_size:stale:L` (grouped evidence: `evt-018`, `evt-021`)
- `jacket_size:stale:M`

After live `M → L`, old L events satisfy **stale L**, not **current L**. Ground truth follows application event order, not CogKura `valid_until`.

## Unit diagnostics

`RelevanceMetrics.unit_evaluations` classifies each context unit as `relevant`, `stale`, `relevant_and_stale`, or `unclassified`, with matched concept IDs and `provenance_status` (`resolved` / `unresolved` / `n_a`). CogKura units with unmapped observation evidence stay unclassified.

## BM25 fairness

Default `SEARCH_MAX_EVENTS=100` (was 20) so the 750-token budget is normally the effective limiter. `ContextStrategyDiagnostics` exposes budget used/remaining, event safety cap, `budget_constrained`, and `unit_cap_reached`.

Sensitivity script: `scripts/compare-bm25.py` (model-free; caps 20/50/100).

## Compare read-only

`ComparisonService` no longer calls `record_context_use()` — even when `generate_answers=true`. Live Memory still records context use after a successful model response.

## Baseline jacket scenario (post-0.3.1, clean reset)

Inspect-only Compare on the default jacket prompt:

| Strategy | Tokens | Units | Labelled coverage | Stale concepts | Stale units | Unclassified |
|----------|--------|-------|-------------------|----------------|-------------|--------------|
| Full History | 2335 | 134 | 5/5 | 2 | 8 | 99 |
| Search (BM25) | 703 | 34 | 4/5 | 2 | 5 | 4 |
| CogKura | 240 | 8 | 3/5 | 0 | 0 | 2 |

Search: `budget_constrained=true`, `unit_cap_reached=false`.

BM25 sensitivity (`scripts/compare-bm25.py`):

```text
cap   tokens   coverage   stale concepts   stale units   unclassified
  20    446      4/5             2              4              3
  50    703      4/5             2              5              4
 100    703      4/5             2              5              4
```

CogKura at 3/5 with 2 unclassified units is a candidate for CogKuraBench investigation — not demo-side retrieval tuning.

## Non-goals

- CogKura ranking changes in this repo
- LLM judge or winner banner
- Extra public Compare strategies
