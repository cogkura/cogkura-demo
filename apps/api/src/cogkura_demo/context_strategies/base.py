"""Context strategy protocol and shared types."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from cogkura import MemoryContext

from cogkura_demo.models import AssociationPathResponse
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
    activation: float | None = None
    retrieval_reason: str | None = None
    raw_observation_ids: tuple[str, ...] = ()
    association_path: AssociationPathResponse | None = None
    relevance_tier: str | None = None
    structured_association_fit: float | None = None


@dataclass(frozen=True, slots=True)
class ContextStrategyDiagnostics:
    budget_tokens: int | None = None
    used_tokens: int | None = None
    remaining_tokens: int | None = None
    selected_units: int | None = None
    candidate_units: int | None = None
    unit_cap: int | None = None
    unit_cap_reached: bool | None = None
    budget_constrained: bool | None = None
    corpus_events: int | None = None
    prompt_budget_tokens: int | None = None


@dataclass(frozen=True, slots=True)
class PreparedCustomerContext:
    mode: ComparisonMode
    rendered: str
    estimated_tokens: int
    units: tuple[ContextUnit, ...]
    prepare_ms: float
    cogkura_context: MemoryContext | None = None
    diagnostics: ContextStrategyDiagnostics = field(default_factory=ContextStrategyDiagnostics)


class CustomerContextStrategy(Protocol):
    mode: ComparisonMode

    async def prepare(
        self,
        *,
        message: str,
        goal: str,
        snapshot: ComparisonSnapshot,
    ) -> PreparedCustomerContext: ...
