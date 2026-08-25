"""Configured customer statement and return-reason mapping."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from cogkura_demo.config import CUSTOMER_ID
from cogkura_demo.scenarios import EventType, HistoryEvent, SemanticFactSpec


class StatementInteraction(BaseModel):
    id: str
    label: str
    message: str
    event_type: EventType
    content_template: str
    semantic_facts: list[SemanticFactSpec] = Field(default_factory=list)


class ReturnReasonInteraction(BaseModel):
    id: str
    label: str
    reason: str
    semantic_facts: list[SemanticFactSpec] = Field(default_factory=list)


class InteractionsConfig(BaseModel):
    statements: list[StatementInteraction] = Field(default_factory=list)
    return_reasons: list[ReturnReasonInteraction] = Field(default_factory=list)


def load_interactions(data_dir: Path) -> InteractionsConfig:
    path = data_dir / "alex" / "interactions.json"
    return InteractionsConfig.model_validate_json(path.read_text(encoding="utf-8"))


def _normalise_message(message: str) -> str:
    collapsed = re.sub(r"\s+", " ", message.strip().lower())
    return collapsed.rstrip(".")


class DemoInteractionMapper:
    def __init__(self, config: InteractionsConfig) -> None:
        self._statements = {_normalise_message(item.message): item for item in config.statements}
        self._return_reasons = {item.id: item for item in config.return_reasons}
        self.statements = config.statements

    def matches_statement(self, message: str) -> bool:
        return _normalise_message(message) in self._statements

    def map_statement(
        self,
        message: str,
        *,
        occurred_at: datetime,
        event_id: str,
    ) -> HistoryEvent | None:
        statement = self._statements.get(_normalise_message(message))
        if statement is None:
            return None
        facts: list[SemanticFactSpec] = []
        for fact in statement.semantic_facts:
            data = fact.model_dump()
            if fact.valid_from_from_event:
                data["valid_from"] = occurred_at
                data.pop("valid_from_from_event", None)
            if fact.valid_until_from_event:
                data["valid_until"] = occurred_at
                data.pop("valid_until_from_event", None)
            facts.append(SemanticFactSpec.model_validate(data))
        return HistoryEvent(
            id=event_id,
            type=statement.event_type,
            customer_id=CUSTOMER_ID,
            occurred_at=occurred_at,
            content=statement.content_template,
            semantic_facts=facts,
            session_id=f"sess-{statement.id}",
        )

    def get_return_reason(self, reason_id: str) -> ReturnReasonInteraction | None:
        return self._return_reasons.get(reason_id)

    @property
    def return_reasons(self) -> list[ReturnReasonInteraction]:
        return list(self._return_reasons.values())
