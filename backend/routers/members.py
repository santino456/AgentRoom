from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Room, Member
from schemas import MemberOut

router = APIRouter(prefix="/api/rooms/{room_id}/members", tags=["members"])


def _get_room(room_id: int, db: Session) -> Room:
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@router.get("", response_model=list[MemberOut])
def list_members(room_id: int, db: Session = Depends(get_db)):
    _get_room(room_id, db)
    return db.query(Member).filter(Member.room_id == room_id).all()


@router.delete("/{member_id}")
def delete_member(room_id: int, member_id: int, db: Session = Depends(get_db)):
    _get_room(room_id, db)
    member = db.query(Member).filter(Member.id == member_id, Member.room_id == room_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    db.delete(member)
    db.commit()
    return {"ok": True}
