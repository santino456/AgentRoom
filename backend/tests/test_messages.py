def _create_room_and_join(client, name="msg-room", member_name="alice"):
    """Create a room, join it, and return room_id, secret, member_token."""
    r = client.post("/api/rooms", json={"name": name})
    room_id = r.json()["id"]
    secret = r.json()["secret"]

    # Join room to get member token
    join_resp = client.post(
        f"/api/rooms/{room_id}/join",
        json={"name": member_name, "type": "agent"},
        headers={"X-Room-Secret": secret},
    )
    token = join_resp.json()["token"]
    return room_id, secret, token


def test_send_message(client):
    room_id, secret, token = _create_room_and_join(client)

    resp = client.post(
        f"/api/rooms/{room_id}/messages",
        json={"content": "hello world"},
        headers={"X-Member-Token": token},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["sender_name"] == "alice"
    assert data["content"] == "hello world"
    assert data["msg_type"] == "message"


def test_send_message_no_token(client):
    """Sending a message without auth should fail."""
    # Create room and join (sets cookies)
    room_id, secret, token = _create_room_and_join(client)

    # Create a new session without cookies to test unauthenticated access
    from fastapi.testclient import TestClient
    from main import app
    with TestClient(app) as fresh_client:
        resp = fresh_client.post(
            f"/api/rooms/{room_id}/messages",
            json={"content": "hello"},
        )
        assert resp.status_code == 401


def test_list_messages(client):
    room_id, secret, token = _create_room_and_join(client)

    client.post(
        f"/api/rooms/{room_id}/messages",
        json={"content": "msg1"},
        headers={"X-Member-Token": token},
    )
    client.post(
        f"/api/rooms/{room_id}/messages",
        json={"content": "msg2"},
        headers={"X-Member-Token": token},
    )

    resp = client.get(
        f"/api/rooms/{room_id}/messages",
        headers={"X-Member-Token": token},
    )
    assert resp.status_code == 200
    data = resp.json()
    msgs = data["messages"] if isinstance(data, dict) else data
    # Filter out system messages (join/leave)
    user_msgs = [m for m in msgs if m["msg_type"] == "message"]
    assert len(user_msgs) == 2
    assert user_msgs[0]["content"] == "msg1"
    assert user_msgs[1]["content"] == "msg2"


def test_edit_message(client):
    room_id, secret, token = _create_room_and_join(client)

    msg = client.post(
        f"/api/rooms/{room_id}/messages",
        json={"content": "original"},
        headers={"X-Member-Token": token},
    ).json()

    resp = client.put(
        f"/api/rooms/{room_id}/messages/{msg['id']}",
        json={"content": "edited"},
        headers={"X-Member-Token": token},
    )
    assert resp.status_code == 200
    assert resp.json()["content"] == "edited"


def test_delete_message(client):
    room_id, secret, token = _create_room_and_join(client)

    msg = client.post(
        f"/api/rooms/{room_id}/messages",
        json={"content": "to delete"},
        headers={"X-Member-Token": token},
    ).json()

    resp = client.delete(
        f"/api/rooms/{room_id}/messages/{msg['id']}",
        headers={"X-Member-Token": token},
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True

    # Verify deletion — only join system message should remain
    msgs_resp = client.get(
        f"/api/rooms/{room_id}/messages",
        headers={"X-Member-Token": token},
    ).json()
    msgs = msgs_resp["messages"] if isinstance(msgs_resp, dict) else msgs_resp
    user_msgs = [m for m in msgs if m["msg_type"] == "message"]
    assert len(user_msgs) == 0


def test_send_mention_message(client):
    room_id, secret, token = _create_room_and_join(client, member_name="alice")

    # Create member bob so to_name resolves
    client.post(
        f"/api/rooms/{room_id}/join",
        json={"name": "bob", "type": "agent"},
        headers={"X-Room-Secret": secret},
    )

    resp = client.post(
        f"/api/rooms/{room_id}/messages",
        json={"content": "@bob hello", "to_name": "bob"},
        headers={"X-Member-Token": token},
    )
    assert resp.status_code == 200
    assert resp.json()["to_name"] == "bob"
