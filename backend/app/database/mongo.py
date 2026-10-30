"""MongoDB connection (PyMongo Async API) and index creation."""
from pymongo import ASCENDING, DESCENDING, AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import OperationFailure

from app.core.config import get_settings

_client: AsyncMongoClient | None = None
_db: AsyncDatabase | None = None


async def connect() -> AsyncDatabase:
    global _client, _db
    settings = get_settings()
    _client = AsyncMongoClient(settings.mongodb_uri, tz_aware=True)
    _db = _client[settings.mongodb_db]
    await ensure_indexes(_db)
    return _db


async def disconnect() -> None:
    global _client, _db
    if _client is not None:
        await _client.close()
    _client, _db = None, None


def set_db(db: AsyncDatabase | None) -> None:
    """Used by tests to inject a database."""
    global _db
    _db = db


def get_db() -> AsyncDatabase:
    """FastAPI dependency returning the active database."""
    if _db is None:
        raise RuntimeError("Database is not initialised")
    return _db


async def ensure_indexes(db: AsyncDatabase) -> None:
    settings = get_settings()
    await db.users.create_index([("email", ASCENDING)], unique=True, name="email_unique")
    await db.monitors.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)], name="user_monitors")
    await db.monitors.create_index([("is_active", ASCENDING), ("next_check_at", ASCENDING)], name="due_monitors")
    await db.check_results.create_index([("monitor_id", ASCENDING), ("checked_at", DESCENDING)], name="monitor_history")
    try:
        await db.check_results.create_index(
            [("checked_at", ASCENDING)],
            expireAfterSeconds=settings.results_retention_days * 86400,
            name="results_ttl",
        )
    except OperationFailure:
        # The TTL value changed since the index was created. Use collMod to change it.
        pass
    await db.incidents.create_index([("user_id", ASCENDING), ("started_at", DESCENDING)], name="user_incidents")
    await db.incidents.create_index([("monitor_id", ASCENDING), ("started_at", DESCENDING)], name="monitor_incidents")
    # At most ONE open incident per monitor, even if two workers race.
    await db.incidents.create_index(
        [("monitor_id", ASCENDING)],
        unique=True,
        partialFilterExpression={"status": "OPEN"},
        name="one_open_incident_per_monitor",
    )
