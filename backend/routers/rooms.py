from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from database import get_db
from models import Room
from schemas import RoomCreate, RoomOut
from rate_limiter import limiter

router = APIRouter(prefix="/api/rooms", tags=["rooms"])


@router.get("", response_model=list[RoomOut])
def list_rooms(db: Session = Depends(get_db)):
    return db.query(Room).order_by(Room.created_at.desc()).all()


@router.post("", response_model=RoomOut)
def create_room(
    room: RoomCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    client_ip = request.client.host if request.client else "unknown"
    if not limiter.is_allowed(f"room:create:{client_ip}", limit=10, window_seconds=3600):
        raise HTTPException(status_code=429, detail="Rate limit exceeded: 10 rooms per hour")

    existing = db.query(Room).filter(Room.name == room.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Room already exists")
    db_room = Room(name=room.name)
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room
