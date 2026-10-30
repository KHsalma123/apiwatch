"""Small helpers shared by services and routers."""
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def to_oid(value: str, what: str = "Resource") -> ObjectId:
    """Convert a path parameter to ObjectId. Invalid ids are reported as 404."""
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=404, detail=f"{what} not found")


def aware(dt: datetime | None) -> datetime | None:
    """MongoDB may return naive datetimes (UTC) depending on client config."""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def paginate_args(page: int, limit: int) -> tuple[int, int]:
    return (page - 1) * limit, limit
