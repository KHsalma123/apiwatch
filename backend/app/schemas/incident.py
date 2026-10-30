from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class IncidentOut(BaseModel):
    id: str
    monitor_id: str
    monitor_name: str | None = None
    started_at: datetime
    resolved_at: datetime | None = None
    duration_seconds: int | None = None
    status: Literal["OPEN", "RESOLVED"]
    error_message: str | None = None
