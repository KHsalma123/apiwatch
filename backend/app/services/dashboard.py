from app.services import incidents as incident_service
from app.services import results as result_service


async def summary(db, user: dict) -> dict:
    monitors = [m async for m in db.monitors.find({"user_id": user["_id"]})]
    active = [m for m in monitors if m["is_active"]]
    up = sum(1 for m in active if m.get("last_status") == "UP")
    down = sum(1 for m in active if m.get("last_status") == "DOWN")
    ids = [m["_id"] for m in monitors]
    stats = await result_service.stats(db, ids, "24h") if ids else {}

    recent = [
        incident_service.incident_out(i)
        async for i in db.incidents.find({"user_id": user["_id"]}).sort("started_at", -1).limit(5)
    ]
    open_incidents = await db.incidents.count_documents({"user_id": user["_id"], "status": "OPEN"})
    overview = [
        {
            "id": str(m["_id"]),
            "name": m["name"],
            "url": m["url"],
            "is_active": m["is_active"],
            "last_status": m.get("last_status", "PENDING"),
            "last_response_time_ms": m.get("last_response_time_ms"),
            "last_checked_at": m.get("last_checked_at"),
        }
        for m in sorted(monitors, key=lambda x: x["name"].lower())
    ]
    return {
        "total_monitors": len(monitors),
        "up": up,
        "down": down,
        "paused": len(monitors) - len(active),
        "pending": len(active) - up - down,
        "avg_response_time_ms": stats.get("avg_response_time_ms"),
        "uptime_percentage": stats.get("uptime_percentage"),
        "open_incidents": open_incidents,
        "recent_incidents": recent,
        "monitors": overview,
    }


async def charts(db, user: dict, range_name: str) -> list[dict]:
    ids = [m["_id"] async for m in db.monitors.find({"user_id": user["_id"]}, {"_id": 1})]
    return await result_service.chart(db, ids, range_name) if ids else []
