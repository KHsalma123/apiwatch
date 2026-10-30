import os

# Settings must exist before the app is imported.
os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")
os.environ.setdefault("MONGODB_DB", "apiwatch_test")
os.environ.setdefault("JWT_SECRET", "test-secret-test-secret-test-secret-123")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")

import ipaddress  # noqa: E402

import httpx  # noqa: E402
import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from pymongo import AsyncMongoClient  # noqa: E402

from app.database import mongo  # noqa: E402
from app.main import app  # noqa: E402
from app.security import ssrf  # noqa: E402


@pytest.fixture(autouse=True)
def fake_dns(monkeypatch):
    """No test touches real DNS: host names resolve to a fixed public IP, 'localhost' to loopback."""

    async def _resolve(host, port):
        try:
            ipaddress.ip_address(host)
            return [host]
        except ValueError:
            pass
        if host == "private.example.com":
            return ["10.0.0.5"]
        return ["93.184.216.34"]

    monkeypatch.setattr(ssrf, "resolve_host", _resolve)


@pytest_asyncio.fixture
async def db():
    """A clean test database (needs a running MongoDB: see README)."""
    client = AsyncMongoClient(os.environ["MONGODB_URI"], tz_aware=True, serverSelectionTimeoutMS=3000)
    database = client[os.environ["MONGODB_DB"]]
    await client.drop_database(os.environ["MONGODB_DB"])
    await mongo.ensure_indexes(database)
    mongo.set_db(database)
    yield database
    await client.drop_database(os.environ["MONGODB_DB"])
    mongo.set_db(None)
    await client.close()


@pytest_asyncio.fixture
async def client(db):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test/api/v1") as c:
        yield c


async def register_and_login(client, email="alice@example.com", password="Passw0rd!long"):
    await client.post("/auth/register", json={"name": "Alice", "email": email, "password": password})
    r = await client.post("/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest_asyncio.fixture
async def auth(client):
    return await register_and_login(client)


MONITOR = {"name": "Example", "url": "https://api.example.com/health", "method": "GET"}
