"""CogKura memory bootstrap and context preparation."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from cogkura import LearningFeedback, LearningResult, Memory, MemoryContext, MemoryProcessingResult
from cogkura.algorithms.semantic import ComplementaryLearningSemanticConsolidator
from cogkura.algorithms.working_memory import TokenEstimator
from cogkura.models import StoredSemanticMemory

from cogkura_demo.config import CUSTOMER_ID, TENANT_ID
from cogkura_demo.models import (
    MemoryAssessmentResponse,
    MemoryContextResponse,
    MemoryItemResponse,
    ProcessingSummaryResponse,
    SemanticMemorySnapshot,
)
from cogkura_demo.scenarios import (
    HistoryEvent,
    ScenarioBundle,
    event_to_observation,
    load_scenario_bundle,
    validate_seed_history,
)
from cogkura_demo.session import DemoSession


def _create_memory(token_estimator: TokenEstimator) -> Memory:
    return Memory(
        token_estimator=token_estimator,
        semantic_consolidator=ComplementaryLearningSemanticConsolidator(
            minimum_supporting_episodes=1,
        ),
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
        self._memory = _create_memory(token_estimator)
        self._session: DemoSession | None = None

    @property
    def session(self) -> DemoSession:
        if self._session is None:
            msg = "Demo memory not initialised"
            raise RuntimeError(msg)
        return self._session

    @property
    def bundle(self) -> ScenarioBundle:
        return self.session.seed_bundle

    async def initialise(self) -> DemoSession:
        bundle = load_scenario_bundle(self._data_dir)
        validate_seed_history(bundle)
        self._memory = _create_memory(self._token_estimator)
        self._session = DemoSession(seed_bundle=bundle)
        for event in bundle.history:
            await self._memory.observe(event_to_observation(event))
        await self._memory.process(
            tenant_id=TENANT_ID,
            subject_id=CUSTOMER_ID,
            as_of=self._session.clock.current,
        )
        return self._session

    async def reset(self) -> DemoSession:
        bundle = load_scenario_bundle(self._data_dir)
        validate_seed_history(bundle)
        self._memory = _create_memory(self._token_estimator)
        self._session = DemoSession(seed_bundle=bundle)
        for event in bundle.history:
            await self._memory.observe(event_to_observation(event))
        await self._memory.process(
            tenant_id=TENANT_ID,
            subject_id=CUSTOMER_ID,
            as_of=self._session.clock.current,
        )
        return self._session

    async def observe_and_process(
        self,
        event: HistoryEvent,
        *,
        as_of: datetime,
    ) -> MemoryProcessingResult:
        await self._memory.observe(event_to_observation(event))
        return await self._memory.process(
            tenant_id=TENANT_ID,
            subject_id=CUSTOMER_ID,
            as_of=as_of,
        )

    async def prepare_customer_context(
        self,
        message: str,
        *,
        goal: str,
        as_of: datetime,
    ) -> MemoryContext:
        return await self._memory.prepare_context(
            message,
            tenant_id=TENANT_ID,
            subject_id=CUSTOMER_ID,
            goal=goal,
            prompt_budget_tokens=self._memory_budget_tokens,
            as_of=as_of,
            valid_at=as_of,
        )

    async def record_context_use(
        self,
        context: MemoryContext,
        *,
        request_id: str,
        referenced_at: datetime,
    ) -> None:
        await self._memory.record_context_use(
            context,
            request_id=request_id,
            referenced_at=referenced_at,
        )

    async def learn(self, feedback: LearningFeedback) -> LearningResult:
        return await self._memory.learn(feedback)

    async def semantic_snapshot(
        self,
        *,
        valid_at: datetime | None = None,
    ) -> list[SemanticMemorySnapshot]:
        memories = await self._memory.list_semantic_memories(
            tenant_id=TENANT_ID,
            subject_id=CUSTOMER_ID,
            valid_at=valid_at,
        )
        return [_map_semantic_memory(memory) for memory in memories]


def _map_semantic_memory(memory: StoredSemanticMemory) -> SemanticMemorySnapshot:
    return SemanticMemorySnapshot(
        memory_key=memory.memory_key,
        slot_key=memory.slot_key,
        revision_key=memory.revision_key,
        revision_number=memory.revision_number,
        statement=memory.statement,
        predicate=memory.predicate,
        object_value=memory.object_value,
        status=memory.status.value,
        valid_from=memory.valid_from.isoformat() if memory.valid_from else None,
        valid_until=memory.valid_until.isoformat() if memory.valid_until else None,
    )


def map_processing_summary(result: MemoryProcessingResult) -> ProcessingSummaryResponse:
    semantics = result.semantics
    return ProcessingSummaryResponse(
        created=semantics.created,
        updated=semantics.updated,
        reinforced=semantics.reinforced,
        conflicts=semantics.conflicts,
        superseded=semantics.superseded,
        revisions_created=semantics.revisions_created,
        revisions_updated=semantics.revisions_updated,
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
        revision_key = None
        if hasattr(item.memory, "revision_key"):
            revision_key = item.memory.revision_key
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
                memory_key=item.memory.memory_key,
                revision_key=revision_key,
                learned_utility=item.components.learned_utility,
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
