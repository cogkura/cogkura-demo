"""Retailer catalogue taxonomy for CogKura entity relationships."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from cogkura import ObservationInput
from pydantic import BaseModel, Field

from cogkura_demo.catalogue import Catalogue, load_catalogue
from cogkura_demo.config import TENANT_ID

TAXONOMY_SOURCE_NAMESPACE = "catalog.taxonomy"
TAXONOMY_SOURCE_RECORD_ID = "taxonomy-jackets"
TAXONOMY_RELATION_TYPE = "is_a"
TAXONOMY_PROVENANCE = "retailer-catalogue"


class CategoryParentSpec(BaseModel):
    category_id: str
    parent_id: str


class HistoricalProductSpec(BaseModel):
    product_id: str
    parent_id: str


class RetailerTaxonomy(BaseModel):
    category_parents: list[CategoryParentSpec] = Field(default_factory=list)
    historical_products: list[HistoricalProductSpec] = Field(default_factory=list)


@dataclass(frozen=True, slots=True)
class EntityRelationshipSpec:
    source_entity_id: str
    relation_type: str
    target_entity_id: str
    provenance: str = TAXONOMY_PROVENANCE


@dataclass(frozen=True, slots=True)
class TaxonomyInventory:
    entity_count: int
    relationship_count: int
    relationship_type_counts: dict[str, int]


def load_retailer_taxonomy(data_dir: Path) -> RetailerTaxonomy:
    path = data_dir / "retailer-taxonomy.json"
    return RetailerTaxonomy.model_validate_json(path.read_text(encoding="utf-8"))


def build_entity_relationships(
    catalogue: Catalogue,
    taxonomy: RetailerTaxonomy,
) -> tuple[EntityRelationshipSpec, ...]:
    relationships: list[EntityRelationshipSpec] = []
    seen: set[tuple[str, str, str]] = set()

    def add(source_entity_id: str, target_entity_id: str) -> None:
        if source_entity_id == target_entity_id:
            msg = f"Self-loop relationship: {source_entity_id}"
            raise ValueError(msg)
        key = (source_entity_id, TAXONOMY_RELATION_TYPE, target_entity_id)
        if key in seen:
            return
        seen.add(key)
        relationships.append(
            EntityRelationshipSpec(
                source_entity_id=source_entity_id,
                relation_type=TAXONOMY_RELATION_TYPE,
                target_entity_id=target_entity_id,
            )
        )

    for product in catalogue.products:
        add(product.id, product.category)

    for category_parent in taxonomy.category_parents:
        add(category_parent.category_id, category_parent.parent_id)

    for historical_product in taxonomy.historical_products:
        add(historical_product.product_id, historical_product.parent_id)

    return tuple(relationships)


def relationships_to_metadata(
    relationships: tuple[EntityRelationshipSpec, ...],
) -> list[dict[str, Any]]:
    return [
        {
            "source_entity_id": relationship.source_entity_id,
            "relation_type": relationship.relation_type,
            "target_entity_id": relationship.target_entity_id,
            "provenance": relationship.provenance,
        }
        for relationship in relationships
    ]


def taxonomy_inventory(relationships: tuple[EntityRelationshipSpec, ...]) -> TaxonomyInventory:
    entities: set[str] = set()
    type_counts: Counter[str] = Counter()
    for relationship in relationships:
        entities.add(relationship.source_entity_id)
        entities.add(relationship.target_entity_id)
        type_counts[relationship.relation_type] += 1
    return TaxonomyInventory(
        entity_count=len(entities),
        relationship_count=len(relationships),
        relationship_type_counts=dict(type_counts),
    )


def build_taxonomy_observation(
    *,
    relationships: tuple[EntityRelationshipSpec, ...],
    observed_at: datetime,
) -> ObservationInput:
    return ObservationInput(
        tenant_id=TENANT_ID,
        subject_id=None,
        source_namespace=TAXONOMY_SOURCE_NAMESPACE,
        source_record_id=TAXONOMY_SOURCE_RECORD_ID,
        event_type="taxonomy",
        content="Retailer catalogue taxonomy import",
        observed_at=observed_at,
        metadata={"relationships": relationships_to_metadata(relationships)},
    )


def load_catalogue_relationships(data_dir: Path) -> tuple[EntityRelationshipSpec, ...]:
    catalogue = load_catalogue(data_dir)
    taxonomy = load_retailer_taxonomy(data_dir)
    return build_entity_relationships(catalogue, taxonomy)
