"""Boot sanity for the FastAPI app."""
from __future__ import annotations

import pytest


pytestmark = pytest.mark.asyncio


async def test_health_endpoint(api_client):
    response = await api_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_root_serves_admin_ui(api_client):
    response = await api_client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<html" in response.text.lower()


async def test_openapi_docs_available(api_client):
    response = await api_client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
