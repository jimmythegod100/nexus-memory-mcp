import logging
from typing import Any, Optional
from uuid import UUID

import asyncpg

from src.models import JobResponse, QueryJobsRequest, StoreJobRequest

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        self.pool = await asyncpg.create_pool(self.dsn, min_size=1, max_size=5)

    async def disconnect(self) -> None:
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def store_job(self, req: StoreJobRequest) -> JobResponse:
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        row = await self.pool.fetchrow(
            """
            INSERT INTO jobs (agent_id, status, prompt, duration, style, format, webhook_url)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id, agent_id, status, prompt, duration, style, format,
                      video_url, error_message, retry_count, created_at, updated_at,
                      webhook_url, completed_at
            """,
            req.agent_id,
            req.status,
            req.prompt,
            req.duration,
            req.style,
            req.format,
            req.webhook_url,
        )
        return JobResponse(**dict(row))

    async def query_jobs(self, req: QueryJobsRequest) -> list[JobResponse]:
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        clauses: list[str] = []
        params: list[Any] = []
        idx = 1
        if req.agent_id:
            clauses.append(f"agent_id = ${idx}")
            params.append(req.agent_id)
            idx += 1
        if req.status:
            clauses.append(f"status = ${idx}")
            params.append(req.status)
            idx += 1
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(req.limit)
        query = f"""
            SELECT id, agent_id, status, prompt, duration, style, format,
                   video_url, error_message, retry_count, created_at, updated_at,
                   webhook_url, completed_at
            FROM jobs
            {where}
            ORDER BY created_at DESC
            LIMIT ${idx}
        """
        rows = await self.pool.fetch(query, *params)
        return [JobResponse(**dict(row)) for row in rows]

    async def ping(self) -> bool:
        if not self.pool:
            return False
        try:
            await self.pool.fetchval("SELECT 1")
            return True
        except Exception as exc:
            logger.warning("Database ping failed: %s", exc)
            return False
