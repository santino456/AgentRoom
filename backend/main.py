import json
import os
import sys
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

# 确保 backend 目录在路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import engine, get_db
from models import Base, Room, Member, Message, MemberType, MessageType, WebhookConfig, FileLock
from websocket import manager

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Agent Coop", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ Pydantic Schemas ============

class RoomCreate(BaseModel):
    name: str


class RoomOut(BaseModel):
    id: int
    name: str
    secret: str
    created_at: datetime

    class Config:
        from_attributes = True


class MemberCreate(BaseModel):
    name: str
    type: str = "agent"


class MemberOut(BaseModel):
    id: int
    name: str
    type: str
    joined_at: datetime
    last_active: datetime

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    from_name: str
    content: str
    to_name: Optional[str] = None
    msg_type: str = "message"


class MessageUpdate(BaseModel):
    content: str


class MessageOut(BaseModel):
    id: int
    room_id: int
    sender_name: Optional[str]
    content: str
    to_name: Optional[str]
    msg_type: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaginatedMessages(BaseModel):
    messages: list[MessageOut]
    total: int
    has_more: bool


class WebhookCreate(BaseModel):
    url: str
    events: str = "message,join"
    secret: str = ""
    enabled: bool = True


class WebhookOut(BaseModel):
    id: int
    room_id: int
    url: str
    events: str
    enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Webhook Helper ============

import asyncio
import httpx

