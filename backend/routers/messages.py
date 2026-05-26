import asyncio
from pathlib import Path

from database import get_db
from dependencies import get_current_member, get_room
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from logging_config import get_logger
from models import Attachment, Member, Message
from rate_limiter import limiter
from schemas import MessageCreate, MessageOut, MessageUpdate, PaginatedMessages
from services.webhook_service import trigger_webhooks
from sqlalchemy.orm import Session
from websocket import manager

router = APIRouter(prefix="/api/rooms/{room_id}/messages", tags=["messages"])
logger = get_logger("messages")
def _message_to_dict(m, db: Session):
    attachments = db.query(Attachment).filter(Attachment.message_id == m.id).all()
    # 优先使用 to_name 字段（支持多 @mention），否则回退到 to_member_id 查询
    to_name = m.to_name
    if not to_name and m.to_member_id:
        tm = db.query(Member).filter(Member.id == m.to_member_id).first()
        to_name = tm.name if tm else None
    return {
        "id": m.id,
        "room_id": m.room_id,
        "sender_name": m.sender.name if m.sender else ("system" if m.msg_type in ("join", "leave", "system") else None),
        "content": m.content,
        "to_name": to_name,
        "msg_type": m.msg_type,
        "created_at": m.created_at.isoformat() if m.created_at else None,
        "updated_at": m.updated_at.isoformat() if m.updated_at else None,
        "attachments": [
            {
                "id": a.id,
                "filename": a.filename,
                "mime_type": a.mime_type,
                "size": a.size,
                "url": f"/uploads/room_{m.room_id}/{Path(a.storage_path).name}",
            }
            for a in attachments
        ],
    }
@router.get("", response_model=list[MessageOut])
def list_messages(
    room_id: int,
    limit: int = 100,
    offset: int = 0,
    request: Request = None,
    x_member_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    get_room(room_id, db)
    # Verify membership
    get_current_member(room_id, request, x_member_token, db)

    from sqlalchemy import or_

    msgs = (
        db.query(Message)
        .filter(Message.room_id == room_id)
        .filter(
            or_(
                Message.sender_id.isnot(None),
                Message.msg_type.in_(["join", "leave", "system"]),
            )
        )
        .order_by(Message.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    result = [_message_to_dict(m, db) for m in msgs]
    return list(reversed(result))
@router.get("/paginated", response_model=PaginatedMessages)
def list_messages_paginated(
    room_id: int,
    limit: int = 50,
    offset: int = 0,
    request: Request = None,
    x_member_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    get_room(room_id, db)
    get_current_member(room_id, request, x_member_token, db)

    from sqlalchemy import or_

    total = (
        db.query(Message)
        .filter(Message.room_id == room_id)
        .filter(
            or_(
                Message.sender_id.isnot(None),
                Message.msg_type.in_(["join", "leave", "system"]),
            )
        )
        .count()
    )
    msgs = (
        db.query(Message)
        .filter(Message.room_id == room_id)
        .filter(
            or_(
                Message.sender_id.isnot(None),
                Message.msg_type.in_(["join", "leave", "system"]),
            )
        )
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
    request: Request,
    x_member_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    get_room(room_id, db)

    sender = get_current_member(room_id, request, x_member_token, db)

    if not limiter.is_allowed(f"msg:{room_id}:{sender.id}", limit=30, window_seconds=60):
        raise HTTPException(status_code=429, detail="Rate limit exceeded: 30 messages per minute")

    to_member_id = None
    to_names = [t.strip() for t in (msg.to_name or "").split(",") if t.strip()]
    if to_names:
        to_member = db.query(Member).filter(
            Member.room_id == room_id,
            Member.name.in_(to_names)
        ).first()
        if to_member:
            to_member_id = to_member.id

    db_msg = Message(
        room_id=room_id,
        sender_id=sender.id,
        content=msg.content,
        to_member_id=to_member_id,
        to_name=msg.to_name or None,
        msg_type=msg.msg_type,
    )
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)

    # Link attachments to this message
    if msg.attachment_ids:
        for att_id in msg.attachment_ids:
            att = db.query(Attachment).filter(
                Attachment.id == att_id,
                Attachment.room_id == room_id,
            ).first()
            if att:
                att.message_id = db_msg.id
        db.commit()

    msg_out = _message_to_dict(db_msg, db)
    await manager.broadcast(room_id, msg_out)
    asyncio.create_task(trigger_webhooks(room_id, msg_out))

    # Log agent mentions for observability
    content_lower = (msg.content or "").lower()
    for alias in ["@claude-agent", "@kimi-agent", "@all"]:
        if alias.lower() in content_lower:
            logger.info(
                "agent_mentioned",
                room_id=room_id,
                msg_id=db_msg.id,
                agent=alias,
                sender=sender.name,
            )
            break

    return msg_out
@router.put("/{message_id}", response_model=MessageOut)
async def update_message(
    room_id: int,
    message_id: int,
    update: MessageUpdate,
    request: Request,
    x_member_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    get_room(room_id, db)
    member = get_current_member(room_id, request, x_member_token, db)

    db_msg = db.query(Message).filter(Message.id == message_id, Message.room_id == room_id).first()
    if not db_msg:
        raise HTTPException(status_code=404, detail="Message not found")

    # Only sender or owner/admin can edit
    if db_msg.sender_id != member.id and member.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Can only edit your own messages")

    db_msg.content = update.content
    db.commit()
    db.refresh(db_msg)

    msg_out = _message_to_dict(db_msg, db)
    await manager.broadcast(room_id, msg_out)
    return msg_out
@router.delete("/{message_id}")
async def delete_message(
    room_id: int,
    message_id: int,
    request: Request,
    x_member_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    get_room(room_id, db)
    member = get_current_member(room_id, request, x_member_token, db)

    db_msg = db.query(Message).filter(Message.id == message_id, Message.room_id == room_id).first()
    if not db_msg:
        raise HTTPException(status_code=404, detail="Message not found")

    # Only sender or owner/admin can delete
    if db_msg.sender_id != member.id and member.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Can only delete your own messages")

    db.delete(db_msg)
    db.commit()
    await manager.broadcast(room_id, {"type": "message_deleted", "id": message_id, "room_id": room_id})
    return {"ok": True}
