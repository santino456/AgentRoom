from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Room, FileLock
from schemas import LockCreate, LockOut

router = APIRouter(prefix="/api/rooms/{room_id}/locks", tags=["locks"])


def _get_room(room_id: int, db: Session) -> Room:
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@router.post("", response_model=LockOut)
def acquire_lock(room_id: int, lock: LockCreate, db: Session = Depends(get_db)):
    _get_room(room_id, db)

    now = datetime.utcnow()
    db.query(FileLock).filter(FileLock.expires_at < now).delete(synchronize_session=False)
    db.commit()

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


@router.get("", response_model=list[LockOut])
def list_locks(room_id: int, db: Session = Depends(get_db)):
    _get_room(room_id, db)

    now = datetime.utcnow()
    db.query(FileLock).filter(FileLock.expires_at < now).delete(synchronize_session=False)
    db.commit()

    return db.query(FileLock).filter(FileLock.room_id == room_id).all()


@router.delete("/{lock_id}")
def release_lock(room_id: int, lock_id: int, db: Session = Depends(get_db)):
    _get_room(room_id, db)

    lock = db.query(FileLock).filter(FileLock.id == lock_id, FileLock.room_id == room_id).first()
    if not lock:
        raise HTTPException(status_code=404, detail="Lock not found")

    db.delete(lock)
    db.commit()
    return {"ok": True}
