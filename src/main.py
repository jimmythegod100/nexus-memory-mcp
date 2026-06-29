import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from src.config import get_settings, setup_logging
from src.database import Database
from src.models import (
    CacheGetResponse,
    CacheSetRequest,
    HealthCheckResponse,
    QueryJobsRequest,
    StoreJobRequest,
)
from src.redis_client import RedisCache
from src.tools import MCP_TOOLS

logger = logging.getLogger(__name__)
setup_logging()

db: Database | None = None
cache: RedisCache | None = None
start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global db, cache
    settings = get_settings()
    db = Database(settings.DATABASE_URL)
    cache = RedisCache(settings.REDIS_URL)
    try:
        await db.connect()
        await cache.connect()
        logger.info("nexus-memory-mcp started")
    except Exception as exc:
        logger.warning("Startup connection deferred (services may be offline): %s", exc)
    yield
    if cache:
        await cache.disconnect()
    if db:
        await db.disconnect()
    logger.info("nexus-memory-mcp shutdown")


app = FastAPI(title="NEXUS Memory MCP Server", version="0.1.0", lifespan=lifespan)


@app.post("/tools/store_job")
async def store_job(req: StoreJobRequest):
    try:
        job = await db.store_job(req)
        return job
    except Exception as e:
        logger.error("store_job failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/tools/query_jobs")
async def query_jobs(req: QueryJobsRequest):
    try:
        jobs = await db.query_jobs(req)
        return {"jobs": jobs}
    except Exception as e:
        logger.error("query_jobs failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/tools/cache_get")
async def cache_get(key: str):
    try:
        value = await cache.get(key)
        return CacheGetResponse(key=key, value=value, found=value is not None)
    except Exception as e:
        logger.error("cache_get failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/tools/cache_set")
async def cache_set(req: CacheSetRequest):
    try:
        await cache.set(req.key, req.value, req.ttl_seconds)
        return {"key": req.key, "stored": True}
    except Exception as e:
        logger.error("cache_set failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/health")
async def health_check():
    uptime = int(time.time() - start_time)
    db_ok = await db.ping() if db else False
    redis_ok = await cache.ping() if cache else False
    status = "healthy" if db_ok and redis_ok else "degraded"
    return HealthCheckResponse(
        status=status,
        service="nexus-memory-mcp",
        uptime_seconds=uptime,
        database_connected=db_ok,
        redis_connected=redis_ok,
    )


@app.get("/mcp/tools")
async def list_mcp_tools():
    return {"tools": [tool.model_dump() for tool in MCP_TOOLS]}


@app.get("/")
async def root():
    return {
        "service": "nexus-memory-mcp",
        "version": "0.1.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "tools": "/mcp/tools",
            "store_job": "/tools/store_job",
            "query_jobs": "/tools/query_jobs",
            "cache_get": "/tools/cache_get",
            "cache_set": "/tools/cache_set",
        },
    }


def run() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    run()
