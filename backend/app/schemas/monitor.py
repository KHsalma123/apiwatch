from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.security.ssrf import UnsafeURLError, validate_url_syntax

Method = Literal["GET", "POST", "PUT", "DELETE"]
Status = Literal["UP", "DOWN", "PENDING"]


class MonitorIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    url: str = Field(min_length=1, max_length=2048)
    method: Method = "GET"
    interval_seconds: int = Field(default=60, ge=30, le=86400)
    timeout_seconds: int = Field(default=10, ge=1, le=30)
    expected_status_codes: list[int] = Field(default_factory=list, max_length=20)
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name must not be empty")
        return v

    @field_validator("url")
    @classmethod
    def check_url_syntax(cls, v: str) -> str:
        v = v.strip()
        try:
            validate_url_syntax(v)  # fast, no DNS. The DNS check happens in the service.
        except UnsafeURLError as e:
            raise ValueError(str(e))
        return v

    @field_validator("expected_status_codes")
    @classmethod
    def check_codes(cls, v: list[int]) -> list[int]:
        if any(c < 100 or c > 599 for c in v):
            raise ValueError("Status codes must be between 100 and 599")
        return sorted(set(v))


class ActiveIn(BaseModel):
    is_active: bool


class MonitorOut(BaseModel):
    id: str
    user_id: str
    name: str
    url: str
    method: Method
    interval_seconds: int
    timeout_seconds: int
    expected_status_codes: list[int]
    is_active: bool
    last_status: Status
    last_checked_at: datetime | None = None
    last_response_time_ms: int | None = None
    last_http_status_code: int | None = None
    created_at: datetime
    updated_at: datetime


class CheckResultOut(BaseModel):
    id: str
    monitor_id: str
    status: Literal["UP", "DOWN"]
    http_status_code: int | None = None
    response_time_ms: int | None = None
    error_message: str | None = None
    checked_at: datetime


class StatsOut(BaseModel):
    range: str
    total_checks: int
    up_checks: int
    uptime_percentage: float | None = None
    avg_response_time_ms: float | None = None
    min_response_time_ms: int | None = None
    max_response_time_ms: int | None = None


class ChartPoint(BaseModel):
    t: datetime
    avg_response_time_ms: float | None = None
    uptime_percentage: float | None = None
    checks: int


class Page(BaseModel):
    items: list
    total: int
    page: int
    limit: int
