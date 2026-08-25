"""Context strategy protocol and shared types."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from cogkura import MemoryContext

from cogkura_demo.scenarios import HistoryEvent


class ComparisonMode(StrEnum):
    FULL_HISTORY = "full_history"
    SEARCH = "search"
    COGKURA = "cogkura"


MODE_LABELS: dict[ComparisonMode, str] = {
    ComparisonMode.FULL_HISTORY: "Full History",
    ComparisonMode.SEARCH: "Search (BM25)",
    ComparisonMode.COGKURA: "CogKura",
}


@dataclass(frozen=True, slots=True)
class ComparisonSnapshot:
    snapshot_id: str
    as_of: datetime
    history: tuple[HistoryEvent, ...]
    history_version: int


@dataclass(frozen=True, slots=True)
class ContextUnit:
    id: str
    text: str
    source_event_ids: tuple[str, ...]
    score: float | None = None
    kind: str | None = None


@dataclass(frozen=True, slots=True)
class PreparedCustomerContext:
    mode: ComparisonMode
    rendered: str
    estimated_tokens: int
    units: tuple[ContextUnit, ...]
    prepare_ms: float
    cogkura_context: MemoryContext | None = None


class CustomerContextStrategy(Protocol):
    mode: ComparisonMode

    async def prepare(
        self,
        *,
        message: str,
        goal: str,
        snapshot: ComparisonSnapshot,
    ) -> PreparedCustomerContext: ...
