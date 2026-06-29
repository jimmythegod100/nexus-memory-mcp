import os

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

os.environ.setdefault("DATABASE_URL", "postgresql://nexus_user:nexus_password@localhost:5432/nexus")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from src.main import app


@pytest.fixture
def client():
    mock_db = MagicMock()
    mock_db.ping = AsyncMock(return_value=True)
    mock_db.connect = AsyncMock()
    mock_db.disconnect = AsyncMock()
    mock_db.store_job = AsyncMock()
    mock_db.query_jobs = AsyncMock(return_value=[])

    mock_cache = MagicMock()
    mock_cache.ping = AsyncMock(return_value=True)
    mock_cache.connect = AsyncMock()
    mock_cache.disconnect = AsyncMock()
    mock_cache.get = AsyncMock(return_value="cached-value")
    mock_cache.set = AsyncMock(return_value=True)

    with TestClient(app) as test_client:
        import src.main as main_module

        main_module.db = mock_db
        main_module.cache = mock_cache
        yield test_client


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "nexus-memory-mcp"
    assert data["status"] in ("healthy", "degraded")


def test_mcp_tools_list(client):
    response = client.get("/mcp/tools")
    assert response.status_code == 200
    names = [t["name"] for t in response.json()["tools"]]
    assert "store_job" in names
    assert "query_jobs" in names
    assert "cache_get" in names
    assert "cache_set" in names


def test_cache_get(client):
    response = client.get("/tools/cache_get?key=test-key")
    assert response.status_code == 200
    data = response.json()
    assert data["found"] is True
    assert data["value"] == "cached-value"
