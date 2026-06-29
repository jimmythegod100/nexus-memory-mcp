import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql://nexus_user:nexus_password@localhost:5432/nexus")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from src.database import Database
from src.models import QueryJobsRequest, StoreJobRequest
from src.redis_client import RedisCache
from src.tools import MCP_TOOLS


def _job_row():
    now = datetime.now(timezone.utc)
    return {
        "id": uuid4(),
        "agent_id": "video-generator-agent",
        "status": "pending",
        "prompt": "A cinematic mountain sunset",
        "duration": 30,
        "style": "cinematic",
        "format": "mp4",
        "video_url": None,
        "error_message": None,
        "retry_count": 0,
        "created_at": now,
        "updated_at": now,
        "webhook_url": None,
        "completed_at": None,
    }


def test_memory_mcp_tools_registered():
    names = {tool.name for tool in MCP_TOOLS}
    assert names == {"store_job", "query_jobs", "cache_get", "cache_set"}


@pytest.mark.asyncio
async def test_database_store_job():
    db = Database("postgresql://example")
    mock_pool = MagicMock()
    mock_pool.fetchrow = AsyncMock(return_value=_job_row())
    db.pool = mock_pool

    req = StoreJobRequest(
        agent_id="video-generator-agent",
        prompt="A cinematic mountain sunset",
        duration=30,
        status="pending",
    )
    result = await db.store_job(req)

    assert result.agent_id == "video-generator-agent"
    assert result.status == "pending"
    mock_pool.fetchrow.assert_awaited_once()


@pytest.mark.asyncio
async def test_database_query_jobs_with_filters():
    db = Database("postgresql://example")
    mock_pool = MagicMock()
    mock_pool.fetch = AsyncMock(return_value=[_job_row()])
    db.pool = mock_pool

    req = QueryJobsRequest(agent_id="video-generator-agent", status="pending", limit=5)
    results = await db.query_jobs(req)

    assert len(results) == 1
    assert results[0].agent_id == "video-generator-agent"
    mock_pool.fetch.assert_awaited_once()


@pytest.mark.asyncio
async def test_database_ping_success():
    db = Database("postgresql://example")
    mock_pool = MagicMock()
    mock_pool.fetchval = AsyncMock(return_value=1)
    db.pool = mock_pool
    assert await db.ping() is True


@pytest.mark.asyncio
async def test_database_ping_no_pool():
    db = Database("postgresql://example")
    assert await db.ping() is False


@pytest.mark.asyncio
async def test_redis_cache_get_and_set():
    cache = RedisCache("redis://localhost:6379/0")
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value="stored-value")
    mock_client.set = AsyncMock()
    mock_client.setex = AsyncMock()
    cache.client = mock_client

    value = await cache.get("job:123")
    assert value == "stored-value"
    assert await cache.set("job:123", "stored-value", ttl_seconds=60) is True
    mock_client.setex.assert_awaited_once()


@pytest.mark.asyncio
async def test_redis_cache_ping():
    cache = RedisCache("redis://localhost:6379/0")
    mock_client = AsyncMock()
    mock_client.ping = AsyncMock(return_value=True)
    cache.client = mock_client
    assert await cache.ping() is True


def test_store_job_endpoint(client):
    import src.main as main_module
    from src.models import JobResponse

    row = _job_row()
    main_module.db.store_job = AsyncMock(return_value=JobResponse(**row))

    response = client.post(
        "/tools/store_job",
        json={
            "agent_id": "video-generator-agent",
            "prompt": "A cinematic mountain sunset",
            "duration": 30,
        },
    )
    assert response.status_code == 200


def test_query_jobs_endpoint(client):
    import src.main as main_module

    main_module.db.query_jobs = AsyncMock(return_value=[])
    response = client.post("/tools/query_jobs", json={"agent_id": "video-generator-agent"})
    assert response.status_code == 200
    assert response.json()["jobs"] == []


def test_cache_set_endpoint(client):
    response = client.post(
        "/tools/cache_set",
        json={"key": "job:abc", "value": "pending", "ttl_seconds": 120},
    )
    assert response.status_code == 200
    assert response.json()["stored"] is True
