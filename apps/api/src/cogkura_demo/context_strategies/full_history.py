"""Full history context strategy."""

from __future__ import annotations

import time

from cogkura_demo.context_strategies.base import (
    ComparisonMode,
    ComparisonSnapshot,
    ContextUnit,
    PreparedCustomerContext,
)
from cogkura_demo.metrics import (
    TokenCounter,
    render_full_history,
    sort_history_chronologically,
)


class FullHistoryStrategy:
    mode = ComparisonMode.FULL_HISTORY

    def __init__(self, *, token_counter: TokenCounter) -> None:
        self._token_counter = token_counter

    async def prepare(
        self,
        *,
        message: str,
        goal: str,
        snapshot: ComparisonSnapshot,
    ) -> PreparedCustomerContext:
        del message, goal
        start = time.perf_counter()
        events = sort_history_chronologically(list(snapshot.history))
        rendered = render_full_history(events)
        units = tuple(
            ContextUnit(
                id=event.id,
                text=render_full_history([event]),
                source_event_ids=(event.id,),
                kind=event.type,
            )
            for event in events
        )
        prepare_ms = (time.perf_counter() - start) * 1000.0
        return PreparedCustomerContext(
            mode=self.mode,
            rendered=rendered,
            estimated_tokens=self._token_counter.count(rendered),
            units=units,
            prepare_ms=round(prepare_ms, 1),
        )
