# CogKura Demo 0.3.13 — Evidence-Aware Semantic Ingestion

Status: implemented in this repository.

See [0.3.12 Live Memory chunking](design-cogkura-demo-0.3.12.md) and the [findings handoff](findings-customer-decision-context.md).

## Goal

Correct application-side semantic ingestion so weak transient behaviour stays episodic, while stronger or explicit evidence can still create durable semantics. CogKura remains `>=0.15.10,<0.16.0`. No Core patch.

## Ownership

CogKura 0.15.10 current-admission of an `ACTIVE` semantic is intended. Demo 0.3.12 authored `activity_interest=skiing` on a brief browse (`evt-024`), so Core correctly treated skiing as current. Gold already labelled that interest stale. 0.3.13 removes the inconsistency at the Demo boundary.

## Policy

[`evidence_policy.py`](../apps/api/src/cogkura_demo/evidence_policy.py) filters facts in `event_to_observation()` only. Full History and BM25 still read raw `HistoryEvent` text and authored facts. The policy does not invent facts, read gold or query text, or special-case activity names.

| Evidence | Event type | Current (0.3.12) | 0.3.13 |
| --- | --- | --- | --- |
| Isolated / same-session browse | `browse` | Durable semantic if authored (skiing on `evt-024`) | Episode only |
| Support interaction | `support_interaction` | Episode (no authored facts in fixture) | Episode only |
| Purchase | `purchase` | Semantic where authored (hiking on `evt-013`) | Unchanged — strong evidence |
| Return with explicit reason | `product_return` | `product_fit_issue` | Unchanged |
| Positive review | `positive_outcome` | Preference semantic where authored | Unchanged |
| Explicit preference | `preference_statement` | Colour / size semantics | Unchanged |
| Explicit size update | `preference_statement` | Authoritative `jacket_size` | Unchanged |

Repeated-browse promotion is out of scope. Same-session ski rows (`sess-ski-browse`) therefore cannot become six independent supports.

Example:

```text
Viewed ski jackets once
→ episode

Bought hiking boots
→ episode
→ activity_interest = hiking

Said "I prefer lightweight outerwear"
→ episode
→ outerwear_weight_preference = lightweight
```

## Fairness constraints (unchanged)

- 134 customer events; no event text rewritten
- Query, gold, taxonomy, BM25 index/query, chunking, and Core thresholds unchanged
- Live M/L contested state and lightweight support-text `size L` remain separate findings

## Compare (inspect-only, canonical jacket prompt)

| Strategy | Tokens | Units | Labelled coverage |
|----------|--------|-------|-------------------|
| Full History | 2335 | 134 | 5/5 |
| Search (BM25) | 703 | 34 | 4/5 |
| CogKura | **89** | **5** | **5/5** |

Seed semantic inventory: `activity_interest=hiking` present; `activity_interest=skiing` absent. Ski browse episodes remain in history. CogKura selected context: current size M, hiking, colour collection, lightweight, NorthPeak fit. Stale labelled concepts in CogKura: `jacket_size:stale:L` (lightweight support episode). `skiing_interest` is not selected.

## Live Memory

Same policy applies to live observe/process. Size update remains `preference_statement`. Isolated browse never promotes `activity_interest`. Reset still returns 134 events.
