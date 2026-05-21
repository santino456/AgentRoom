def test_list_rooms_empty(client):
    resp = client.get("/api/rooms")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_room(client):
    resp = client.post("/api/rooms", json={"name": "test-room"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "test-room"
    assert "id" in data
    assert "secret" in data
    assert len(data["secret"]) == 32  # 16-byte hex


def test_create_duplicate_room(client):
    client.post("/api/rooms", json={"name": "dup-room"})
    resp = client.post("/api/rooms", json={"name": "dup-room"})
    assert resp.status_code == 400
    assert "already exists" in resp.json()["detail"]


def test_list_rooms_after_create(client):
    client.post("/api/rooms", json={"name": "room-a"})
    client.post("/api/rooms", json={"name": "room-b"})
    resp = client.get("/api/rooms")
    assert resp.status_code == 200
    rooms = resp.json()
    assert len(rooms) == 2
    names = {r["name"] for r in rooms}
    assert names == {"room-a", "room-b"}
