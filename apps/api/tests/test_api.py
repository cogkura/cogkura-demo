"""API endpoint tests."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from cogkura_demo.config import get_settings
from cogkura_demo.main import DemoState, app


@pytest.fixture
async def client() -> AsyncClient:
    settings = get_settings()
    demo_state = DemoState(settings)
    app.state.demo = demo_state
    await demo_state.bootstrap()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_demo_state(client: AsyncClient) -> None:
    response = await client.get("/api/demo")
    assert response.status_code == 200
    payload = response.json()
    assert payload["customer"]["id"] == "alex"
    assert payload["history"]["events"] >= 100
    assert payload["scenario"]["suggested_prompt"]
    assert payload["ready"] is True


@pytest.mark.asyncio
async def test_chat_inspect_only_without_openai(client: AsyncClient) -> None:
    response = await client.post(
        "/api/chat",
        json={
            "message": (
                "I'm looking for a waterproof jacket for a hiking trip to Scotland "
                "next month. What would you recommend?"
            )
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "model_unavailable"
    assert payload["memory"]["estimated_tokens"] > 0
    assert payload["metrics"]["history_events"] >= 100
    assert "message" not in payload


@pytest.mark.asyncio
async def test_reset(client: AsyncClient) -> None:
    chat_before = await client.post(
        "/api/chat",
        json={"message": "Tell me about waterproof jackets."},
    )
    assert chat_before.status_code == 200
    reset = await client.post("/api/reset")
    assert reset.status_code == 200
    assert reset.json()["status"] == "reset"
    demo = await client.get("/api/demo")
    assert demo.status_code == 200
