"""Retailer taxonomy and structured relationship tests."""

from __future__ import annotations

import pytest

from cogkura_demo.catalogue import load_catalogue
from cogkura_demo.comparison import ComparisonService
from cogkura_demo.config import CUSTOMER_ID, DATA_DIR, DEMO_AS_OF, TENANT_ID, get_settings
from cogkura_demo.context_strategies.bm25 import Bm25SearchStrategy, build_search_document
from cogkura_demo.context_strategies.full_history import FullHistoryStrategy
from cogkura_demo.evaluation import ComparisonEvaluator, load_comparison_config
from cogkura_demo.memory import DemoMemory
from cogkura_demo.metrics import CogkuraTokenEstimator, TiktokenCounter
from cogkura_demo.models import ComparisonRequest
from cogkura_demo.scenarios import load_scenario_bundle
from cogkura_demo.taxonomy import (
    TAXONOMY_RELATION_TYPE,
    build_entity_relationships,
    build_taxonomy_observation,
    load_catalogue_relationships,
    load_retailer_taxonomy,
    taxonomy_inventory,
)

JACKET_PROMPT = (
    "I'm looking for a waterproof jacket for a hiking trip to Scotland "
    "next month. What would you recommend?"
)
GOAL = "Help Alex choose an appropriate waterproof hiking jacket."


@pytest.fixture
def counter() -> TiktokenCounter:
    return TiktokenCounter("gpt-4.1-mini")


@pytest.fixture
async def structured_memory(counter: TiktokenCounter) -> DemoMemory:
    memory = DemoMemory(
        data_dir=DATA_DIR,
        token_estimator=CogkuraTokenEstimator(counter),
        memory_budget_tokens=750,
        seed_taxonomy=True,
    )
    await memory.initialise()
    return memory


@pytest.fixture
async def legacy_memory(counter: TiktokenCounter) -> DemoMemory:
    memory = DemoMemory(
        data_dir=DATA_DIR,
        token_estimator=CogkuraTokenEstimator(counter),
        memory_budget_tokens=750,
        seed_taxonomy=False,
    )
    await memory.initialise()
    return memory


def test_taxonomy_relationships_are_query_independent() -> None:
    relationships = load_catalogue_relationships(DATA_DIR)
    inventory = taxonomy_inventory(relationships)
    assert inventory.relationship_count == 14
    assert inventory.entity_count == 15
    assert inventory.relationship_type_counts == {TAXONOMY_RELATION_TYPE: 14}
    assert all(
        relationship.source_entity_id != relationship.target_entity_id
        for relationship in relationships
    )


def test_northpeak_catalogue_path_exists() -> None:
    relationships = load_catalogue_relationships(DATA_DIR)
    by_source = {
        (relationship.source_entity_id, relationship.target_entity_id)
        for relationship in relationships
    }
    assert ("northpeak-alpine-shell", "waterproof-jacket") in by_source
    assert ("waterproof-jacket", "jacket") in by_source
    assert ("breeze-windbreaker", "jacket") in by_source


def test_taxonomy_entity_ids_match_history_product_ids() -> None:
    relationships = load_catalogue_relationships(DATA_DIR)
    entity_ids = {relationship.source_entity_id for relationship in relationships} | {
        relationship.target_entity_id for relationship in relationships
    }
    jacket_scenario_product_ids = {
        "northpeak-alpine-shell",
        "breeze-windbreaker",
        "glacier-ski-jacket",
    }
    assert jacket_scenario_product_ids.issubset(entity_ids)


def test_seed_history_event_count_and_content_unchanged() -> None:
    bundle = load_scenario_bundle(DATA_DIR)
    assert len(bundle.history) == 134
    northpeak_return = next(event for event in bundle.history if event.id == "evt-022")
    assert "sleeves were too short" in northpeak_return.content


@pytest.mark.asyncio
async def test_taxonomy_ingested_through_public_observe_api(
    structured_memory: DemoMemory,
) -> None:
    relationships = await structured_memory._memory.list_entity_relationships(
        tenant_id=TENANT_ID,
    )
    assert len(relationships) == 14


@pytest.mark.asyncio
async def test_legacy_mode_has_no_relationship_graph(legacy_memory: DemoMemory) -> None:
    relationships = await legacy_memory._memory.list_entity_relationships(
        tenant_id=TENANT_ID,
    )
    assert len(relationships) == 0


