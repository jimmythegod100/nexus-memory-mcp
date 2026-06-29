import os

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

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
