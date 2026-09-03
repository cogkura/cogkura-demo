"""CogKura memory bootstrap and context preparation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path

from cogkura import LearningFeedback, LearningResult, Memory, MemoryContext, MemoryProcessingResult
from cogkura.algorithms.semantic import ComplementaryLearningSemanticConsolidator
from cogkura.algorithms.working_memory import TokenEstimator
from cogkura.models import (
    AssociationPath,
    RelationshipEdge,
    StoredSemanticMemory,
    WorkingMemoryItem,
)
from cogkura.storage import InMemoryObservationStore

from cogkura_demo.config import CUSTOMER_ID, TENANT_ID
from cogkura_demo.models import (
    AssociationPathResponse,
    MemoryAssessmentResponse,
    MemoryContextResponse,
    MemoryItemResponse,
    ProcessingSummaryResponse,
    RelationshipEdgeResponse,
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
from cogkura_demo.taxonomy import (
    build_entity_relationships,
    build_taxonomy_observation,
    load_catalogue,
    load_retailer_taxonomy,
)


def _create_memory(
    token_estimator: TokenEstimator,
    observation_store: InMemoryObservationStore,
) -> Memory:
    return Memory(
        token_estimator=token_estimator,
        observation_store=observation_store,
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
        seed_taxonomy: bool = True,
    ) -> None:
        self._data_dir = data_dir
        self._token_estimator = token_estimator
        self._memory_budget_tokens = memory_budget_tokens
        self._seed_taxonomy = seed_taxonomy
        self._observation_store = InMemoryObservationStore()
        self._memory = _create_memory(token_estimator, self._observation_store)
        self._event_ids_by_observation: dict[str, str] = {}
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

    @property
    def memory_budget_tokens(self) -> int:
        return self._memory_budget_tokens

    async def initialise(self) -> DemoSession:
        return await self._rebuild_from_seed()

    async def reset(self) -> DemoSession:
        return await self._rebuild_from_seed()

    async def observe_and_process(
        self,
        event: HistoryEvent,
        *,
        as_of: datetime,
    ) -> MemoryProcessingResult:
        await self._memory.observe(event_to_observation(event))
        result = await self._memory.process(
            tenant_id=TENANT_ID,
            subject_id=CUSTOMER_ID,
            as_of=as_of,
        )
        await self._refresh_observation_event_ids()
        return result

    def map_context(self, context: MemoryContext) -> MemoryContextResponse:
        return map_memory_context(
            context,
            event_ids_by_observation=self._event_ids_by_observation,
        )

    async def _rebuild_from_seed(self) -> DemoSession:
        bundle = load_scenario_bundle(self._data_dir)
        validate_seed_history(bundle)
        self._observation_store = InMemoryObservationStore()
        self._memory = _create_memory(self._token_estimator, self._observation_store)
        self._session = DemoSession(seed_bundle=bundle)
        if self._seed_taxonomy:
            catalogue = load_catalogue(self._data_dir)
            taxonomy = load_retailer_taxonomy(self._data_dir)
            relationships = build_entity_relationships(catalogue, taxonomy)
            taxonomy_observation = build_taxonomy_observation(
                relationships=relationships,
                observed_at=self._session.clock.current,
            )
            await self._memory.observe(taxonomy_observation)
        for event in bundle.history:
            await self._memory.observe(event_to_observation(event))
        await self._memory.process(
            tenant_id=TENANT_ID,
            subject_id=CUSTOMER_ID,
            as_of=self._session.clock.current,
        )
        await self._refresh_observation_event_ids()
        return self._session

    async def _refresh_observation_event_ids(self) -> None:
        observations = await self._observation_store.list(
            tenant_id=TENANT_ID,
            subject_id=CUSTOMER_ID,
        )
        self._event_ids_by_observation = {
            observation.id: observation.source_record_id for observation in observations
        }

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


def _resolve_source_event_ids(
    observation_ids: Sequence[str],
    event_ids_by_observation: Mapping[str, str] | None,
) -> list[str]:
    if not observation_ids:
        return []
    if event_ids_by_observation is None:
        return list(observation_ids)
    resolved: list[str] = []
    seen: set[str] = set()
    for observation_id in observation_ids:
        event_id = event_ids_by_observation.get(observation_id)
        if event_id is None or event_id in seen:
            continue
        seen.add(event_id)
        resolved.append(event_id)
    return resolved


def _map_relationship_edge(edge: RelationshipEdge) -> RelationshipEdgeResponse:
    return RelationshipEdgeResponse(
        relationship_id=edge.relationship_id,
        relation_type=edge.relation_type,
        direction=edge.direction,
        source_entity_id=edge.source_entity_id,
        target_entity_id=edge.target_entity_id,
        weight=edge.weight,
        provenance=edge.provenance,
    )


def _observation_ids_from_item(item: WorkingMemoryItem) -> list[str]:
    recalls = item.member_recalls or (item.recall,)
    ordered: list[str] = []
    seen: set[str] = set()
    for recall in recalls:
        diagnostics = recall.diagnostics
        if diagnostics is None or not diagnostics.observation_evidence_ids:
            continue
        for observation_id in diagnostics.observation_evidence_ids:
            if observation_id in seen:
                continue
            seen.add(observation_id)
            ordered.append(observation_id)
    return ordered


def _item_statement(item: WorkingMemoryItem) -> str:
    if item.chunk is not None:
        return item.chunk.serialized_text
    return item.memory.statement


def _map_association_path(path: AssociationPath | None) -> AssociationPathResponse | None:
    if path is None:
        return None
    return AssociationPathResponse(
        matched_features=list(path.matched_features),
        seed_episode_id=path.seed_episode_id,
        seed_entity_id=path.seed_entity_id,
        bridge_entity_id=path.bridge_entity_id,
        related_episode_id=path.related_episode_id,
        hop_kind=path.hop_kind,
        weight=path.weight,
        hop_count=path.hop_count,
        seed_relevance=path.seed_relevance,
        relationship_edges=[_map_relationship_edge(edge) for edge in path.relationship_edges],
    )


def map_memory_context(
    context: MemoryContext,
    *,
    event_ids_by_observation: Mapping[str, str] | None = None,
) -> MemoryContextResponse:
    items: list[MemoryItemResponse] = []
    for item in context.items:
        diagnostics = item.recall.diagnostics
        provenance = None
        raw_observation_ids = _observation_ids_from_item(item)
        source_event_ids = _resolve_source_event_ids(
            raw_observation_ids,
            event_ids_by_observation,
        )
        if source_event_ids:
            provenance = ", ".join(source_event_ids[:3])
        retrieval_reason = item.recall.reason
        if provenance:
            if retrieval_reason:
                retrieval_reason = f"{retrieval_reason} ({provenance})"
            else:
                retrieval_reason = provenance
        revision_key = None
        if hasattr(item.memory, "revision_key"):
            revision_key = item.memory.revision_key
        association_path = None
        if diagnostics is not None:
            association_path = _map_association_path(diagnostics.association_path)
        items.append(
            MemoryItemResponse(
                statement=_item_statement(item),
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
                source_event_ids=source_event_ids,
                raw_observation_ids=raw_observation_ids,
                association_path=association_path,
                relevance_tier=diagnostics.relevance_tier if diagnostics else None,
                structured_association_fit=(
                    diagnostics.structured_association_fit if diagnostics else None
                ),
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
