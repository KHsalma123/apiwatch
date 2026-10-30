import pytest

from tests.conftest import MONITOR, register_and_login


async def test_crud_flow(client, auth):
    r = await client.post("/monitors", headers=auth, json=MONITOR)
    assert r.status_code == 201
    m = r.json()
    assert m["last_status"] == "PENDING" and m["interval_seconds"] == 60 and m["is_active"]

    r = await client.put(f"/monitors/{m['id']}", headers=auth, json={**MONITOR, "name": "Renamed", "interval_seconds": 120})
    assert r.status_code == 200 and r.json()["name"] == "Renamed"

    r = await client.patch(f"/monitors/{m['id']}/active", headers=auth, json={"is_active": False})
    assert r.json()["is_active"] is False

    listing = (await client.get("/monitors", headers=auth)).json()
    assert listing["total"] == 1 and listing["items"][0]["name"] == "Renamed"

    assert (await client.delete(f"/monitors/{m['id']}", headers=auth)).status_code == 204
    assert (await client.get(f"/monitors/{m['id']}", headers=auth)).status_code == 404


@pytest.mark.parametrize("url", [
    "http://localhost/", "http://127.0.0.1/", "http://169.254.169.254/", "ftp://example.com/",
    "http://10.0.0.1/", "https://private.example.com/",
])
async def test_ssrf_urls_rejected_on_create(client, auth, url):
    r = await client.post("/monitors", headers=auth, json={**MONITOR, "url": url})
    assert r.status_code == 422


async def test_validation_errors(client, auth):
    assert (await client.post("/monitors", headers=auth, json={**MONITOR, "method": "TRACE"})).status_code == 422
    assert (await client.post("/monitors", headers=auth, json={**MONITOR, "interval_seconds": 5})).status_code == 422
    assert (await client.post("/monitors", headers=auth, json={**MONITOR, "expected_status_codes": [999]})).status_code == 422
    assert (await client.post("/monitors", headers=auth, json={**MONITOR, "name": "  "})).status_code == 422


async def test_user_cannot_access_other_users_monitor(client, auth):
    m = (await client.post("/monitors", headers=auth, json=MONITOR)).json()
    other = await register_and_login(client, email="mallory@example.com")
    for method, path, kwargs in [
        ("get", f"/monitors/{m['id']}", {}),
        ("put", f"/monitors/{m['id']}", {"json": MONITOR}),
        ("patch", f"/monitors/{m['id']}/active", {"json": {"is_active": False}}),
        ("delete", f"/monitors/{m['id']}", {}),
        ("post", f"/monitors/{m['id']}/check", {}),
        ("get", f"/monitors/{m['id']}/results", {}),
        ("get", f"/monitors/{m['id']}/stats", {}),
    ]:
        r = await getattr(client, method)(path, headers=other, **kwargs)
        assert r.status_code == 404, (method, path)
    assert (await client.get("/monitors", headers=other)).json()["total"] == 0
    assert (await client.get(f"/monitors/{m['id']}", headers=auth)).status_code == 200


async def test_invalid_id_is_404(client, auth):
    assert (await client.get("/monitors/not-an-id", headers=auth)).status_code == 404


async def test_monitor_limit(client, auth, monkeypatch):
    from app.core.config import get_settings
    monkeypatch.setattr(get_settings(), "max_monitors_per_user", 2)
    for i in range(2):
        assert (await client.post("/monitors", headers=auth, json={**MONITOR, "name": f"m{i}"})).status_code == 201
    assert (await client.post("/monitors", headers=auth, json=MONITOR)).status_code == 400
