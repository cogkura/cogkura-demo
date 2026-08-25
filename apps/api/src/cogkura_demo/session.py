"""Mutable demo session state."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from cogkura import MemoryContext

from cogkura_demo.config import DEMO_AS_OF
from cogkura_demo.scenarios import HistoryEvent, ScenarioBundle, TimelineEventRecord


@dataclass
class DemoClock:
    baseline: datetime = DEMO_AS_OF
    current: datetime = DEMO_AS_OF

    def advance(self) -> datetime:
        self.current = self.current + timedelta(days=1)
        return self.current

    def reset(self) -> None:
        self.current = self.baseline


@dataclass
class DemoOrder:
    id: str
    product_id: str
    turn_id: str
    purchased_at: datetime
    returned_at: datetime | None = None


@dataclass
class AgentTurnRecord:
    turn_id: str
    occurred_at: datetime
    context: MemoryContext
    response_id: str | None
    recommended_product_ids: tuple[str, ...]
    message: str


@dataclass
class MemoryValueChange:
    predicate: str
    before: str | None
    after: str | None
    kind: str = "current_value_changed"


@dataclass
class ProcessedClientEvent:
    client_event_id: str
    response_payload: dict[str, object]


@dataclass
class DemoSession:
    seed_bundle: ScenarioBundle
    live_events: list[HistoryEvent] = field(default_factory=list)
    turn_records: dict[str, AgentTurnRecord] = field(default_factory=dict)
    live_orders: dict[str, DemoOrder] = field(default_factory=dict)
    memory_changes: list[MemoryValueChange] = field(default_factory=list)
    clock: DemoClock = field(default_factory=DemoClock)
    turn_counter: int = 0
    processed_client_events: dict[str, ProcessedClientEvent] = field(default_factory=dict)
    last_learning: dict[str, object] | None = None
    last_mutation: dict[str, object] | None = None
    live_event_counter: int = 0
    live_order_counter: int = 0
    live_purchase_count: int = 0
    live_return_count: int = 0

    @property
    def history(self) -> list[HistoryEvent]:
        return [*self.seed_bundle.history, *self.live_events]

    @property
    def history_event_count(self) -> int:
        return len(self.history)

    @property
    def order_count(self) -> int:
        return self.seed_bundle.customer.order_count + self.live_purchase_count

    @property
    def return_count(self) -> int:
        return self.seed_bundle.customer.return_count + self.live_return_count

    def next_turn_id(self) -> str:
        self.turn_counter += 1
        return f"turn-{self.turn_counter:03d}"

    def next_live_event_id(self, prefix: str) -> str:
        self.live_event_counter += 1
        return f"live-{prefix}-{self.live_event_counter:03d}"

    def next_order_id(self) -> str:
        self.live_order_counter += 1
        return f"demo-order-{self.live_order_counter:03d}"

    def reset(self, bundle: ScenarioBundle) -> None:
        self.seed_bundle = bundle
        self.live_events.clear()
        self.turn_records.clear()
        self.live_orders.clear()
        self.memory_changes.clear()
        self.clock.reset()
        self.turn_counter = 0
        self.processed_client_events.clear()
        self.last_learning = None
        self.last_mutation = None
        self.live_event_counter = 0
        self.live_order_counter = 0
        self.live_purchase_count = 0
        self.live_return_count = 0

    def build_timeline(self) -> list[TimelineEventRecord]:
        seed = list(self.seed_bundle.scenario.timeline)
        live_entries: list[TimelineEventRecord] = []
        for event in self.live_events:
            label = event.occurred_at.strftime("%b %Y")
            if event.type == "preference_statement":
                detail = event.content
            elif event.type == "purchase":
                product = event.product_id or "product"
                detail = f"Purchase — {product.replace('-', ' ').title()}"
            elif event.type == "product_return":
                detail = f"Return — {event.content}"
            else:
                detail = event.content
            live_entries.append(
                TimelineEventRecord(
                    id=event.id,
                    label=f"{label} · New",
                    detail=detail,
                    occurred_at=event.occurred_at.date().isoformat(),
                )
            )
        return [*seed, *live_entries]
