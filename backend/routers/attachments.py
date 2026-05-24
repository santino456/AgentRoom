import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File, Form
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models import Room, Attachment

router = APIRouter(prefix="/api/rooms/{room_id}/attachments", tags=["attachments"])


UPLOAD_DIR = Path.home() / ".agent-coop" / "uploads"


def _get_room(room_id: int, db: Session) -> Room:
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


def _verify_secret(room: Room, secret: str):
    if room.secret and room.secret != secret:
        raise HTTPException(status_code=403, detail="Invalid room secret")


@router.post("")
async def upload_attachment(
    room_id: int,
    file: UploadFile = File(...),
    x_room_secret: str = Header(default=""),
    uploader_name: str = Form(default=""),
    db: Session = Depends(get_db),
):
    room = _get_room(room_id, db)
    _verify_secret(room, x_room_secret)

    # 读取文件内容
    contents = await file.read()
    size = len(contents)

    max_size = settings.max_attachment_size_mb * 1024 * 1024
    if size > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max {settings.max_attachment_size_mb}MB"
        )

    # 生成存储路径
    room_dir = UPLOAD_DIR / f"room_{room_id}"
    room_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix
    safe_name = f"{uuid.uuid4().hex[:12]}_{file.filename}"
    storage_path = room_dir / safe_name

    with open(storage_path, "wb") as f:
        f.write(contents)

    attachment = Attachment(
        room_id=room_id,
        filename=file.filename,
        storage_path=str(storage_path),
        mime_type=file.content_type or "application/octet-stream",
        size=size,
        uploader_name=uploader_name,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    return {
        "id": attachment.id,
        "filename": attachment.filename,
        "mime_type": attachment.mime_type,
        "size": attachment.size,
        "url": f"/uploads/room_{room_id}/{safe_name}",
    }


@router.get("")
def list_attachments(room_id: int, db: Session = Depends(get_db)):
    _get_room(room_id, db)
    attachments = db.query(Attachment).filter(Attachment.room_id == room_id).all()
    return [
        {
            "id": a.id,
            "filename": a.filename,
            "mime_type": a.mime_type,
            "size": a.size,
            "url": f"/uploads/room_{room_id}/{Path(a.storage_path).name}",
            "created_at": a.created_at,
        }
        for a in attachments
    ]
