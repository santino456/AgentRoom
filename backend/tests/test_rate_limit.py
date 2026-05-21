import time


def test_message_rate_limit(client):
    # Create a room first
    client.post("/api/rooms", json={"name": "rate-test-room"})

    # Send 30 messages quickly (should succeed)
    for i in range(30):
        resp = client.post(
            "/api/rooms/1/messages",
            json={"from_name": "tester", "content": f"msg {i}"},
            headers={"X-Room-Secret": client.get("/api/rooms").json()[0]["secret"]},
        )
        assert resp.status_code == 200, f"Message {i} failed: {resp.status_code}"

    # 31st message should be rate limited
    resp = client.post(
        "/api/rooms/1/messages",
        json={"from_name": "tester", "content": "overflow"},
        headers={"X-Room-Secret": client.get("/api/rooms").json()[0]["secret"]},
    )
    assert resp.status_code == 429
    assert "Rate limit exceeded" in resp.json()["detail"]


def test_message_rate_limit_per_user(client):
    """Rate limit should be per-user, not global."""
    client.post("/api/rooms", json={"name": "rate-test-room-2"})
    secret = client.get("/api/rooms").json()[0]["secret"]

    # tester sends 30 messages
    for i in range(30):
        client.post(
            "/api/rooms/1/messages",
            json={"from_name": "tester", "content": f"msg {i}"},
            headers={"X-Room-Secret": secret},
        )

    # other user should still be able to send
    resp = client.post(
        "/api/rooms/1/messages",
        json={"from_name": "other", "content": "ok"},
        headers={"X-Room-Secret": secret},
    )
    assert resp.status_code == 200


def test_room_creation_rate_limit(client):
    # Create 10 rooms (should succeed)
    for i in range(10):
        resp = client.post("/api/rooms", json={"name": f"room-{i}"})
        assert resp.status_code == 200, f"Room {i} failed: {resp.status_code}"

    # 11th room should be rate limited
    resp = client.post("/api/rooms", json={"name": "room-overflow"})
    assert resp.status_code == 429
    assert "Rate limit exceeded" in resp.json()["detail"]
