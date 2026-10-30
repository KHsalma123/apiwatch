"""Saving check results and managing incidents.

process_result() is the heart of the system: it is called by the worker AND by the
manual check endpoint, so both behave identically.
"""
from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from app.services.common import aware, to_oid, utcnow


async def process_result(db, monitor: dict, outcome) -> dict:
    """Store the check result, refresh the monitor's latest state, open/resolve incidents."""
    now = outcome.checked_at
    result_doc = {
        "monitor_id": monitor["_id"],
        "status": outcome.status,
        "http_status_code": outcome.http_status_code,
        "response_time_ms": outcome.response_time_ms,
        "error_message": outcome.error_message,
        "checked_at": now,
    }
    await db.check_results.insert_one(result_doc)

    await db.monitors.update_one(
        {"_id": monitor["_id"]},
        {
            "$set": {
                "last_status": outcome.status,
                "last_checked_at": now,
                "last_response_time_ms": outcome.response_time_ms,
                "last_http_status_code": outcome.http_status_code,
            }
        },
    )

    if outcome.status == "DOWN":
        await _open_incident(db, monitor, outcome)
    else:
        await _resolve_incident(db, monitor, now)
    return result_doc


async def _open_incident(db, monitor: dict, outcome) -> None:
    """Create an incident unless one is already open (the unique partial index is the safety net)."""
    existing = await db.incidents.find_one({"monitor_id": monitor["_id"], "status": "OPEN"}, {"_id": 1})
    if existing:
        return
    try:
        await db.incidents.insert_one(
            {
                "monitor_id": monitor["_id"],
                "user_id": monitor["user_id"],
                "monitor_name": monitor["name"],
                "started_at": outcome.checked_at,
                "resolved_at": None,
                "duration_seconds": None,
                "status": "OPEN",
                "error_message": outcome.error_message,
                "notified_down": False,  # used by the (future) email notification phase
                "notified_recovery": False,
            }
        )
    except DuplicateKeyError:
        pass  # another process opened it at the same time: fine


async def _resolve_incident(db, monitor: dict, now) -> None:
    incident = await db.incidents.find_one({"monitor_id": monitor["_id"], "status": "OPEN"})
    if incident is None:
        return
    duration = max(0, int((aware(now) - aware(incident["started_at"])).total_seconds()))
    await db.incidents.update_one(
        {"_id": incident["_id"], "status": "OPEN"},
        {"$set": {"status": "RESOLVED", "resolved_at": now, "duration_seconds": duration}},
    )


def incident_out(i: dict) -> dict:
    return {
        "id": str(i["_id"]),
        "monitor_id": str(i["monitor_id"]),
        "monitor_name": i.get("monitor_name"),
        "started_at": i["started_at"],
        "resolved_at": i.get("resolved_at"),
        "duration_seconds": i.get("duration_seconds"),
        "status": i["status"],
        "error_message": i.get("error_message"),
    }


async def list_page(db, user: dict, page: int, limit: int, status: str | None = None, monitor_id: str | None = None):
    q: dict = {"user_id": user["_id"]}
    if status:
        q["status"] = status
    if monitor_id:
        q["monitor_id"] = to_oid(monitor_id, "Monitor")
    total = await db.incidents.count_documents(q)
    cursor = db.incidents.find(q).sort("started_at", -1).skip((page - 1) * limit).limit(limit)
    return {"items": [incident_out(i) async for i in cursor], "total": total, "page": page, "limit": limit}


async def get_owned(db, user: dict, incident_id: str) -> dict:
    i = await db.incidents.find_one({"_id": to_oid(incident_id, "Incident"), "user_id": user["_id"]})
    if i is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident_out(i)
