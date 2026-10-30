"""Check -> result -> incident lifecycle. HTTP is mocked; MongoDB is real (see README)."""
import httpx
import pytest

from app.monitoring import checker, worker
from tests.conftest import MONITOR


def fake_status(monkeypatch, codes: list[int]):
    """Make perform_check use a mocked transport that answers with the next status code."""
    original = checker.perform_check
    seq = iter(codes)

    async def patched(method, url, timeout, expected, client):
        code = next(seq)
        def handler(request):
            if code == 0:
                raise httpx.ConnectError("refused", request=request)
            return httpx.Response(code)
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
            return await original(method, url, timeout, expected, c)

    monkeypatch.setattr(checker, "perform_check", patched)


async def make_monitor(client, auth):
    return (await client.post("/monitors", headers=auth, json=MONITOR)).json()["id"]


async def test_up_down_up_creates_and_resolves_one_incident(client, auth, monkeypatch):
    mid = await make_monitor(client, auth)
    fake_status(monkeypatch, [200, 500, 0, 200])

    r = await client.post(f"/monitors/{mid}/check", headers=auth)
    assert r.status_code == 200 and r.json()["status"] == "UP"
    assert (await client.get("/incidents", headers=auth)).json()["total"] == 0

    assert (await client.post(f"/monitors/{mid}/check", headers=auth)).json()["status"] == "DOWN"
    assert (await client.post(f"/monitors/{mid}/check", headers=auth)).json()["status"] == "DOWN"
    incidents = (await client.get("/incidents", headers=auth)).json()
    assert incidents["total"] == 1  # still ONE incident for consecutive failures
    assert incidents["items"][0]["status"] == "OPEN"

    assert (await client.post(f"/monitors/{mid}/check", headers=auth)).json()["status"] == "UP"
    incident = (await client.get("/incidents", headers=auth)).json()["items"][0]
    assert incident["status"] == "RESOLVED" and incident["duration_seconds"] >= 0
    assert incident["resolved_at"] is not None

    mon = (await client.get(f"/monitors/{mid}", headers=auth)).json()
    assert mon["last_status"] == "UP" and mon["last_http_status_code"] == 200

    results = (await client.get(f"/monitors/{mid}/results", headers=auth)).json()
    assert results["total"] == 4
    stats = (await client.get(f"/monitors/{mid}/stats?range=24h", headers=auth)).json()
    assert stats["total_checks"] == 4 and stats["uptime_percentage"] == 50.0

    summary = (await client.get("/dashboard/summary", headers=auth)).json()
    assert summary["total_monitors"] == 1 and summary["up"] == 1 and len(summary["recent_incidents"]) == 1
    charts = (await client.get("/dashboard/charts?range=24h", headers=auth)).json()
    assert charts and charts[0]["checks"] == 4


async def test_deleting_monitor_removes_its_data(client, auth, db, monkeypatch):
    mid = await make_monitor(client, auth)
    fake_status(monkeypatch, [500])
    await client.post(f"/monitors/{mid}/check", headers=auth)
    await client.delete(f"/monitors/{mid}", headers=auth)
    assert await db.check_results.count_documents({}) == 0
    assert await db.incidents.count_documents({}) == 0


async def test_only_one_open_incident_per_monitor_is_enforced_by_index(db):
    from bson import ObjectId
    from pymongo.errors import DuplicateKeyError
    mid = ObjectId()
    await db.incidents.insert_one({"monitor_id": mid, "status": "OPEN"})
    with pytest.raises(DuplicateKeyError):
        await db.incidents.insert_one({"monitor_id": mid, "status": "OPEN"})
    await db.incidents.insert_one({"monitor_id": mid, "status": "RESOLVED"})  # resolved ones are unlimited


async def test_worker_claims_due_monitors_only_once(client, auth, db, monkeypatch):
    await make_monitor(client, auth)  # next_check_at = now -> due
    first = await worker.claim_due_monitors(db, 10)
    second = await worker.claim_due_monitors(db, 10)  # already pushed into the future
    assert len(first) == 1 and second == []


async def test_worker_tick_runs_checks_and_skips_paused(client, auth, db, monkeypatch):
    import asyncio
    mid = await make_monitor(client, auth)
    paused = (await client.post("/monitors", headers=auth, json={**MONITOR, "name": "p", "is_active": False})).json()["id"]
    fake_status(monkeypatch, [200])
    async with httpx.AsyncClient() as c:
        n = await worker.run_tick(db, c, asyncio.Semaphore(5))
    assert n == 1
    assert (await client.get(f"/monitors/{mid}", headers=auth)).json()["last_status"] == "UP"
    assert (await client.get(f"/monitors/{paused}", headers=auth)).json()["last_status"] == "PENDING"


async def test_rate_limit_headers_do_not_break_manual_check_404(client, auth):
    assert (await client.post("/monitors/000000000000000000000000/check", headers=auth)).status_code == 404
