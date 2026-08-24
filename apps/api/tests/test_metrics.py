"""Metrics tests."""

from __future__ import annotations

from cogkura_demo.config import DATA_DIR
from cogkura_demo.metrics import (
    TiktokenCounter,
    estimate_full_history_tokens,
    history_reduction_percent,
    serialize_full_history,
)
from cogkura_demo.scenarios import load_scenario_bundle


def test_full_history_serialization_stable() -> None:
    bundle = load_scenario_bundle(DATA_DIR)
    first = serialize_full_history(bundle.history)
    second = serialize_full_history(bundle.history)
    assert first == second
    counter = TiktokenCounter("gpt-4.1-mini")
    assert estimate_full_history_tokens(bundle.history, counter) > 0


def test_reduction_percent() -> None:
    assert history_reduction_percent(1000, 100) == 90.0
