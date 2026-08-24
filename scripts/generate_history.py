#!/usr/bin/env python3
"""Generate deterministic Alex Morgan history.json (run once, commit output)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

OUTPUT = Path(__file__).resolve().parents[1] / "data" / "alex" / "history.json"
CUSTOMER = "alex"
START = datetime(2025, 2, 1, 9, 0, tzinfo=UTC)


def iso(dt: datetime) -> str:
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def event(
    idx: int,
    *,
    type_: str,
    dt: datetime,
    content: str,
    product_id: str | None = None,
    reason: str | None = None,
    semantic_facts: list[dict[str, str]] | None = None,
    session_id: str | None = None,
) -> dict:
    payload: dict = {
        "id": f"evt-{idx:03d}",
        "type": type_,
        "customer_id": CUSTOMER,
        "occurred_at": iso(dt),
        "content": content,
        "session_id": session_id or f"sess-{idx:03d}",
    }
    if product_id:
        payload["product_id"] = product_id
    if reason:
        payload["reason"] = reason
    if semantic_facts:
        payload["semantic_facts"] = semantic_facts
    return payload


def main() -> None:
    events: list[dict] = []
    idx = 1
    t = START

    def add(**kwargs) -> None:
        nonlocal idx, t
        if "dt" in kwargs:
            t = kwargs.pop("dt")
        events.append(event(idx, dt=t, **kwargs))
        idx += 1

    # Hiking interest cluster (Feb–Mar 2025)
    for day in range(0, 12):
        add(
            type_="browse",
            dt=START + timedelta(days=day * 2, hours=day % 5),
            content=f"Alex browsed hiking {['boots', 'backpacks', 'poles', 'trousers', 'jackets'][day % 5]}.",
            session_id="sess-hike-start",
        )
    add(
        type_="purchase",
        dt=datetime(2025, 3, 18, 14, 20, tzinfo=UTC),
        content="Alex purchased TrailLite hiking boots in size UK 9.",
        product_id="trail-lite-boots",
        semantic_facts=[
            {
                "predicate": "activity_interest",
                "object_value": "hiking",
                "cardinality": "one",
                "polarity": "affirm",
            }
        ],
    )
    add(
        type_="purchase",
        dt=datetime(2025, 5, 12, 11, 5, tzinfo=UTC),
        content="Alex purchased TrailLite hiking trousers in size L.",
        product_id="trail-lite-trousers",
    )

    # Lightweight preference cluster
    for i, name in enumerate(["RidgeShell 2", "AeroTrail Pro", "featherweight shells"]):
        add(
            type_="browse",
            dt=datetime(2025, 6, 10 + i, 16, 0, tzinfo=UTC),
            content=f"Alex browsed lightweight jacket listings including {name}.",
            session_id="sess-light-jackets",
        )
    add(
        type_="purchase",
        dt=datetime(2025, 7, 22, 10, 30, tzinfo=UTC),
        content="Alex purchased a lightweight windbreaker in size L.",
        product_id="breeze-windbreaker",
        semantic_facts=[
            {
                "predicate": "outerwear_weight_preference",
                "object_value": "lightweight",
                "cardinality": "one",
                "polarity": "affirm",
            },
            {
                "predicate": "jacket_size",
                "object_value": "L",
                "cardinality": "one",
                "polarity": "affirm",
            },
        ],
    )
    add(
        type_="positive_outcome",
        dt=datetime(2025, 11, 4, 9, 15, tzinfo=UTC),
        content="Alex left a positive review praising how light the windbreaker feels on long hikes.",
        product_id="breeze-windbreaker",
    )

    # NorthPeak purchase and return (size L, sleeve issue)
    add(
        type_="browse",
        dt=datetime(2025, 8, 30, 19, 0, tzinfo=UTC),
        content="Alex compared waterproof shells including NorthPeak Alpine Shell.",
        product_id="northpeak-alpine-shell",
    )
    add(
        type_="purchase",
        dt=datetime(2025, 9, 2, 12, 45, tzinfo=UTC),
        content="Alex purchased the NorthPeak Alpine Shell in size L.",
        product_id="northpeak-alpine-shell",
        semantic_facts=[
            {
                "predicate": "jacket_size",
                "object_value": "L",
                "cardinality": "one",
                "polarity": "affirm",
            }
        ],
    )
    add(
        type_="product_return",
        dt=datetime(2025, 9, 18, 10, 15, tzinfo=UTC),
        content="Alex returned the NorthPeak Alpine Shell because the sleeves were too short.",
        product_id="northpeak-alpine-shell",
        reason="Sleeves were too short",
        semantic_facts=[
            {
                "predicate": "product_fit_issue",
                "object_value": "northpeak-alpine-shell:sleeves_too_short",
                "cardinality": "one",
                "polarity": "affirm",
            }
        ],
    )
    add(
        type_="support_interaction",
        dt=datetime(2025, 9, 19, 15, 30, tzinfo=UTC),
        content="Alex contacted support about NorthPeak sleeve length and asked about alternative fits.",
        product_id="northpeak-alpine-shell",
        session_id="sess-support-northpeak",
    )

    # Old skiing interest (stale)
    for i in range(6):
        add(
            type_="browse",
            dt=datetime(2026, 1, 14 + i, 20, 0, tzinfo=UTC),
            content=f"Alex browsed ski {'jackets' if i % 2 == 0 else 'goggles'} briefly.",
            product_id="glacier-ski-jacket" if i % 2 == 0 else None,
            session_id="sess-ski-browse",
            semantic_facts=[
                {
                    "predicate": "activity_interest",
                    "object_value": "skiing",
                    "cardinality": "one",
                    "polarity": "affirm",
                }
            ]
            if i == 0
            else None,
        )

    # Colour preference
    add(
        type_="preference_statement",
        dt=datetime(2026, 4, 22, 18, 40, tzinfo=UTC),
        content="Alex said they normally stick to black, navy or grey for jackets.",
        semantic_facts=[
            {
                "predicate": "colour_preference",
                "object_value": "black",
                "cardinality": "many",
                "polarity": "affirm",
            },
            {
                "predicate": "colour_preference",
                "object_value": "navy",
                "cardinality": "many",
                "polarity": "affirm",
            },
            {
                "predicate": "colour_preference",
                "object_value": "grey",
                "cardinality": "many",
                "polarity": "affirm",
            },
        ],
    )

    # Size change to M
    add(
        type_="preference_statement",
        dt=datetime(2026, 6, 15, 8, 50, tzinfo=UTC),
        content="Alex mentioned they have lost some weight and are a medium now.",
        semantic_facts=[
            {
                "predicate": "jacket_size",
                "object_value": "M",
                "cardinality": "one",
                "polarity": "affirm",
            }
        ],
    )

    # Recent hiking browsing before demo date
    for i in range(8):
        add(
            type_="browse",
            dt=datetime(2026, 7, 5 + i, 12, 0, tzinfo=UTC),
            content=f"Alex browsed waterproof hiking gear for Scotland trips ({['jackets', 'gaiters', 'maps', 'layers'][i % 4]}).",
            session_id="sess-scotland-prep",
        )

    # Fill with realistic noise to reach 100–150 events
    noise_topics = [
        "camp mugs",
        "head torches",
        "merino base layers",
        "dry bags",
        "trekking socks",
        "hydration bladders",
        "gaiters",
        "beanie hats",
        "gloves",
        "sleeping bag liners",
        "trekking poles",
        "compasses",
        "first aid kits",
        "insect repellent",
        "sun cream",
    ]
    noise_day = datetime(2025, 4, 1, tzinfo=UTC)
    while len(events) < 132:
        topic = noise_topics[len(events) % len(noise_topics)]
        add(
            type_="browse" if len(events) % 7 != 0 else "support_interaction",
            dt=noise_day,
            content=f"Alex {'browsed' if len(events) % 7 != 0 else 'asked support about'} {topic}.",
            session_id=f"sess-noise-{len(events) // 10}",
        )
        noise_day += timedelta(days=3, hours=len(events) % 8)

    # Additional purchases and returns for summary counts
    purchases = [
        ("trekking-poles-carbon", "carbon trekking poles"),
        ("merino-tee", "merino base layer"),
        ("dry-bag-set", "dry bag set"),
        ("head-torch-pro", "rechargeable head torch"),
        ("hiking-socks-3pack", "hiking sock bundle"),
        ("camp-stove-mini", "mini camp stove"),
        ("insulated-mug", "insulated camp mug"),
        ("map-case", "waterproof map case"),
        ("gaiters-light", "lightweight gaiters"),
        ("pack-rain-cover", "backpack rain cover"),
        ("trekking-shorts", "quick-dry trekking shorts"),
        ("fleece-midlayer", "midweight fleece"),
    ]
    for i, (pid, label) in enumerate(purchases):
        if len(events) >= 128:
            break
        add(
            type_="purchase",
            dt=datetime(2025, 4, 5, tzinfo=UTC) + timedelta(days=20 * i),
            content=f"Alex purchased {label}.",
            product_id=pid,
        )

    for i, label in enumerate(["ill-fitting gloves", "duplicate map case"]):
        add(
            type_="product_return",
            dt=datetime(2025, 10, 10 + i * 20, tzinfo=UTC),
            content=f"Alex returned {label}.",
            reason="Not needed",
        )

    # Trim or pad to target range
    while len(events) < 100:
        add(
            type_="browse",
            dt=noise_day,
            content="Alex browsed general outdoor clearance items.",
        )
        noise_day += timedelta(days=2)

    if len(events) > 150:
        events = events[:150]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps({"events": events}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(events)} events to {OUTPUT}")


if __name__ == "__main__":
    main()