async def trigger_webhooks(room_id: int, message: dict):
    """异步触发房间的所有 webhook"""
    db = None
    try:
        db = next(get_db())
        configs = db.query(WebhookConfig).filter(
            WebhookConfig.room_id == room_id,
            WebhookConfig.enabled == True
        ).all()
        
        if not configs:
            return
        
        msg_type = message.get("msg_type", "message")
        payload = json.dumps(message, ensure_ascii=False)
        
        async with httpx.AsyncClient(timeout=10) as client:
            for cfg in configs:
                events = cfg.events.split(",")
                if msg_type not in events and "*" not in events:
                    continue
                
                headers = {"Content-Type": "application/json"}
                if cfg.secret:
                    import hmac, hashlib
                    sig = hmac.new(cfg.secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
                    headers["X-Webhook-Signature"] = sig
                
                try:
                    await client.post(cfg.url, content=payload, headers=headers)
                except Exception as e:
                    print(f"[Webhook] Failed to {cfg.url}: {e}")
    except Exception as e:
        print(f"[Webhook] Error: {e}")
    finally:
        if db:
            db.close()


# ============ Helper ============

def get_or_create_member(db: Session, room_id: int, name: str, type_: str = "agent"):
    member = db.query(Member).filter(Member.room_id == room_id, Member.name == name).first()
    if not member:
        member = Member(room_id=room_id, name=name, type=type_)
        db.add(member)
        db.commit()
        db.refresh(member)
    return member


# ============ API Routes ============

@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    from sqlalchemy import text
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {e}"

    ws_status = "ok"
    ws_connections = {}
    try:
        for room_id, conns in manager.active_connections.items():
            ws_connections[room_id] = len(conns)
    except Exception as e:
        ws_status = f"error: {e}"

    return {
        "status": "ok" if db_status == "ok" and ws_status == "ok" else "degraded",
        "database": db_status,
        "websocket": {"status": ws_status, "connections": ws_connections},
    }


@app.get("/api/rooms", response_model=list[RoomOut])
def list_rooms(db: Session = Depends(get_db)):
    return db.query(Room).order_by(Room.created_at.desc()).all()


@app.post("/api/rooms", response_model=RoomOut)
def create_room(room: RoomCreate, db: Session = Depends(get_db)):
    existing = db.query(Room).filter(Room.name == room.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Room already exists")
    db_room = Room(name=room.name)
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room


@app.get("/api/rooms/{room_id}/members", response_model=list[MemberOut])
def list_members(room_id: int, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return db.query(Member).filter(Member.room_id == room_id).all()


@app.delete("/api/rooms/{room_id}/members/{member_id}")
def delete_member(room_id: int, member_id: int, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    member = db.query(Member).filter(Member.id == member_id, Member.room_id == room_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    db.delete(member)
    db.commit()
    return {"ok": True}


@app.get("/api/rooms/{room_id}/messages", response_model=list[MessageOut])
def list_messages(room_id: int, limit: int = 100, offset: int = 0, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    msgs = (
        db.query(Message)
        .filter(Message.room_id == room_id)
        .order_by(Message.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    # 转为输出格式
    result = []
    for m in msgs:
        result.append({
            "id": m.id,
            "room_id": m.room_id,
            "sender_name": m.sender.name if m.sender else None,
            "content": m.content,
            "to_name": m.to_member_id and db.query(Member).filter(Member.id == m.to_member_id).first().name,
            "msg_type": m.msg_type,
            "created_at": m.created_at,
            "updated_at": m.updated_at,
        })
    return list(reversed(result))


@app.get("/api/rooms/{room_id}/messages/paginated", response_model=PaginatedMessages)
def list_messages_paginated(room_id: int, limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    total = db.query(Message).filter(Message.room_id == room_id).count()
    msgs = (
        db.query(Message)
        .filter(Message.room_id == room_id)
        .order_by(Message.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    result = []
    for m in msgs:
        result.append({
            "id": m.id,
            "room_id": m.room_id,
            "sender_name": m.sender.name if m.sender else None,
            "content": m.content,
            "to_name": m.to_member_id and db.query(Member).filter(Member.id == m.to_member_id).first().name,
            "msg_type": m.msg_type,
            "created_at": m.created_at,
            "updated_at": m.updated_at,
        })
    return {
        "messages": list(reversed(result)),
        "total": total,
        "has_more": offset + limit < total,
    }


@app.post("/api/rooms/{room_id}/messages", response_model=MessageOut)
async def create_message(
    room_id: int,
    msg: MessageCreate,
    x_room_secret: str = Header(default=""),
    db: Session = Depends(get_db),
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if room.secret and room.secret != x_room_secret:
        raise HTTPException(status_code=403, detail="Invalid room secret")

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

    # Broadcast via WebSocket
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
    
    # 异步触发 webhook
    asyncio.create_task(trigger_webhooks(room_id, msg_out))

    return msg_out


@app.put("/api/rooms/{room_id}/messages/{message_id}", response_model=MessageOut)
async def update_message(
    room_id: int,
    message_id: int,
    update: MessageUpdate,
    x_room_secret: str = Header(default=""),
    db: Session = Depends(get_db),
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if room.secret and room.secret != x_room_secret:
        raise HTTPException(status_code=403, detail="Invalid room secret")

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


@app.delete("/api/rooms/{room_id}/messages/{message_id}")
async def delete_message(
    room_id: int,
    message_id: int,
    x_room_secret: str = Header(default=""),
    db: Session = Depends(get_db),
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if room.secret and room.secret != x_room_secret:
        raise HTTPException(status_code=403, detail="Invalid room secret")

    db_msg = db.query(Message).filter(Message.id == message_id, Message.room_id == room_id).first()
    if not db_msg:
        raise HTTPException(status_code=404, detail="Message not found")

    db.delete(db_msg)
    db.commit()

    await manager.broadcast(room_id, {"type": "message_deleted", "id": message_id, "room_id": room_id})
    return {"ok": True}


@app.post("/api/rooms/{room_id}/join")
async def join_room(
    room_id: int,
    member: MemberCreate,
    x_room_secret: str = Header(default=""),
    db: Session = Depends(get_db),
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if room.secret and room.secret != x_room_secret:
        raise HTTPException(status_code=403, detail="Invalid room secret")

    m = get_or_create_member(db, room_id, member.name, member.type)

    # 发送系统消息
    db_msg = Message(
        room_id=room_id,
        sender_id=None,
        content=f"@{m.name} 加入了房间。",
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
    
    # 异步触发 webhook
    asyncio.create_task(trigger_webhooks(room_id, msg_out))

    return {"ok": True, "member_id": m.id}


# ============ Webhook Routes ============

@app.post("/api/rooms/{room_id}/webhooks", response_model=WebhookOut)
def create_webhook(room_id: int, cfg: WebhookCreate, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    db_cfg = WebhookConfig(
        room_id=room_id,
        url=cfg.url,
        events=cfg.events,
        secret=cfg.secret,
        enabled=cfg.enabled,
    )
    db.add(db_cfg)
    db.commit()
    db.refresh(db_cfg)
    return db_cfg


@app.get("/api/rooms/{room_id}/webhooks", response_model=list[WebhookOut])
def list_webhooks(room_id: int, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return db.query(WebhookConfig).filter(WebhookConfig.room_id == room_id).all()


@app.delete("/api/webhooks/{webhook_id}")
def delete_webhook(webhook_id: int, db: Session = Depends(get_db)):
    cfg = db.query(WebhookConfig).filter(WebhookConfig.id == webhook_id).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="Webhook not found")
    db.delete(cfg)
    db.commit()
    return {"ok": True}


# ============ WebSocket ============

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: int):
    await manager.connect(room_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # 客户端心跳
            if data == "ping":
                await websocket.send_text('{"type":"pong"}')
                continue
            # Agent 心跳：更新 last_active + 注册 WS 连接
            db = None
            try:
                payload = json.loads(data)
                if payload.get("type") == "heartbeat" and payload.get("agent"):
                    agent_name = payload["agent"]
                    db = next(get_db())
                    member = db.query(Member).filter(
                        Member.room_id == room_id,
                        Member.name == agent_name
                    ).first()
                    if member:
                        member.last_active = datetime.utcnow()
                        db.commit()
                    # 注册 agent 的 WebSocket 连接
                    manager.register_agent(room_id, agent_name, websocket)
            except Exception:
                pass
            finally:
                if db:
                    db.close()
    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)


# ============ Agent Status ============

class AgentStatusOut(BaseModel):
    name: str
    type: str
    process_online: bool
    listening: bool
    last_active: Optional[datetime] = None


@app.get("/api/rooms/{room_id}/agent-status", response_model=list[AgentStatusOut])
def get_agent_status(room_id: int, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    members = db.query(Member).filter(Member.room_id == room_id).all()
    now = datetime.utcnow()
    online_threshold = timedelta(minutes=3)

    result = []
    for m in members:
        last_active = m.last_active
        process_online = last_active is not None and (now - last_active) < online_threshold
        listening = manager.is_agent_connected(room_id, m.name)
        result.append({
            "name": m.name,
            "type": m.type,
            "process_online": process_online,
            "listening": listening,
            "last_active": last_active,
        })
    return result


# ============ File Lock API (Agent Collaboration) ============

class LockCreate(BaseModel):
    file_path: str
    agent_name: str
    ttl_seconds: int = 300


class LockOut(BaseModel):
    id: int
    room_id: int
    file_path: str
    agent_name: str
    acquired_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True


@app.post("/api/rooms/{room_id}/locks", response_model=LockOut)
def acquire_lock(room_id: int, lock: LockCreate, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # 清理过期锁
    now = datetime.utcnow()
    db.query(FileLock).filter(FileLock.expires_at < now).delete(synchronize_session=False)
    db.commit()

    # 检查是否已有活跃锁
    existing = db.query(FileLock).filter(
        FileLock.room_id == room_id,
        FileLock.file_path == lock.file_path,
        FileLock.expires_at > now
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"File locked by {existing.agent_name} until {existing.expires_at.isoformat()}"
        )

    expires = now + timedelta(seconds=lock.ttl_seconds)
    db_lock = FileLock(
        room_id=room_id,
        file_path=lock.file_path,
        agent_name=lock.agent_name,
        expires_at=expires
    )
    db.add(db_lock)
    db.commit()
    db.refresh(db_lock)
    return db_lock


@app.get("/api/rooms/{room_id}/locks", response_model=list[LockOut])
def list_locks(room_id: int, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    now = datetime.utcnow()
    # 自动清理过期锁
    db.query(FileLock).filter(FileLock.expires_at < now).delete(synchronize_session=False)
    db.commit()

    return db.query(FileLock).filter(FileLock.room_id == room_id).all()


@app.delete("/api/rooms/{room_id}/locks/{lock_id}")
def release_lock(room_id: int, lock_id: int, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    lock = db.query(FileLock).filter(FileLock.id == lock_id, FileLock.room_id == room_id).first()
    if not lock:
        raise HTTPException(status_code=404, detail="Lock not found")

    db.delete(lock)
    db.commit()
    return {"ok": True}


# ============ Static Files (Frontend) ============

FRONTEND_BUILD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")

if os.path.isdir(FRONTEND_BUILD):
    app.mount("/", StaticFiles(directory=FRONTEND_BUILD, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
