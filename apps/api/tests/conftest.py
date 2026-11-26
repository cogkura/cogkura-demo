"""Shared safeguards for deterministic, offline demo tests."""

import pytest


@pytest.fixture(autouse=True)
def disable_configured_openai_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Do not let a developer's local .env send test requests to OpenAI."""
    monkeypatch.setenv("OPENAI_API_KEY", "")
