import pytest

def auth_header(client, username="user1", password="pass1"):
    # Helper to create & login a user, return auth header
    client.post("/accounts/", json={
        "username": username,
        "email": f"{username}@test.com",
        "password": password
    })
    resp = client.post("/accounts/login", json={
        "username": username,
        "password": password
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_crud_tweet_and_cache(client):
    headers = auth_header(client)

    # Create
    resp = client.post("/tweets/", json={"content": "Hello"}, headers=headers)
    assert resp.status_code == 201
    tweet = resp.json()
    tid = tweet["id"]
    assert tweet["content"] == "Hello"

    # Read (should hit cache stub)
    resp = client.get(f"/tweets/{tid}")
    assert resp.status_code == 200
    assert resp.json()["id"] == tid

    # Update
    resp = client.put(f"/tweets/{tid}", json={"content": "Updated"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["content"] == "Updated"

    # Delete
    resp = client.delete(f"/tweets/{tid}", headers=headers)
    assert resp.status_code == 204

    # Confirm 404 after delete
    resp = client.get(f"/tweets/{tid}")
    assert resp.status_code == 404

def test_list_and_search_and_like(client):
    headers = auth_header(client, "charlie", "pw")

    # Create multiple tweets
    contents = ["first", "second", "third"]
    for c in contents:
        client.post("/tweets/", json={"content": c}, headers=headers)

    # List recent (cache stub returns all)
    resp = client.get("/tweets/")
    assert resp.status_code == 200
    listed = [t["content"] for t in resp.json()]
    # Since stub prepends, order should be reverse creation
    assert listed == contents[::-1]

    # Search for "sec"
    resp = client.get("/tweets/search/?q=sec")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["content"] == "second"

    # Like a tweet
    tid = results[0]["id"]
    resp = client.post(f"/tweets/{tid}/like", headers=headers)
    assert resp.status_code == 200
    assert "queued" in resp.json()["message"].lower()

    # Immediately check that stub batcher incremented the count
    resp = client.get(f"/tweets/{tid}")
    assert resp.json()["like_count"] == 1