@pytest.mark.asyncio
async def test_event_observation_sets_entity_ids() -> None:
    bundle = load_scenario_bundle(DATA_DIR)
    northpeak_return = next(event for event in bundle.history if event.id == "evt-022")
    from cogkura_demo.scenarios import event_to_observation

    observation = event_to_observation(northpeak_return)
    assert observation.metadata["entity_ids"] == ["northpeak-alpine-shell"]
    facts = observation.metadata["semantic_facts"]
    assert facts[0]["object_entity_id"] == "northpeak-alpine-shell"


@pytest.mark.asyncio
async def test_full_history_and_search_unchanged_with_structured_taxonomy(
    structured_memory: DemoMemory,
    counter: TiktokenCounter,
) -> None:
    snapshot = structured_memory.session.snapshot(snapshot_id="taxonomy-fairness")
    full_history = FullHistoryStrategy(token_counter=counter)
    search = Bm25SearchStrategy(
        token_counter=counter,
        catalogue=load_catalogue(DATA_DIR),
        budget_tokens=750,
        max_events=100,
    )
    full = await full_history.prepare(message=JACKET_PROMPT, goal=GOAL, snapshot=snapshot)
    bm25 = await search.prepare(message=JACKET_PROMPT, goal=GOAL, snapshot=snapshot)
    assert full.estimated_tokens == 2335
    assert len(full.units) == 134
    assert bm25.estimated_tokens == 703
    assert len(bm25.units) == 34


def test_bm25_corpus_excludes_taxonomy_metadata() -> None:
    bundle = load_scenario_bundle(DATA_DIR)
    catalogue = load_catalogue(DATA_DIR)
    taxonomy = load_retailer_taxonomy(DATA_DIR)
    relationships = build_entity_relationships(catalogue, taxonomy)
    taxonomy_text = " ".join(
        f"{relationship.source_entity_id} {relationship.relation_type} "
        f"{relationship.target_entity_id}"
        for relationship in relationships
    )
    for event in bundle.history:
        document = build_search_document(event, catalogue)
        assert taxonomy_text not in document
        assert "catalog.taxonomy" not in document


@pytest.mark.asyncio
async def test_structured_recall_returns_northpeak_and_lightweight_semantics(
    structured_memory: DemoMemory,
) -> None:
    inspection = await structured_memory._memory.inspect_recall(
        JACKET_PROMPT,
        tenant_id=TENANT_ID,
        subject_id=CUSTOMER_ID,
        limit=50,
        as_of=DEMO_AS_OF,
        valid_at=DEMO_AS_OF,
    )
    assert inspection.relationship_seed_count >= 1
    assert inspection.relationship_paths_used >= 1
    returned_statements = {
        getattr(candidate.memory, "statement", "").lower() for candidate in inspection.returned
    }
    assert any("northpeak" in statement for statement in returned_statements)
    assert any("lightweight" in statement for statement in returned_statements)
    structured = [
        candidate
        for candidate in inspection.returned
        if candidate.diagnostics is not None
        and candidate.diagnostics.relevance_tier == "structured_relation"
    ]
    assert len(structured) >= 2


@pytest.mark.asyncio
async def test_structured_semantics_recalled_and_selected(
    structured_memory: DemoMemory,
    counter: TiktokenCounter,
) -> None:
    service = ComparisonService(
        demo_memory=structured_memory,
        catalogue=load_catalogue(DATA_DIR),
        token_counter=counter,
        evaluator=ComparisonEvaluator(load_comparison_config(DATA_DIR)),
        llm_client=None,
        model_available=False,
        search_budget_tokens=get_settings().search_context_budget_tokens,
        search_max_events=get_settings().search_max_events,
    )
    run = await service.compare(
        ComparisonRequest(message=JACKET_PROMPT, generate_answers=False),
    )
    cogkura = next(result for result in run.response.results if result.mode == "cogkura")
    assert cogkura.metrics.context_tokens == 135
    assert cogkura.metrics.context_units == 6
    assert cogkura.relevance.expected_concepts_found == 5
    assert cogkura.relevance.concepts_missing == []
    selected_text = " ".join(unit.text.lower() for unit in cogkura.context.units)
    assert "northpeak" in selected_text
    assert "lightweight" in selected_text


