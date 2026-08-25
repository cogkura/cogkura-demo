"""CogKura context strategy."""

from __future__ import annotations

import time

from cogkura_demo.context_strategies.base import (
    ComparisonMode,
    ComparisonSnapshot,
    ContextUnit,
    PreparedCustomerContext,
)
from cogkura_demo.memory import DemoMemory


class CogKuraStrategy:
    mode = ComparisonMode.COGKURA

    def __init__(self, *, demo_memory: DemoMemory) -> None:
        self._demo_memory = demo_memory

    async def prepare(
        self,
        *,
        message: str,
        goal: str,
        snapshot: ComparisonSnapshot,
    ) -> PreparedCustomerContext:
        start = time.perf_counter()
        context = await self._demo_memory.prepare_customer_context(
            message,
            goal=goal,
            as_of=snapshot.as_of,
        )
        mapped = self._demo_memory.map_context(context)
        units = tuple(
            ContextUnit(
                id=item.memory_key or f"memory-{index}",
                text=item.statement,
                source_event_ids=tuple(item.source_event_ids),
                score=item.score,
                kind=item.memory_kind,
            )
            for index, item in enumerate(mapped.items)
        )
        prepare_ms = (time.perf_counter() - start) * 1000.0
        return PreparedCustomerContext(
            mode=self.mode,
            rendered=mapped.rendered,
            estimated_tokens=mapped.estimated_tokens,
            units=units,
            prepare_ms=round(prepare_ms, 1),
            cogkura_context=context,
        )
