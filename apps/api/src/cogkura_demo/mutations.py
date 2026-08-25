"""Semantic snapshot comparison and product matching."""

from __future__ import annotations

import re

from cogkura_demo.catalogue import Catalogue, Product
from cogkura_demo.models import SemanticMemorySnapshot
from cogkura_demo.session import MemoryValueChange


def compare_semantic_snapshots(
    before: list[SemanticMemorySnapshot],
    after: list[SemanticMemorySnapshot],
) -> list[MemoryValueChange]:
    before_by_predicate = _current_values(before)
    after_by_predicate = _current_values(after)
    predicates = sorted(set(before_by_predicate) | set(after_by_predicate))
    changes: list[MemoryValueChange] = []
    for predicate in predicates:
        old = before_by_predicate.get(predicate)
        new = after_by_predicate.get(predicate)
        if old != new:
            changes.append(
                MemoryValueChange(
                    predicate=predicate,
                    before=old,
                    after=new,
                )
            )
    return changes


def _current_values(snapshots: list[SemanticMemorySnapshot]) -> dict[str, str]:
    values: dict[str, str] = {}
    for item in snapshots:
        if item.status not in {"current", "active"}:
            continue
        if item.predicate and item.object_value:
            values[item.predicate] = item.object_value
    return values


def match_products_in_text(text: str, catalogue: Catalogue) -> list[str]:
    lowered = text.lower()
    matches: list[str] = []
    for product in catalogue.products:
        pattern = re.escape(product.name.lower())
        if re.search(pattern, lowered):
            matches.append(product.id)
    return matches


def find_product(catalogue: Catalogue, product_id: str) -> Product | None:
    for product in catalogue.products:
        if product.id == product_id:
            return product
    return None
