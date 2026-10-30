"""Monitor CRUD and ownership rules. Every query is filtered by user_id."""
from datetime import timedelta

from fastapi import HTTPException

from app.core.config import get_settings
from app.schemas.monitor import MonitorIn
from app.security.ssrf import UnsafeURLError, assert_url_is_public
from app.services.common import to_oid, utcnow


def monitor_out(m: dict) -> dict:
    return {
        "id": str(m["_id"]),
        "user_id": str(m["user_id"]),
        "name": m["name"],
        "url": m["url"],
        "method": m["method"],
        "interval_seconds": m["interval_seconds"],
        "timeout_seconds": m["timeout_seconds"],
        "expected_status_codes": m.get("expected_status_codes", []),
        "is_active": m["is_active"],
        "last_status": m.get("last_status", "PENDING"),
        "last_checked_at": m.get("last_checked_at"),
        "last_response_time_ms": m.get("last_response_time_ms"),
        "last_http_status_code": m.get("last_http_status_code"),
        "created_at": m["created_at"],
        "updated_at": m["updated_at"],
    }


async def _validate_public(url: str) -> None:
    try:
        await assert_url_is_public(url)
    except UnsafeURLError as e:
        raise HTTPException(status_code=422, detail=str(e))


async def get_owned(db, user: dict, monitor_id: str) -> dict:
    """Return the monitor if it belongs to the user, else 404 (never 403: do not reveal existence)."""
    m = await db.monitors.find_one({"_id": to_oid(monitor_id, "Monitor"), "user_id": user["_id"]})
    if m is None:
        raise HTTPException(status_code=404, detail="Monitor not found")
    return m


async def create(db, user: dict, data: MonitorIn) -> dict:
    s = get_settings()
    if data.interval_seconds < s.min_interval_seconds:
        raise HTTPException(status_code=422, detail=f"Interval must be at least {s.min_interval_seconds} seconds")
    if await db.monitors.count_documents({"user_id": user["_id"]}) >= s.max_monitors_per_user:
        raise HTTPException(status_code=400, detail=f"You can create at most {s.max_monitors_per_user} monitors")
    await _validate_public(data.url)
    now = utcnow()
    doc = {
        "user_id": user["_id"],
        **data.model_dump(),
        "last_status": "PENDING",
        "last_checked_at": None,
        "last_response_time_ms": None,
        "last_http_status_code": None,
        "next_check_at": now,  # the worker picks it up at its next tick
        "created_at": now,
        "updated_at": now,
    }
    res = await db.monitors.insert_one(doc)
    doc["_id"] = res.inserted_id
    return doc


async def update(db, user: dict, monitor_id: str, data: MonitorIn) -> dict:
    m = await get_owned(db, user, monitor_id)
    s = get_settings()
    if data.interval_seconds < s.min_interval_seconds:
        raise HTTPException(status_code=422, detail=f"Interval must be at least {s.min_interval_seconds} seconds")
    if data.url != m["url"]:
        await _validate_public(data.url)
    now = utcnow()
    changes = {**data.model_dump(), "updated_at": now}
    if data.is_active and not m["is_active"]:
        changes["next_check_at"] = now
    await db.monitors.update_one({"_id": m["_id"]}, {"$set": changes})
    return await db.monitors.find_one({"_id": m["_id"]})


async def set_active(db, user: dict, monitor_id: str, is_active: bool) -> dict:
    m = await get_owned(db, user, monitor_id)
    now = utcnow()
    changes = {"is_active": is_active, "updated_at": now}
    if is_active:
        changes["next_check_at"] = now
    await db.monitors.update_one({"_id": m["_id"]}, {"$set": changes})
    return await db.monitors.find_one({"_id": m["_id"]})


async def delete(db, user: dict, monitor_id: str) -> None:
    m = await get_owned(db, user, monitor_id)
    await db.check_results.delete_many({"monitor_id": m["_id"]})
    await db.incidents.delete_many({"monitor_id": m["_id"]})
    await db.monitors.delete_one({"_id": m["_id"]})


async def list_page(db, user: dict, page: int, limit: int, status: str | None, search: str | None):
    import re

    q: dict = {"user_id": user["_id"]}
    if status:
        q["last_status"] = status
    if search:
        q["name"] = {"$regex": re.escape(search), "$options": "i"}
    total = await db.monitors.count_documents(q)
    cursor = db.monitors.find(q).sort("created_at", -1).skip((page - 1) * limit).limit(limit)
    items = [monitor_out(m) async for m in cursor]
    return {"items": items, "total": total, "page": page, "limit": limit}


def interval(m: dict) -> timedelta:
    return timedelta(seconds=m["interval_seconds"])
