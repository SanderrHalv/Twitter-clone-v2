import pytest

def test_register_login_and_me(client):
    # 1) Register a new user
    resp = client.post("/accounts/", json={
        "username": "alice",
        "email": "alice@example.com",
        "password": "secret123"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "alice"
    assert "id" in data

    # 2) Login with that user
    resp = client.post("/accounts/login", json={
        "username": "alice",
        "password": "secret123"
    })
    assert resp.status_code == 200
    token = resp.json().get("access_token")
    assert token, "Expected JWT access_token in response"

    # 3) Use token to call /accounts/me
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/accounts/me", headers=headers)
    assert resp.status_code == 200
    me = resp.json()
    assert me["username"] == "alice"
    assert me["email"] == "alice@example.com"

def test_register_duplicate_user(client):
    # Register once
    client.post("/accounts/", json={
        "username": "bob",
        "email": "bob@example.com",
        "password": "pw"
    })
    # Attempt duplicate
    resp = client.post("/accounts/", json={
        "username": "bob",
        "email": "bob@example.com",
        "password": "pw2"
    })
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"].lower()

def test_login_invalid_credentials(client):
    # No such user
    resp = client.post("/accounts/login", json={
        "username": "noone",
        "password": "doesntmatter"
    })
    assert resp.status_code == 401
    assert "invalid credentials" in resp.json()["detail"].lower()
