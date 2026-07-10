import logging
from typing import Any, Optional
from uuid import UUID

import asyncpg

from src.models import JobResponse, QueryJobsRequest, StoreJobRequest
from src.models import (
    PlatformUploadResponse,
    QueryPlatformUploadsRequest,
    UpsertPlatformUploadRequest,
)

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

    async def upsert_platform_upload(
        self, req: UpsertPlatformUploadRequest
    ) -> PlatformUploadResponse:
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        completed_at = "NOW()" if req.status == "completed" else "NULL"
        row = await self.pool.fetchrow(
            f"""
            INSERT INTO platform_uploads (batch_id, file_path, platform, status, post_url, error_message, execution_node, completed_at)
            VALUES ($1::uuid, $2, $3, $4, $5, $6, $7, {completed_at})
            ON CONFLICT (batch_id, platform) DO UPDATE SET
                status = EXCLUDED.status,
                post_url = COALESCE(EXCLUDED.post_url, platform_uploads.post_url),
                error_message = EXCLUDED.error_message,
                execution_node = COALESCE(EXCLUDED.execution_node, platform_uploads.execution_node),
                updated_at = NOW(),
                completed_at = CASE
                    WHEN EXCLUDED.status = 'completed' THEN NOW()
                    ELSE platform_uploads.completed_at
                END,
                retry_count = CASE
                    WHEN EXCLUDED.status = 'failed' AND platform_uploads.status = 'failed'
                    THEN platform_uploads.retry_count + 1
                    ELSE platform_uploads.retry_count
                END
            RETURNING id, batch_id, file_path, platform, status, post_url, error_message,
                      retry_count, execution_node, created_at, updated_at, completed_at
            """,
            req.batch_id,
            req.file_path,
            req.platform,
            req.status,
            req.post_url,
            req.error_message,
            req.execution_node,
        )
        return PlatformUploadResponse(**dict(row))

    async def query_platform_uploads(
        self, req: QueryPlatformUploadsRequest
    ) -> list[PlatformUploadResponse]:
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        clauses: list[str] = []
        params: list[Any] = []
        idx = 1
        if req.batch_id:
            clauses.append(f"batch_id = ${idx}::uuid")
            params.append(req.batch_id)
            idx += 1
        if req.file_path:
            clauses.append(f"file_path = ${idx}")
            params.append(req.file_path)
            idx += 1
        if req.platform:
            clauses.append(f"platform = ${idx}")
            params.append(req.platform)
            idx += 1
        if req.status:
            clauses.append(f"status = ${idx}")
            params.append(req.status)
            idx += 1
        if req.execution_node:
            clauses.append(f"execution_node = ${idx}")
            params.append(req.execution_node)
            idx += 1
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(req.limit)
        query = f"""
            SELECT id, batch_id, file_path, platform, status, post_url, error_message,
                   retry_count, execution_node, created_at, updated_at, completed_at
            FROM platform_uploads
            {where}
            ORDER BY updated_at DESC
            LIMIT ${idx}
        """
        rows = await self.pool.fetch(query, *params)
        return [PlatformUploadResponse(**dict(row)) for row in rows]

    async def ping(self) -> bool:
        if not self.pool:
            return False
        try:
            await self.pool.fetchval("SELECT 1")
            return True
        except Exception as exc:
            logger.warning("Database ping failed: %s", exc)
            return False
