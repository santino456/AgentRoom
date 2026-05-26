import asyncio
import json
from datetime import datetime, timezone

from database import get_db
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from logging_config import get_logger
from models import Member
from websocket import manager

router = APIRouter()
logger = get_logger("websocket")

PING_INTERVAL = 30  # seconds
PING_TIMEOUT = 10   # seconds

# 全局单连接：同一 member 同一房间只能有一个 WS 连接
_active_connections: dict[tuple[int, int], WebSocket] = {}


@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: int, token: str = ""):
    db = next(get_db())
    try:
        member = None
        # 1. Try URL token (member_token or user_token)
        if token:
            member = db.query(Member).filter(
                Member.room_id == room_id,
                (Member.token == token) | (Member.user_token == token)
            ).first()
        # 2. Try user_token cookie (global identity)
        if not member:
            user_token = websocket.cookies.get("user_token", "")
            if user_token:
                member = db.query(Member).filter(
                    Member.room_id == room_id,
                    Member.user_token == user_token
                ).first()
        # 3. Try member_token cookie (legacy)
        if not member:
            member_token = websocket.cookies.get("member_token", "")
            if member_token:
                member = db.query(Member).filter(
                    Member.room_id == room_id,
                    Member.token == member_token
                ).first()
        if not member:
            await websocket.close(code=1008, reason="Unauthorized")
            return
    finally:
        db.close()

    # 全局单连接限制：同一 member 同一房间，新连接踢掉旧连接
    conn_key = (member.id, room_id)
    if conn_key in _active_connections:
        old_ws = _active_connections[conn_key]
        try:
            await old_ws.close(code=1000, reason="Replaced by new connection")
        except Exception:
            pass
    _active_connections[conn_key] = websocket

    await manager.connect(room_id, websocket)
    last_pong = asyncio.get_event_loop().time()
    try:
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=PING_INTERVAL
                )
            except asyncio.TimeoutError:
                # Send ping and wait for pong
                now = asyncio.get_event_loop().time()
                if now - last_pong > PING_INTERVAL + PING_TIMEOUT:
                    logger.warning("websocket_ping_timeout", room_id=room_id)
                    await websocket.close(code=1000, reason="ping timeout")
                    break
                await websocket.send_text('{"type":"ping"}')
                continue

            # Client heartbeat response
            if data == "pong":
                last_pong = asyncio.get_event_loop().time()
                continue
            if data == "ping":
                await websocket.send_text('{"type":"pong"}')
                last_pong = asyncio.get_event_loop().time()
                continue

            # Agent heartbeat: update last_active + register WS connection
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
                        member.last_active = datetime.now(timezone.utc)
                        db.commit()
                    manager.register_agent(room_id, agent_name, websocket)
                    last_pong = asyncio.get_event_loop().time()
            except Exception:
                pass
            finally:
                if db:
                    db.close()
    except WebSocketDisconnect:
        pass
    finally:
        # 只有当前 websocket 仍是这个 key 的拥有者时才移除（避免旧连接关闭时误删新连接）
        if _active_connections.get(conn_key) is websocket:
            _active_connections.pop(conn_key, None)
        manager.disconnect(room_id, websocket)
