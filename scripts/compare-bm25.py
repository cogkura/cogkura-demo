#!/usr/bin/env python3
"""Model-free BM25 sensitivity check for the jacket comparison scenario."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "api" / "src"))

from cogkura_demo.catalogue import load_catalogue
from cogkura_demo.config import DATA_DIR, DEMO_AS_OF, get_settings
from cogkura_demo.context_strategies.base import ComparisonSnapshot
from cogkura_demo.context_strategies.bm25 import Bm25SearchStrategy
from cogkura_demo.evaluation import ComparisonEvaluator, load_comparison_config
from cogkura_demo.metrics import TiktokenCounter
from cogkura_demo.scenarios import load_scenario_bundle

JACKET_PROMPT = (
    "I'm looking for a waterproof jacket for a hiking trip to Scotland "
    "next month. What would you recommend?"
)


async def run_cap(*, cap: int) -> None:
    settings = get_settings()
    bundle = load_scenario_bundle(DATA_DIR)
    counter = TiktokenCounter(settings.openai_model)
    strategy = Bm25SearchStrategy(
        token_counter=counter,
        catalogue=load_catalogue(DATA_DIR),
        budget_tokens=settings.search_context_budget_tokens,
        max_events=cap,
    )
    snapshot = ComparisonSnapshot(
        snapshot_id=f"bm25-cap-{cap}",
        as_of=DEMO_AS_OF,
        history=tuple(bundle.history),
        history_version=0,
    )
    prepared = await strategy.prepare(
        message=JACKET_PROMPT,
        goal=bundle.scenario.goal,
        snapshot=snapshot,
    )
    relevance = ComparisonEvaluator(load_comparison_config(DATA_DIR)).evaluate(
        prepared,
        snapshot.history,
    )
    print(
        f"{cap:>4}  "
        f"{prepared.estimated_tokens:>5}  "
        f"{relevance.expected_concepts_found}/{relevance.expected_concepts_total}  "
        f"{relevance.excluded_concepts_present:>6}  "
        f"{relevance.stale_units:>5}  "
        f"{relevance.unclassified_units:>5}"
    )


async def main() -> None:
    print("cap   tokens   coverage   stale concepts   stale units   unclassified")
    for cap in (20, 50, 100):
        await run_cap(cap=cap)


if __name__ == "__main__":
    asyncio.run(main())
