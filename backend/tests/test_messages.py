def _create_room(client, name="msg-room"):
    r = client.post("/api/rooms", json={"name": name})
    return r.json()["id"], r.json()["secret"]


def test_send_message(client):
    room_id, secret = _create_room(client)

    resp = client.post(
        f"/api/rooms/{room_id}/messages",
        json={"from_name": "alice", "content": "hello world"},
        headers={"X-Room-Secret": secret},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["sender_name"] == "alice"
    assert data["content"] == "hello world"
    assert data["msg_type"] == "message"


def test_send_message_no_secret(client):
    room_id, _ = _create_room(client)
    resp = client.post(
        f"/api/rooms/{room_id}/messages",
        json={"from_name": "alice", "content": "hello"},
    )
    assert resp.status_code == 403


def test_list_messages(client):
    room_id, secret = _create_room(client)

    client.post(
        f"/api/rooms/{room_id}/messages",
        json={"from_name": "alice", "content": "msg1"},
        headers={"X-Room-Secret": secret},
    )
    client.post(
        f"/api/rooms/{room_id}/messages",
        json={"from_name": "bob", "content": "msg2"},
        headers={"X-Room-Secret": secret},
    )

    resp = client.get(f"/api/rooms/{room_id}/messages")
    assert resp.status_code == 200
    msgs = resp.json()
    assert len(msgs) == 2
    assert msgs[0]["content"] == "msg1"
    assert msgs[1]["content"] == "msg2"


def test_edit_message(client):
    room_id, secret = _create_room(client)

    msg = client.post(
        f"/api/rooms/{room_id}/messages",
        json={"from_name": "alice", "content": "original"},
        headers={"X-Room-Secret": secret},
    ).json()

    resp = client.put(
        f"/api/rooms/{room_id}/messages/{msg['id']}",
        json={"content": "edited"},
        headers={"X-Room-Secret": secret},
    )
    assert resp.status_code == 200
    assert resp.json()["content"] == "edited"


def test_delete_message(client):
    room_id, secret = _create_room(client)

    msg = client.post(
        f"/api/rooms/{room_id}/messages",
        json={"from_name": "alice", "content": "to delete"},
        headers={"X-Room-Secret": secret},
    ).json()

    resp = client.delete(
        f"/api/rooms/{room_id}/messages/{msg['id']}",
        headers={"X-Room-Secret": secret},
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True

    # Verify deletion
    msgs = client.get(f"/api/rooms/{room_id}/messages").json()
    assert len(msgs) == 0


def test_send_mention_message(client):
    room_id, secret = _create_room(client)

    # Create member bob so to_member_id resolves
    client.post(
        f"/api/rooms/{room_id}/join",
        json={"name": "bob", "type": "agent"},
        headers={"X-Room-Secret": secret},
    )

    resp = client.post(
        f"/api/rooms/{room_id}/messages",
        json={"from_name": "alice", "content": "@bob hello", "to_name": "bob"},
        headers={"X-Room-Secret": secret},
    )
    assert resp.status_code == 200
    assert resp.json()["to_name"] == "bob"
