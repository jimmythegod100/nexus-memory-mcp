from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class JobRecord(BaseModel):
    agent_id: str
    status: str = "pending"
    prompt: str
    duration: int
    style: Optional[str] = None
    format: Optional[str] = None
    video_url: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    webhook_url: Optional[str] = None


class JobResponse(BaseModel):
    id: UUID
    agent_id: str
    status: str
    prompt: str
    duration: int
    style: Optional[str] = None
    format: Optional[str] = None
    video_url: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    created_at: datetime
    updated_at: datetime
    webhook_url: Optional[str] = None
    completed_at: Optional[datetime] = None


class StoreJobRequest(BaseModel):
    agent_id: str
    prompt: str
    duration: int = Field(..., ge=5, le=300)
    status: str = "pending"
    style: Optional[str] = None
    format: Optional[str] = None
    webhook_url: Optional[str] = None


class QueryJobsRequest(BaseModel):
    agent_id: Optional[str] = None
    status: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100)


class CacheSetRequest(BaseModel):
    key: str = Field(..., min_length=1, max_length=512)
    value: str
    ttl_seconds: Optional[int] = Field(default=None, ge=1, le=86400)


class CacheGetResponse(BaseModel):
    key: str
    value: Optional[str] = None
    found: bool


class MCPToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]


class HealthCheckResponse(BaseModel):
    status: str
    service: str
    uptime_seconds: int
    database_connected: bool
    redis_connected: bool


class UpsertPlatformUploadRequest(BaseModel):
    batch_id: str
    file_path: str
    platform: str
    status: str
    post_url: Optional[str] = None
    error_message: Optional[str] = None
    execution_node: Optional[str] = None


class PlatformUploadResponse(BaseModel):
    id: UUID
    batch_id: UUID
    file_path: str
    platform: str
    status: str
    post_url: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    execution_node: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


class QueryPlatformUploadsRequest(BaseModel):
    batch_id: Optional[str] = None
    file_path: Optional[str] = None
    platform: Optional[str] = None
    status: Optional[str] = None
    execution_node: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=200)
