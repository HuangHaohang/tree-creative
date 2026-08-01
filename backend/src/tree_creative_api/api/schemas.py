from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class ServiceInfo(BaseModel):
    name: str
    version: str
    environment: str


class HealthResponse(BaseModel):
    service: str
    version: str
    status: str
    dependencies: dict[str, str] = Field(default_factory=dict)
