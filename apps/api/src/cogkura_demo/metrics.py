"""Token estimation and history baseline metrics."""

from __future__ import annotations

from typing import Protocol

import tiktoken

from cogkura_demo.scenarios import HistoryEvent


class TokenCounter(Protocol):
    def count(self, text: str) -> int: ...


class TiktokenCounter:
    """Shared token counter for baseline history and CogKura budget alignment."""

    def __init__(self, model: str) -> None:
        try:
            self._encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            self._encoding = tiktoken.get_encoding("cl100k_base")

    def count(self, text: str) -> int:
        if not text:
            return 0
        return len(self._encoding.encode(text))


class CogkuraTokenEstimator:
    """Adapter for cogkura TokenEstimator protocol."""

    def __init__(self, counter: TokenCounter) -> None:
        self._counter = counter

    def estimate(self, text: str) -> int:
        if not text:
            return 0
        return max(1, self._counter.count(text))


def sort_history_chronologically(events: list[HistoryEvent]) -> list[HistoryEvent]:
    return sorted(events, key=lambda event: (event.occurred_at, event.id))


def serialize_history_line(event: HistoryEvent) -> str:
    date = event.occurred_at.strftime("%Y-%m-%d")
    parts = [date, event.type, event.content]
    if event.product_id:
        parts.append(event.product_id)
    if event.reason:
        parts.append(event.reason)
    return " | ".join(parts)


def render_full_history(events: list[HistoryEvent]) -> str:
    ordered = sort_history_chronologically(events)
    lines = [serialize_history_line(event) for event in ordered]
    return "\n".join(lines)


def serialize_full_history(events: list[HistoryEvent]) -> str:
    return render_full_history(events)


def estimate_full_history_tokens(events: list[HistoryEvent], counter: TokenCounter) -> int:
    return counter.count(serialize_full_history(events))


def history_reduction_percent(full_history_tokens: int, memory_context_tokens: int) -> float:
    if full_history_tokens <= 0:
        return 0.0
    reduction = (1.0 - (memory_context_tokens / full_history_tokens)) * 100.0
    return round(max(0.0, reduction), 1)
