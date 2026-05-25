from datetime import datetime, timedelta, timezone

from database import get_db
from fastapi import APIRouter, Depends, HTTPException, Query
from models import Member, Room
from schemas import AgentStatusOut
from sqlalchemy.orm import Session
from websocket import manager

router = APIRouter(prefix="/api/rooms/{room_id}/agent-status", tags=["agent-status"])


@router.get("", response_model=list[AgentStatusOut])
def get_agent_status(room_id: int, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    members = db.query(Member).filter(Member.room_id == room_id, Member.type == "agent").all()
    now = datetime.now(timezone.utc)
    online_threshold = timedelta(minutes=3)

    result = []
    for m in members:
        last_active = m.last_active
        if last_active and last_active.tzinfo is None:
            last_active = last_active.replace(tzinfo=timezone.utc)
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


@router.get("/listener-count")
def get_listener_count(room_id: int, agent: str = Query(..., description="Agent name"), db: Session = Depends(get_db)):
    """返回指定 agent 在当前房间的 WS 监听器连接数。"""
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    count = manager.get_agent_connection_count(room_id, agent)
    return {"agent": agent, "room_id": room_id, "listener_count": count}
