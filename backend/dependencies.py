from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Room


def get_room_secret(x_room_secret: str = Header(default="")) -> str:
    return x_room_secret


def verify_room_secret(room_id: int, secret: str, db: Session = Depends(get_db)) -> Room:
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if room.secret and room.secret != secret:
        raise HTTPException(status_code=403, detail="Invalid room secret")
    return room
