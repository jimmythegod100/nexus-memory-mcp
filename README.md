# NEXUS Memory MCP Server

MCP server for PostgreSQL job persistence and Redis caching.

## Quick Start

```bash
poetry install
cp .env.example .env
# Start control plane first: cd ../nexus-control-plane && make up
poetry run nexus-memory-mcp
```

Service runs on http://localhost:8002

## MCP Tools

- **store_job** — persist job to PostgreSQL `jobs` table
- **query_jobs** — filter jobs by agent_id/status
- **cache_get** / **cache_set** — Redis key-value operations

## Endpoints

- GET /health
- GET /mcp/tools
- POST /tools/store_job
- POST /tools/query_jobs
- GET /tools/cache_get
- POST /tools/cache_set
