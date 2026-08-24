"""CogKura memory bootstrap and context preparation."""

from __future__ import annotations

from pathlib import Path

from cogkura import Memory, MemoryContext
from cogkura.algorithms.working_memory import TokenEstimator

from cogkura_demo.config import CUSTOMER_ID, DEMO_AS_OF, TENANT_ID
from cogkura_demo.models import MemoryAssessmentResponse, MemoryContextResponse, MemoryItemResponse
from cogkura_demo.scenarios import (
    ScenarioBundle,
    event_to_observation,
    load_scenario_bundle,
    validate_history,
)


class DemoMemory:
    def __init__(
        self,
        *,
        data_dir: Path,
        token_estimator: TokenEstimator,
        memory_budget_tokens: int,
    ) -> None:
        self._data_dir = data_dir
        self._token_estimator = token_estimator
        self._memory_budget_tokens = memory_budget_tokens
        self._memory = Memory(token_estimator=token_estimator)
        self._bundle: ScenarioBundle | None = None

    @property
    def bundle(self) -> ScenarioBundle:
        if self._bundle is None:
            msg = "Demo memory not initialised"
            raise RuntimeError(msg)
        return self._bundle

    async def initialise(self) -> ScenarioBundle:
        bundle = load_scenario_bundle(self._data_dir)
        validate_history(bundle)
        self._bundle = bundle
        self._memory = Memory(token_estimator=self._token_estimator)
        for event in bundle.history:
            await self._memory.observe(event_to_observation(event))
        await self._memory.process(
            tenant_id=TENANT_ID,
            subject_id=CUSTOMER_ID,
            as_of=DEMO_AS_OF,
        )
        return bundle

    async def reset(self) -> ScenarioBundle:
        return await self.initialise()

    async def prepare_customer_context(
        self,
        message: str,
        *,
        goal: str,
    ) -> MemoryContext:
        return await self._memory.prepare_context(
            message,
            tenant_id=TENANT_ID,
            subject_id=CUSTOMER_ID,
            goal=goal,
            prompt_budget_tokens=self._memory_budget_tokens,
            as_of=DEMO_AS_OF,
            valid_at=DEMO_AS_OF,
        )

    async def record_context_use(self, context: MemoryContext, *, request_id: str) -> None:
        await self._memory.record_context_use(
            context,
            request_id=request_id,
            referenced_at=DEMO_AS_OF,
        )


def map_memory_context(context: MemoryContext) -> MemoryContextResponse:
    items: list[MemoryItemResponse] = []
    for item in context.items:
        diagnostics = item.recall.diagnostics
        provenance = None
        if diagnostics is not None and diagnostics.observation_evidence_ids:
            provenance = ", ".join(diagnostics.observation_evidence_ids[:3])
        retrieval_reason = item.recall.reason
        if provenance:
            if retrieval_reason:
                retrieval_reason = f"{retrieval_reason} ({provenance})"
            else:
                retrieval_reason = provenance
        items.append(
            MemoryItemResponse(
                statement=item.memory.statement,
                memory_kind=item.memory_kind.value,
                score=item.recall.score,
                activation=item.recall.activation,
                retrieval_reason=retrieval_reason,
                selection_reason=item.reason,
                rank=item.rank,
                estimated_tokens=item.estimated_tokens,
            )
        )
    return MemoryContextResponse(
        rendered=context.render(),
        estimated_tokens=context.estimated_tokens,
        items=items,
        assessment=MemoryAssessmentResponse(
            flags=[flag.value for flag in context.assessment.flags],
        ),
    )
