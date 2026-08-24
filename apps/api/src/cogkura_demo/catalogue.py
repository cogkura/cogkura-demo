"""Product catalogue loading and search."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class Product(BaseModel):
    id: str
    name: str
    category: str
    price_gbp: int
    waterproof: bool
    weight_grams: int
    colours: list[str]
    sizes: list[str]
    fit: str
    description: str


class Catalogue(BaseModel):
    products: list[Product] = Field(default_factory=list)


def load_catalogue(data_dir: Path) -> Catalogue:
    path = data_dir / "catalogue.json"
    return Catalogue.model_validate_json(path.read_text(encoding="utf-8"))


def search_products(
    catalogue: Catalogue,
    *,
    category: str | None = None,
    waterproof: bool | None = None,
    size: str | None = None,
    colours: list[str] | None = None,
    max_price_gbp: int | None = None,
) -> list[Product]:
    results: list[Product] = []
    for product in catalogue.products:
        if category is not None and product.category != category:
            continue
        if waterproof is not None and product.waterproof != waterproof:
            continue
        if size is not None and size not in product.sizes:
            continue
        if colours is not None and not any(colour in product.colours for colour in colours):
            continue
        if max_price_gbp is not None and product.price_gbp > max_price_gbp:
            continue
        results.append(product)
    return results


def waterproof_jacket_candidates(catalogue: Catalogue) -> list[Product]:
    """Broad search for demo agent: waterproof jackets only, no memory-based filters."""
    return search_products(catalogue, category="waterproof-jacket", waterproof=True)
