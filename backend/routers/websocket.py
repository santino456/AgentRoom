import json
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from database import get_db
from models import Member
from websocket import manager

router = APIRouter()


@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: int):
    await manager.connect(room_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Client heartbeat
            if data == "ping":
                await websocket.send_text('{"type":"pong"}')
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
            except Exception:
                pass
            finally:
                if db:
                    db.close()
    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)
