# CogKura Demo 0.3.11 — Structured Product Context

Status: implemented in this repository.

See [0.3.10 / 0.15.8](design-cogkura-demo-0.3.10.md) and the [findings handoff](findings-customer-decision-context.md).

## Goal

Supply retailer-owned product/category `is_a` relationships through the public CogKura 0.15.8 observation API without changing customer history text, gold labels, query, Full History, BM25, or working-memory selection.

## Source model

[`data/retailer-taxonomy.json`](../data/retailer-taxonomy.json) declares category parents (`waterproof-jacket` → `jacket`, etc.) and the historical SKU `breeze-windbreaker` → `jacket`. Product→category edges are derived from [`data/catalogue.json`](../data/catalogue.json) at seed time.

NorthPeak path:

```text
jacket ← is_a waterproof-jacket ← is_a northpeak-alpine-shell
```

Customer events with `product_id` now also set `metadata["entity_ids"]`. Product-scoped semantic facts set `object_entity_id` on observation ingest.

## Run C result (structured data)

Inspect-only Compare on the waterproof-jacket prompt with taxonomy seeded:

| Strategy | Tokens | Units | Labelled coverage |
|----------|--------|-------|-------------------|
| Full History | 2335 | 134 | 5/5 |
| Search (BM25) | 703 | 34 | 4/5 |
| CogKura | **89** | **8** | **3/5** |

Labelled coverage is unchanged versus Run B, but broad recall now reaches NorthPeak fit and lightweight preference via `structured_relation` paths (`relationship_paths_used=3`). Both semantics are **recalled** and **not selected** into the eight-item working-memory context — working memory is the bottleneck.

Taxonomy inventory: 15 entities, 14 `is_a` relationships.

## Application behaviour

- Taxonomy is ingested via one `catalog.taxonomy` observation before customer history replay.
- Compare still uses `prepare_context()` only.
- Context Inspector shows Core-reported relationship paths when present.

## Non-goals

- Adding query/gold-encoded edges
- Changing `max_items=8` or suppressing stale skiing / colour redundancy
- Inferring product taxonomy from product names in demo code
