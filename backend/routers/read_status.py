from database import get_db
from dependencies import get_current_member, get_room
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from models import Message, MessageRead
from sqlalchemy import func
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/rooms/{room_id}/messages", tags=["read-status"])
@router.post("/read")
def mark_message_read(
    room_id: int,
    message_id: int,
    request: Request,
    x_member_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Mark a message as read by the current member."""
    get_room(room_id, db)
    member = get_current_member(room_id, request, x_member_token, db)

    # Verify message exists in this room
    msg = db.query(Message).filter(Message.id == message_id, Message.room_id == room_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    # Upsert read record
    existing = db.query(MessageRead).filter(
        MessageRead.room_id == room_id,
        MessageRead.member_id == member.id,
        MessageRead.message_id == message_id
    ).first()

    if not existing:
        read_record = MessageRead(room_id=room_id, member_id=member.id, message_id=message_id)
        db.add(read_record)
        db.commit()

    return {"ok": True}
@router.get("/unread-count")
def get_unread_count(
    room_id: int,
    request: Request,
    x_member_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Get unread message count for the current member in this room."""
    get_room(room_id, db)
    member = get_current_member(room_id, request, x_member_token, db)

    total_msgs = db.query(func.count(Message.id)).filter(Message.room_id == room_id).scalar() or 0
    read_msgs = db.query(func.count(MessageRead.id)).filter(
        MessageRead.room_id == room_id,
        MessageRead.member_id == member.id
    ).scalar() or 0

    return {"unread_count": max(0, total_msgs - read_msgs)}


@router.post("/mark-all-read")
def mark_all_read(
    room_id: int,
    request: Request,
    x_member_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Mark all messages in this room as read by the current member."""
    get_room(room_id, db)
    member = get_current_member(room_id, request, x_member_token, db)

    # Get all message IDs in this room that are not yet read by this member
    read_msg_ids = db.query(MessageRead.message_id).filter(
        MessageRead.room_id == room_id,
        MessageRead.member_id == member.id,
    ).all()
    read_ids = {r[0] for r in read_msg_ids}

    all_msgs = db.query(Message.id).filter(Message.room_id == room_id).all()
    unread_ids = [m[0] for m in all_msgs if m[0] not in read_ids]

    for msg_id in unread_ids:
        db.add(MessageRead(room_id=room_id, member_id=member.id, message_id=msg_id))

    if unread_ids:
        db.commit()

    return {"ok": True, "marked_count": len(unread_ids)}
