"""CogKura context strategy."""

from __future__ import annotations

import time

from cogkura_demo.context_strategies.base import (
    ComparisonMode,
    ComparisonSnapshot,
    ContextStrategyDiagnostics,
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
                activation=item.activation,
                retrieval_reason=item.retrieval_reason,
                raw_observation_ids=tuple(item.raw_observation_ids),
                association_path=item.association_path,
                relevance_tier=item.relevance_tier,
                structured_association_fit=item.structured_association_fit,
                chunk_kind=item.chunk_kind,
                member_count=item.member_count,
                members_omitted=item.members_omitted,
                members=tuple(item.members),
            )
            for index, item in enumerate(mapped.items)
        )
        prepare_ms = (time.perf_counter() - start) * 1000.0
        diagnostics = ContextStrategyDiagnostics(
            budget_tokens=self._demo_memory.memory_budget_tokens,
            used_tokens=mapped.estimated_tokens,
            remaining_tokens=max(
                0,
                self._demo_memory.memory_budget_tokens - mapped.estimated_tokens,
            ),
            selected_units=len(units),
            prompt_budget_tokens=self._demo_memory.memory_budget_tokens,
        )
        return PreparedCustomerContext(
            mode=self.mode,
            rendered=mapped.rendered,
            estimated_tokens=mapped.estimated_tokens,
            units=units,
            prepare_ms=round(prepare_ms, 1),
            cogkura_context=context,
            diagnostics=diagnostics,
        )
