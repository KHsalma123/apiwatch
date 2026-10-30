from tests.conftest import register_and_login


async def test_register_login_me(client):
    r = await client.post("/auth/register", json={"name": "Bob", "email": "Bob@Example.com", "password": "longenough1"})
    assert r.status_code == 201 and r.json()["email"] == "bob@example.com"
    assert "password" not in r.text and "hashed" not in r.text
    r = await client.post("/auth/login", json={"email": "bob@example.com", "password": "longenough1"})
    assert r.status_code == 200
    me = await client.get("/users/me", headers={"Authorization": f"Bearer {r.json()['access_token']}"})
    assert me.status_code == 200 and me.json()["name"] == "Bob"


async def test_duplicate_email_409(client):
    body = {"name": "A", "email": "a@example.com", "password": "longenough1"}
    assert (await client.post("/auth/register", json=body)).status_code == 201
    assert (await client.post("/auth/register", json=body)).status_code == 409


async def test_weak_input_422(client):
    r = await client.post("/auth/register", json={"name": "A", "email": "nope", "password": "short"})
    assert r.status_code == 422


async def test_wrong_password_401(client):
    await register_and_login(client)
    r = await client.post("/auth/login", json={"email": "alice@example.com", "password": "wrong-password"})
    assert r.status_code == 401


async def test_protected_routes_require_token(client):
    for path in ("/users/me", "/monitors", "/incidents", "/dashboard/summary"):
        assert (await client.get(path)).status_code == 401
    bad = {"Authorization": "Bearer nope"}
    assert (await client.get("/monitors", headers=bad)).status_code == 401


async def test_change_password(client, auth):
    r = await client.post("/users/me/change-password", headers=auth,
                          json={"current_password": "Passw0rd!long", "new_password": "NewPassw0rd!!"})
    assert r.status_code == 204
    r = await client.post("/auth/login", json={"email": "alice@example.com", "password": "NewPassw0rd!!"})
    assert r.status_code == 200
