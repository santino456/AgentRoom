import asyncio
import secrets

from fastapi import APIRouter, Depends, HTTPException, Header, Request, Response
from sqlalchemy.orm import Session

from database import get_db
from models import Room, Member, Message, MessageType
from schemas import MemberCreate
from websocket import manager
from services.member_service import get_or_create_member
from services.webhook_service import trigger_webhooks

router = APIRouter(tags=["join"])


@router.post("/api/rooms/{room_id}/join")
async def join_room(
    room_id: int,
    member: MemberCreate,
    request: Request,
    response: Response,
    x_room_secret: str = Header(default=""),
    db: Session = Depends(get_db),
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    user_token = request.cookies.get("user_token")

    # Existing member by user_token — re-join without secret
    if user_token:
        existing = db.query(Member).filter(
            Member.room_id == room_id, Member.user_token == user_token
        ).first()
        if existing:
            response.set_cookie(key="member_token", value=existing.token, max_age=31536000, path="/")
            return {"ok": True, "member_id": existing.id, "token": existing.token}

    # Existing member by name — re-join without secret (backward compat)
    existing_by_name = db.query(Member).filter(
        Member.room_id == room_id, Member.name == member.name
    ).first()
    if existing_by_name:
        if user_token:
            existing_by_name.user_token = user_token
            db.commit()
        response.set_cookie(key="member_token", value=existing_by_name.token, max_age=31536000, path="/")
        return {"ok": True, "member_id": existing_by_name.id, "token": existing_by_name.token}

    # New member — require room secret
    if room.secret and room.secret != x_room_secret:
        raise HTTPException(status_code=403, detail="Invalid room secret")

    m = get_or_create_member(db, room_id, member.name, member.type)
    if user_token:
        m.user_token = user_token
        db.commit()
        db.refresh(m)

    db_msg = Message(
        room_id=room_id,
        sender_id=None,
        content=f"@{m.name} joined the room.",
        msg_type=MessageType.JOIN,
    )
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)

    msg_out = {
        "id": db_msg.id,
        "room_id": db_msg.room_id,
        "sender_name": "system",
        "content": db_msg.content,
        "to_name": None,
        "msg_type": db_msg.msg_type,
        "created_at": db_msg.created_at.isoformat(),
    }
    await manager.broadcast(room_id, msg_out)
    asyncio.create_task(trigger_webhooks(room_id, msg_out))

    response.set_cookie(key="member_token", value=m.token, max_age=31536000, path="/")
    return {"ok": True, "member_id": m.id, "token": m.token}
