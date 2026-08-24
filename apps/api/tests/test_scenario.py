"""Scenario data validation tests."""

from __future__ import annotations

from cogkura_demo.config import DATA_DIR
from cogkura_demo.scenarios import event_to_observation, load_scenario_bundle, validate_history


def test_history_count_and_validation() -> None:
    bundle = load_scenario_bundle(DATA_DIR)
    validate_history(bundle)
    assert 100 <= len(bundle.history) <= 150


def test_observation_mapping_has_semantic_facts() -> None:
    bundle = load_scenario_bundle(DATA_DIR)
    size_events = [event for event in bundle.history if event.semantic_facts]
    assert size_events
    observation = event_to_observation(size_events[0])
    assert observation.tenant_id == "northstar"
    assert observation.subject_id == "alex"


def test_scenario_expected_concepts_present() -> None:
    bundle = load_scenario_bundle(DATA_DIR)
    assert "northpeak_fit_issue" in bundle.scenario.expected_concepts
    assert "jacket_size:M" in bundle.scenario.expected_concepts
