import json
import asyncio
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from database import get_db
from models import Member
from websocket import manager
from logging_config import get_logger

router = APIRouter()
logger = get_logger("websocket")

PING_INTERVAL = 30  # seconds
PING_TIMEOUT = 10   # seconds


@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: int):
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
                        member.last_active = datetime.utcnow()
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
        manager.disconnect(room_id, websocket)
