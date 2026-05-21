from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Room, Member
from schemas import AgentStatusOut
from websocket import manager

router = APIRouter(prefix="/api/rooms/{room_id}/agent-status", tags=["agent-status"])


@router.get("", response_model=list[AgentStatusOut])
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
