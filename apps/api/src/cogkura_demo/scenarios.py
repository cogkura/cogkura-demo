"""Scenario data loading and event-to-observation mapping."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from cogkura import ObservationInput
from pydantic import BaseModel, Field

from cogkura_demo.config import CUSTOMER_ID, DEMO_AS_OF, TENANT_ID

EventType = Literal[
    "browse",
    "purchase",
    "product_return",
    "support_interaction",
    "preference_statement",
    "positive_outcome",
    "negative_outcome",
]


class SemanticFactSpec(BaseModel):
    predicate: str
    object_value: str
    cardinality: Literal["one", "many"] = "one"
    polarity: Literal["affirm", "deny"] = "affirm"


class HistoryEvent(BaseModel):
    id: str
    type: EventType
    customer_id: str
    occurred_at: datetime
    content: str
    product_id: str | None = None
    reason: str | None = None
    semantic_facts: list[SemanticFactSpec] = Field(default_factory=list)
    session_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CustomerRecord(BaseModel):
    id: str
    name: str
    customer_since: str
    order_count: int
    return_count: int


class TimelineEventRecord(BaseModel):
    id: str
    label: str
    detail: str
    occurred_at: str


class ScenarioRecord(BaseModel):
    id: str
    name: str
    prompt: str
    goal: str
    expected_concepts: list[str]
    excluded_concepts: list[str]
    timeline: list[TimelineEventRecord]


class ScenarioBundle(BaseModel):
    customer: CustomerRecord
    history: list[HistoryEvent]
    scenario: ScenarioRecord


def load_scenario_bundle(data_dir: Path) -> ScenarioBundle:
    customer_path = data_dir / "alex" / "customer.json"
    history_path = data_dir / "alex" / "history.json"
    scenario_path = data_dir / "alex" / "scenario.json"

    customer = CustomerRecord.model_validate_json(customer_path.read_text(encoding="utf-8"))
    history_payload = json.loads(history_path.read_text(encoding="utf-8"))
    history = [HistoryEvent.model_validate(item) for item in history_payload["events"]]
    scenario = ScenarioRecord.model_validate_json(scenario_path.read_text(encoding="utf-8"))
    return ScenarioBundle(customer=customer, history=history, scenario=scenario)


def event_to_observation(event: HistoryEvent) -> ObservationInput:
    metadata: dict[str, Any] = dict(event.metadata)
    if event.semantic_facts:
        metadata["semantic_facts"] = [
            fact.model_dump(exclude_none=True) for fact in event.semantic_facts
        ]
    if event.session_id:
        metadata["session_id"] = event.session_id
    if event.product_id:
        metadata["product_id"] = event.product_id
    if event.reason:
        metadata["reason"] = event.reason

    return ObservationInput(
        tenant_id=TENANT_ID,
        subject_id=CUSTOMER_ID,
        source_namespace="commerce",
        source_record_id=event.id,
        event_type=event.type,
        content=event.content,
        observed_at=event.occurred_at,
        metadata=metadata,
    )


def validate_history(bundle: ScenarioBundle) -> None:
    if not (100 <= len(bundle.history) <= 150):
        msg = f"Expected 100-150 history events, got {len(bundle.history)}"
        raise ValueError(msg)
    for event in bundle.history:
        if event.occurred_at >= DEMO_AS_OF:
            msg = f"Event {event.id} occurs after DEMO_AS_OF"
            raise ValueError(msg)
        if event.customer_id != CUSTOMER_ID:
            msg = f"Event {event.id} has wrong customer_id"
            raise ValueError(msg)
