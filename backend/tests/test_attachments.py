import io


def _join_room(client, room_id, secret, name):
    resp = client.post(
        f"/api/rooms/{room_id}/join",
        json={"name": name, "type": "agent"},
        headers={"X-Room-Secret": secret},
    )
    return resp.json()["token"]


def test_upload_attachment(client, db_session):
    # Create a room first
    r = client.post("/api/rooms", json={"name": "test-attachments"})
    room = r.json()
    room_id = room["id"]
    secret = room["secret"]

    # Upload a file
    file_content = b"Hello, this is a test file!"
    response = client.post(
        f"/api/rooms/{room_id}/attachments",
        files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")},
        headers={"X-Room-Secret": secret},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.txt"
    assert data["mime_type"] == "text/plain"
    assert data["size"] == len(file_content)
    assert "url" in data
    assert data["url"].startswith(f"/uploads/room_{room_id}/")


def test_upload_attachment_with_uploader_name(client, db_session):
    r = client.post("/api/rooms", json={"name": "test-uploader"})
    room = r.json()
    room_id = room["id"]
    secret = room["secret"]

    response = client.post(
        f"/api/rooms/{room_id}/attachments",
        files={"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")},
        data={"uploader_name": "claude-agent"},
        headers={"X-Room-Secret": secret},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.txt"


def test_send_message_with_attachment(client, db_session):
    r = client.post("/api/rooms", json={"name": "test-msg-attach"})
    room = r.json()
    room_id = room["id"]
    secret = room["secret"]

    # Join room to get member token
    token = _join_room(client, room_id, secret, "test-agent")

    # Upload a file first
    upload = client.post(
        f"/api/rooms/{room_id}/attachments",
        files={"file": ("doc.txt", io.BytesIO(b"doc content"), "text/plain")},
        headers={"X-Room-Secret": secret},
    )
    assert upload.status_code == 200
    att = upload.json()

    # Send message with attachment using member token
    msg = client.post(
        f"/api/rooms/{room_id}/messages",
        json={"content": "see attached", "attachment_ids": [att["id"]]},
        headers={"X-Member-Token": token},
    )
    assert msg.status_code == 200
    data = msg.json()
    assert len(data["attachments"]) == 1
    assert data["attachments"][0]["filename"] == "doc.txt"


def test_upload_attachment_invalid_room(client):
    response = client.post(
        "/api/rooms/99999/attachments",
        files={"file": ("test.txt", io.BytesIO(b"test"), "text/plain")},
    )
    assert response.status_code == 404


def test_upload_attachment_invalid_secret(client, db_session):
    r = client.post("/api/rooms", json={"name": "test-secret"})
    room = r.json()
    room_id = room["id"]

    response = client.post(
        f"/api/rooms/{room_id}/attachments",
        files={"file": ("test.txt", io.BytesIO(b"test"), "text/plain")},
        headers={"X-Room-Secret": "wrong-secret"},
    )
    assert response.status_code == 403


def test_list_attachments(client, db_session):
    r = client.post("/api/rooms", json={"name": "test-list"})
    room = r.json()
    room_id = room["id"]
    secret = room["secret"]

    # Upload two files
    client.post(
        f"/api/rooms/{room_id}/attachments",
        files={"file": ("a.txt", io.BytesIO(b"a"), "text/plain")},
        headers={"X-Room-Secret": secret},
    )
    client.post(
        f"/api/rooms/{room_id}/attachments",
        files={"file": ("b.txt", io.BytesIO(b"b"), "text/plain")},
        headers={"X-Room-Secret": secret},
    )

    response = client.get(f"/api/rooms/{room_id}/attachments")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["filename"] in ("a.txt", "b.txt")