@pytest.mark.asyncio
async def test_legacy_compare_matches_run_b_baseline(
    legacy_memory: DemoMemory,
    counter: TiktokenCounter,
) -> None:
    service = ComparisonService(
        demo_memory=legacy_memory,
        catalogue=load_catalogue(DATA_DIR),
        token_counter=counter,
        evaluator=ComparisonEvaluator(load_comparison_config(DATA_DIR)),
        llm_client=None,
        model_available=False,
        search_budget_tokens=get_settings().search_context_budget_tokens,
        search_max_events=get_settings().search_max_events,
    )
    run = await service.compare(
        ComparisonRequest(message=JACKET_PROMPT, generate_answers=False),
    )
    cogkura = next(result for result in run.response.results if result.mode == "cogkura")
    inspection = await legacy_memory._memory.inspect_recall(
        JACKET_PROMPT,
        tenant_id=TENANT_ID,
        subject_id=CUSTOMER_ID,
        limit=50,
        as_of=DEMO_AS_OF,
        valid_at=DEMO_AS_OF,
    )
    assert inspection.relationship_seed_count == 0
    assert inspection.relationship_paths_used == 0
    assert cogkura.relevance.expected_concepts_found == 3
    assert cogkura.metrics.context_units == 4
    assert cogkura.metrics.context_tokens == 90


@pytest.mark.asyncio
async def test_deterministic_taxonomy_replay(structured_memory: DemoMemory) -> None:
    first = await structured_memory._memory.list_entity_relationships(tenant_id=TENANT_ID)
    first_ids = tuple(relationship.relationship_id for relationship in first)
    await structured_memory.reset()
    second = await structured_memory._memory.list_entity_relationships(tenant_id=TENANT_ID)
    second_ids = tuple(relationship.relationship_id for relationship in second)
    assert first_ids == second_ids


@pytest.mark.asyncio
async def test_northpeak_relationship_causality(counter: TiktokenCounter) -> None:
    catalogue = load_catalogue(DATA_DIR)
    taxonomy = load_retailer_taxonomy(DATA_DIR)
    relationships = tuple(
        relationship
        for relationship in build_entity_relationships(catalogue, taxonomy)
        if relationship.source_entity_id != "northpeak-alpine-shell"
    )
    memory = DemoMemory(
        data_dir=DATA_DIR,
        token_estimator=CogkuraTokenEstimator(counter),
        memory_budget_tokens=750,
        seed_taxonomy=False,
    )
    bundle = load_scenario_bundle(DATA_DIR)
    from cogkura_demo.session import DemoSession

    memory._observation_store = memory._observation_store.__class__()
    from cogkura_demo.memory import _create_memory

    memory._memory = _create_memory(memory._token_estimator, memory._observation_store)
    memory._session = DemoSession(seed_bundle=bundle)
    await memory._memory.observe(
        build_taxonomy_observation(
            relationships=relationships,
            observed_at=memory._session.clock.current,
        )
    )
    from cogkura_demo.scenarios import event_to_observation

    for event in bundle.history:
        await memory._memory.observe(event_to_observation(event))
    await memory._memory.process(
        tenant_id=TENANT_ID,
        subject_id=CUSTOMER_ID,
        as_of=memory._session.clock.current,
    )
    inspection = await memory._memory.inspect_recall(
        JACKET_PROMPT,
        tenant_id=TENANT_ID,
        subject_id=CUSTOMER_ID,
        limit=50,
        as_of=DEMO_AS_OF,
        valid_at=DEMO_AS_OF,
    )
    northpeak_semantics = [
        candidate
        for candidate in inspection.returned
        if getattr(candidate.memory, "predicate", None) == "product_fit_issue"
    ]
    assert not any(
        candidate.diagnostics is not None
        and candidate.diagnostics.relevance_tier == "structured_relation"
        for candidate in northpeak_semantics
    )


@pytest.mark.asyncio
async def test_semantic_support_unchanged_by_relationship_seed(
    legacy_memory: DemoMemory,
    structured_memory: DemoMemory,
) -> None:
    legacy_snapshot = await legacy_memory.semantic_snapshot(valid_at=DEMO_AS_OF)
    structured_snapshot = await structured_memory.semantic_snapshot(valid_at=DEMO_AS_OF)
    legacy_by_key = {item.memory_key: item for item in legacy_snapshot}
    structured_by_key = {item.memory_key: item for item in structured_snapshot}
    assert legacy_by_key.keys() == structured_by_key.keys()
    for key, legacy_item in legacy_by_key.items():
        structured_item = structured_by_key[key]
        assert legacy_item.statement == structured_item.statement
        assert legacy_item.predicate == structured_item.predicate
        assert legacy_item.object_value == structured_item.object_value
