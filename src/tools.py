from src.models import MCPToolDefinition

STORE_JOB_TOOL = MCPToolDefinition(
    name="store_job",
    description="Persist a video generation job to PostgreSQL",
    input_schema={
        "type": "object",
        "properties": {
            "agent_id": {"type": "string"},
            "prompt": {"type": "string"},
            "duration": {"type": "integer"},
            "status": {"type": "string"},
            "style": {"type": "string"},
            "format": {"type": "string"},
            "webhook_url": {"type": "string"},
        },
        "required": ["agent_id", "prompt", "duration"],
    },
    output_schema={
        "type": "object",
        "properties": {"id": {"type": "string"}, "status": {"type": "string"}},
    },
)

QUERY_JOBS_TOOL = MCPToolDefinition(
    name="query_jobs",
    description="Query jobs by agent_id and/or status",
    input_schema={
        "type": "object",
        "properties": {
            "agent_id": {"type": "string"},
            "status": {"type": "string"},
            "limit": {"type": "integer"},
        },
    },
    output_schema={"type": "object", "properties": {"jobs": {"type": "array"}}},
)

CACHE_GET_TOOL = MCPToolDefinition(
    name="cache_get",
    description="Get a value from Redis cache",
    input_schema={
        "type": "object",
        "properties": {"key": {"type": "string"}},
        "required": ["key"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "key": {"type": "string"},
            "value": {"type": "string"},
            "found": {"type": "boolean"},
        },
    },
)

CACHE_SET_TOOL = MCPToolDefinition(
    name="cache_set",
    description="Set a value in Redis cache with optional TTL",
    input_schema={
        "type": "object",
        "properties": {
            "key": {"type": "string"},
            "value": {"type": "string"},
            "ttl_seconds": {"type": "integer"},
        },
        "required": ["key", "value"],
    },
    output_schema={"type": "object", "properties": {"key": {"type": "string"}, "stored": {"type": "boolean"}}},
)

UPSERT_PLATFORM_UPLOAD_TOOL = MCPToolDefinition(
    name="upsert_platform_upload",
    description="Track per-platform upload status for a cross-post batch",
    input_schema={
        "type": "object",
        "properties": {
            "batch_id": {"type": "string"},
            "file_path": {"type": "string"},
            "platform": {"type": "string"},
            "status": {"type": "string"},
            "post_url": {"type": "string"},
            "error_message": {"type": "string"},
            "execution_node": {"type": "string"},
        },
        "required": ["batch_id", "file_path", "platform", "status"],
    },
    output_schema={"type": "object"},
)

QUERY_PLATFORM_UPLOADS_TOOL = MCPToolDefinition(
    name="query_platform_uploads",
    description="Query platform upload rows by batch, file, platform, status, or execution node",
    input_schema={
        "type": "object",
        "properties": {
            "batch_id": {"type": "string"},
            "file_path": {"type": "string"},
            "platform": {"type": "string"},
            "status": {"type": "string"},
            "execution_node": {"type": "string"},
            "limit": {"type": "integer"},
        },
    },
    output_schema={"type": "object", "properties": {"uploads": {"type": "array"}}},
)

MCP_TOOLS = [
    STORE_JOB_TOOL,
    QUERY_JOBS_TOOL,
    CACHE_GET_TOOL,
    CACHE_SET_TOOL,
    UPSERT_PLATFORM_UPLOAD_TOOL,
    QUERY_PLATFORM_UPLOADS_TOOL,
]
