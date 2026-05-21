import asyncio

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from database import get_db
from models import Room, Member, Message
from schemas import MessageCreate, MessageUpdate, MessageOut, PaginatedMessages
from websocket import manager
from services.member_service import get_or_create_member
from services.webhook_service import trigger_webhooks

router = APIRouter(prefix="/api/rooms/{room_id}/messages", tags=["messages"])


def _get_room(room_id: int, db: Session) -> Room:
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


def _verify_secret(room: Room, secret: str):
    if room.secret and room.secret != secret:
        raise HTTPException(status_code=403, detail="Invalid room secret")


def _message_to_dict(m, db: Session):
    return {
        "id": m.id,
        "room_id": m.room_id,
        "sender_name": m.sender.name if m.sender else None,
        "content": m.content,
        "to_name": m.to_member_id and db.query(Member).filter(Member.id == m.to_member_id).first().name,
        "msg_type": m.msg_type,
        "created_at": m.created_at,
        "updated_at": m.updated_at,
    }


@router.get("", response_model=list[MessageOut])
def list_messages(room_id: int, limit: int = 100, offset: int = 0, db: Session = Depends(get_db)):
    _get_room(room_id, db)
    msgs = (
        db.query(Message)
        .filter(Message.room_id == room_id)
        .order_by(Message.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    result = [_message_to_dict(m, db) for m in msgs]
    return list(reversed(result))


@router.get("/paginated", response_model=PaginatedMessages)
def list_messages_paginated(room_id: int, limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    _get_room(room_id, db)
    total = db.query(Message).filter(Message.room_id == room_id).count()
    msgs = (
        db.query(Message)
        .filter(Message.room_id == room_id)
        .order_by(Message.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    result = [_message_to_dict(m, db) for m in msgs]
    return {
        "messages": list(reversed(result)),
        "total": total,
        "has_more": offset + limit < total,
    }


@router.post("", response_model=MessageOut)
async def create_message(
    room_id: int,
    msg: MessageCreate,
    x_room_secret: str = Header(default=""),
    db: Session = Depends(get_db),
):
    room = _get_room(room_id, db)
    _verify_secret(room, x_room_secret)

    sender = get_or_create_member(db, room_id, msg.from_name, "agent")

    to_member_id = None
    if msg.to_name:
        to_member = db.query(Member).filter(Member.room_id == room_id, Member.name == msg.to_name).first()
        if to_member:
            to_member_id = to_member.id

    db_msg = Message(
        room_id=room_id,
        sender_id=sender.id,
        content=msg.content,
        to_member_id=to_member_id,
        msg_type=msg.msg_type,
    )
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)

    msg_out = {
        "id": db_msg.id,
        "room_id": db_msg.room_id,
        "sender_name": sender.name,
        "content": db_msg.content,
        "to_name": msg.to_name,
        "msg_type": db_msg.msg_type,
        "created_at": db_msg.created_at.isoformat(),
        "updated_at": db_msg.updated_at.isoformat() if db_msg.updated_at else None,
    }
    await manager.broadcast(room_id, msg_out)
    asyncio.create_task(trigger_webhooks(room_id, msg_out))
    return msg_out


@router.put("/{message_id}", response_model=MessageOut)
async def update_message(
    room_id: int,
    message_id: int,
    update: MessageUpdate,
    x_room_secret: str = Header(default=""),
    db: Session = Depends(get_db),
):
    room = _get_room(room_id, db)
    _verify_secret(room, x_room_secret)

    db_msg = db.query(Message).filter(Message.id == message_id, Message.room_id == room_id).first()
    if not db_msg:
        raise HTTPException(status_code=404, detail="Message not found")

    db_msg.content = update.content
    db.commit()
    db.refresh(db_msg)

    msg_out = {
        "id": db_msg.id,
        "room_id": db_msg.room_id,
        "sender_name": db_msg.sender.name if db_msg.sender else None,
        "content": db_msg.content,
        "to_name": db_msg.to_member_id and db.query(Member).filter(Member.id == db_msg.to_member_id).first().name,
        "msg_type": db_msg.msg_type,
        "created_at": db_msg.created_at.isoformat(),
        "updated_at": db_msg.updated_at.isoformat() if db_msg.updated_at else None,
    }
    await manager.broadcast(room_id, msg_out)
    return msg_out


@router.delete("/{message_id}")
async def delete_message(
    room_id: int,
    message_id: int,
    x_room_secret: str = Header(default=""),
    db: Session = Depends(get_db),
):
    room = _get_room(room_id, db)
    _verify_secret(room, x_room_secret)

    db_msg = db.query(Message).filter(Message.id == message_id, Message.room_id == room_id).first()
    if not db_msg:
        raise HTTPException(status_code=404, detail="Message not found")

    db.delete(db_msg)
    db.commit()
    await manager.broadcast(room_id, {"type": "message_deleted", "id": message_id, "room_id": room_id})
    return {"ok": True}
