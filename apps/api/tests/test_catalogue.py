"""Catalogue tests."""

from __future__ import annotations

from cogkura_demo.catalogue import load_catalogue, search_products, waterproof_jacket_candidates
from cogkura_demo.config import DATA_DIR


def test_catalogue_has_waterproof_jackets() -> None:
    catalogue = load_catalogue(DATA_DIR)
    jackets = waterproof_jacket_candidates(catalogue)
    assert 8 <= len(catalogue.products) <= 12
    assert len(jackets) >= 5
    ids = {product.id for product in jackets}
    assert "northpeak-alpine-shell" in ids
    assert "ridge-shell-2" in ids


def test_search_products_filters() -> None:
    catalogue = load_catalogue(DATA_DIR)
    medium = search_products(
        catalogue,
        category="waterproof-jacket",
        waterproof=True,
        size="M",
    )
    assert all("M" in product.sizes for product in medium)
