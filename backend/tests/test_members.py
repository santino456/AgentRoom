def test_join_room(client):
    room = client.post("/api/rooms", json={"name": "member-test"}).json()
    room_id = room["id"]
    secret = room["secret"]

    resp = client.post(
        f"/api/rooms/{room_id}/join",
        json={"name": "alice", "type": "human"},
        headers={"X-Room-Secret": secret},
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_list_members(client):
    room = client.post("/api/rooms", json={"name": "member-list"}).json()
    room_id = room["id"]
    secret = room["secret"]

    client.post(
        f"/api/rooms/{room_id}/join",
        json={"name": "bob", "type": "agent"},
        headers={"X-Room-Secret": secret},
    )

    resp = client.get(f"/api/rooms/{room_id}/members")
    assert resp.status_code == 200
    members = resp.json()
    assert len(members) == 1
    assert members[0]["name"] == "bob"
    assert members[0]["type"] == "agent"


def test_join_room_invalid_secret(client):
    room = client.post("/api/rooms", json={"name": "secret-test"}).json()
    room_id = room["id"]

    resp = client.post(
        f"/api/rooms/{room_id}/join",
        json={"name": "eve", "type": "agent"},
        headers={"X-Room-Secret": "wrong-secret"},
    )
    assert resp.status_code == 403
