def _join_room(client, room_id, secret, name):
    """Join a room and return the member token."""
    resp = client.post(
        f"/api/rooms/{room_id}/join",
        json={"name": name, "type": "agent"},
        headers={"X-Room-Secret": secret},
    )
    return resp.json()["token"]


def test_message_rate_limit(client):
    # Create a room and join
    r = client.post("/api/rooms", json={"name": "rate-test-room"})
    room_id = r.json()["id"]
    secret = r.json()["secret"]
    token = _join_room(client, room_id, secret, "tester")

    # Send 30 messages quickly (should succeed)
    for i in range(30):
        resp = client.post(
            f"/api/rooms/{room_id}/messages",
            json={"content": f"msg {i}"},
            headers={"X-Member-Token": token},
        )
        assert resp.status_code == 200, f"Message {i} failed: {resp.status_code}"

    # 31st message should be rate limited
    resp = client.post(
        f"/api/rooms/{room_id}/messages",
        json={"content": "overflow"},
        headers={"X-Member-Token": token},
    )
    assert resp.status_code == 429
    assert "Rate limit exceeded" in resp.json()["detail"]


def test_message_rate_limit_per_user(client):
    """Rate limit key is per-member (msg:room_id:sender_id)."""
    r = client.post("/api/rooms", json={"name": "rate-test-room-2"})
    room_id = r.json()["id"]
    secret = r.json()["secret"]
    token = _join_room(client, room_id, secret, "tester")

    # tester sends 30 messages (all succeed)
    for i in range(30):
        resp = client.post(
            f"/api/rooms/{room_id}/messages",
            json={"content": f"msg {i}"},
            headers={"X-Member-Token": token},
        )
        assert resp.status_code == 200, f"Message {i} failed: {resp.status_code}"

    # 31st message from same user should be rate limited
    resp = client.post(
        f"/api/rooms/{room_id}/messages",
        json={"content": "overflow"},
        headers={"X-Member-Token": token},
    )
    assert resp.status_code == 429


def test_room_creation_rate_limit(client):
    # Create 10 rooms (should succeed)
    for i in range(10):
        resp = client.post("/api/rooms", json={"name": f"room-{i}"})
        assert resp.status_code == 200, f"Room {i} failed: {resp.status_code}"

    # 11th room should be rate limited
    resp = client.post("/api/rooms", json={"name": "room-overflow"})
    assert resp.status_code == 429
    assert "Rate limit exceeded" in resp.json()["detail"]
