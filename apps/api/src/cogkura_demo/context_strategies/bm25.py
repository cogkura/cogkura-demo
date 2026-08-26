"""BM25 search context strategy."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass

from rank_bm25 import BM25Okapi  # type: ignore[import-untyped]

from cogkura_demo.catalogue import Catalogue
from cogkura_demo.context_strategies.base import (
    ComparisonMode,
    ComparisonSnapshot,
    ContextStrategyDiagnostics,
    ContextUnit,
    PreparedCustomerContext,
)
from cogkura_demo.metrics import TokenCounter, sort_history_chronologically
from cogkura_demo.scenarios import HistoryEvent

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def build_search_document(event: HistoryEvent, catalogue: Catalogue) -> str:
    parts = [event.type, event.content]
    if event.reason:
        parts.append(event.reason)
    if event.product_id:
        product = next(
            (item for item in catalogue.products if item.id == event.product_id),
            None,
        )
        if product is not None:
            parts.append(product.name)
        parts.append(event.product_id)
    for fact in event.semantic_facts:
        parts.append(fact.predicate)
        parts.append(fact.object_value)
    return " ".join(parts)


def render_search_event(event: HistoryEvent, *, rank: int) -> str:
    date = event.occurred_at.strftime("%d %b %Y")
    return f"{rank}. {date} — {event.type}\n{event.content}"


@dataclass(frozen=True, slots=True)
class RankedEvent:
    event: HistoryEvent
    score: float
    rank: int


@dataclass(frozen=True, slots=True)
class PackingResult:
    selected: list[RankedEvent]
    rendered: str
    used_tokens: int
    budget_constrained: bool
    event_cap_reached: bool


class Bm25SearchStrategy:
    mode = ComparisonMode.SEARCH

    def __init__(
        self,
        *,
        token_counter: TokenCounter,
        catalogue: Catalogue,
        budget_tokens: int,
        max_events: int,
    ) -> None:
        self._token_counter = token_counter
        self._catalogue = catalogue
        self._budget_tokens = budget_tokens
        self._max_events = max_events

    async def prepare(
        self,
        *,
        message: str,
        goal: str,
        snapshot: ComparisonSnapshot,
    ) -> PreparedCustomerContext:
        start = time.perf_counter()
        events = sort_history_chronologically(list(snapshot.history))
        ranked = self._rank_events(events=events, goal=goal, message=message)
        packing = self._pack_results(ranked)
        units = tuple(
            ContextUnit(
                id=item.event.id,
                text=render_search_event(item.event, rank=item.rank),
                source_event_ids=(item.event.id,),
                score=round(item.score, 4),
                kind=item.event.type,
            )
            for item in packing.selected
        )
        prepare_ms = (time.perf_counter() - start) * 1000.0
        diagnostics = ContextStrategyDiagnostics(
            budget_tokens=self._budget_tokens,
            used_tokens=packing.used_tokens,
            remaining_tokens=max(0, self._budget_tokens - packing.used_tokens),
            selected_units=len(packing.selected),
            candidate_units=len(ranked),
            unit_cap=self._max_events,
            unit_cap_reached=packing.event_cap_reached,
            budget_constrained=packing.budget_constrained,
            corpus_events=len(events),
        )
        return PreparedCustomerContext(
            mode=self.mode,
            rendered=packing.rendered,
            estimated_tokens=self._token_counter.count(packing.rendered),
            units=units,
            prepare_ms=round(prepare_ms, 1),
            diagnostics=diagnostics,
        )

    def _rank_events(
        self,
        *,
        events: list[HistoryEvent],
        goal: str,
        message: str,
    ) -> list[RankedEvent]:
        if not events:
            return []
        documents = [tokenize(build_search_document(event, self._catalogue)) for event in events]
        corpus = BM25Okapi(documents)
        query = tokenize(f"{goal} {message}")
        scores = corpus.get_scores(query)
        scored = list(zip(events, scores, strict=True))
        scored.sort(key=lambda item: (-item[1], -item[0].occurred_at.timestamp(), item[0].id))
        return [
            RankedEvent(event=event, score=float(score), rank=index + 1)
            for index, (event, score) in enumerate(scored)
        ]

    def _pack_results(self, ranked: list[RankedEvent]) -> PackingResult:
        selected: list[RankedEvent] = []
        lines: list[str] = []
        tokens_so_far = 0
        budget_constrained = False
        event_cap_reached = False

        for item in ranked:
            if len(selected) >= self._max_events:
                event_cap_reached = True
                break
            line = render_search_event(item.event, rank=item.rank)
            line_tokens = self._token_counter.count(line)
            separator_tokens = self._token_counter.count("\n\n") if lines else 0
            if tokens_so_far + separator_tokens + line_tokens > self._budget_tokens:
                budget_constrained = True
                continue
            if separator_tokens:
                tokens_so_far += separator_tokens
            tokens_so_far += line_tokens
            selected.append(item)
            lines.append(line)

        return PackingResult(
            selected=selected,
            rendered="\n\n".join(lines),
            used_tokens=tokens_so_far,
            budget_constrained=budget_constrained,
            event_cap_reached=event_cap_reached,
        )
