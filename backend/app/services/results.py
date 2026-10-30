"""History, statistics and chart data (MongoDB aggregations)."""
from datetime import timedelta

from fastapi import HTTPException

from app.services.common import utcnow

# range -> (time window, bucket unit, bucket size)
RANGES = {
    "1h": (timedelta(hours=1), "minute", 1),
    "24h": (timedelta(hours=24), "minute", 15),
    "7d": (timedelta(days=7), "hour", 1),
    "30d": (timedelta(days=30), "hour", 6),
}


def _range(name: str):
    if name not in RANGES:
        raise HTTPException(status_code=422, detail=f"range must be one of {', '.join(RANGES)}")
    return RANGES[name]


def result_out(r: dict) -> dict:
    return {
        "id": str(r["_id"]),
        "monitor_id": str(r["monitor_id"]),
        "status": r["status"],
        "http_status_code": r.get("http_status_code"),
        "response_time_ms": r.get("response_time_ms"),
        "error_message": r.get("error_message"),
        "checked_at": r["checked_at"],
    }


_UP = {"$cond": [{"$eq": ["$status", "UP"]}, 1, 0]}
_UP_RESPONSE = {"$cond": [{"$eq": ["$status", "UP"]}, "$response_time_ms", None]}  # $avg ignores null


async def history(db, monitor_id, page: int, limit: int, status: str | None, date_from, date_to):
    q: dict = {"monitor_id": monitor_id}
    if status:
        q["status"] = status
    if date_from or date_to:
        q["checked_at"] = {}
        if date_from:
            q["checked_at"]["$gte"] = date_from
        if date_to:
            q["checked_at"]["$lte"] = date_to
    total = await db.check_results.count_documents(q)
    cursor = db.check_results.find(q).sort("checked_at", -1).skip((page - 1) * limit).limit(limit)
    return {"items": [result_out(r) async for r in cursor], "total": total, "page": page, "limit": limit}


async def stats(db, monitor_ids: list, range_name: str) -> dict:
    window, _, _ = _range(range_name)
    since = utcnow() - window
    pipeline = [
        {"$match": {"monitor_id": {"$in": monitor_ids}, "checked_at": {"$gte": since}}},
        {
            "$group": {
                "_id": None,
                "total": {"$sum": 1},
                "up": {"$sum": _UP},
                "avg": {"$avg": _UP_RESPONSE},
                "min": {"$min": _UP_RESPONSE},
                "max": {"$max": _UP_RESPONSE},
            }
        },
    ]
    rows = [r async for r in await db.check_results.aggregate(pipeline)]
    r = rows[0] if rows else None
    if not r:
        return {"range": range_name, "total_checks": 0, "up_checks": 0, "uptime_percentage": None,
                "avg_response_time_ms": None, "min_response_time_ms": None, "max_response_time_ms": None}
    return {
        "range": range_name,
        "total_checks": r["total"],
        "up_checks": r["up"],
        "uptime_percentage": round(100 * r["up"] / r["total"], 2),
        "avg_response_time_ms": round(r["avg"], 1) if r["avg"] is not None else None,
        "min_response_time_ms": r["min"],
        "max_response_time_ms": r["max"],
    }


async def chart(db, monitor_ids: list, range_name: str) -> list[dict]:
    window, unit, size = _range(range_name)
    since = utcnow() - window
    pipeline = [
        {"$match": {"monitor_id": {"$in": monitor_ids}, "checked_at": {"$gte": since}}},
        {
            "$group": {
                "_id": {"$dateTrunc": {"date": "$checked_at", "unit": unit, "binSize": size}},
                "avg": {"$avg": _UP_RESPONSE},
                "up": {"$sum": _UP},
                "total": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    return [
        {
            "t": r["_id"],
            "avg_response_time_ms": round(r["avg"], 1) if r["avg"] is not None else None,
            "uptime_percentage": round(100 * r["up"] / r["total"], 2),
            "checks": r["total"],
        }
        async for r in await db.check_results.aggregate(pipeline)
    ]
