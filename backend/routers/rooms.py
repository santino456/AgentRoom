import secrets
from urllib.parse import quote, unquote

from database import get_db

def _ensure_user_token(request, response):
    """Return existing user_token or generate a new one and set cookie."""
    user_token = request.cookies.get("user_token")
    if not user_token:
        user_token = secrets.token_urlsafe(24)
        response.set_cookie(key="user_token", value=user_token, max_age=31536000, path="/")
    return user_token
from dependencies import get_current_member
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from models import Member, Room
from rate_limiter import limiter
from schemas import RoomAnnouncementUpdate, RoomCreate, RoomOut, RoomUpdate
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/rooms", tags=["rooms"])


@router.get("", response_model=list[RoomOut])
def list_rooms(request: Request, db: Session = Depends(get_db)):
    """Return all rooms where the current user is a member (via user_token or member_token)."""
    from sqlalchemy import or_, select

    user_token = request.cookies.get("user_token")
    member_token = request.cookies.get("member_token")

    conditions = []
    if user_token:
        conditions.append(Member.user_token == user_token)
    if member_token:
        conditions.append(Member.token == member_token)

    if not conditions:
        return []

    member_rooms = select(Member.room_id).where(or_(*conditions)).scalar_subquery()
    return db.query(Room).filter(Room.id.in_(member_rooms)).order_by(Room.created_at.desc()).all()


@router.post("", response_model=RoomOut)
def create_room(
    room: RoomCreate,
    request: Request,
    response: Response,
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


@router.get("/{room_id}/announcement", response_model=str)
def get_announcement(
    room_id: int,
    request: Request,
    x_member_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Get room announcement."""
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    # Verify the requester is a member
    get_current_member(room_id, request, x_member_token, db)
    return room.announcement or ""


@router.put("/{room_id}/announcement", response_model=RoomOut)
def update_announcement(
    room_id: int,
    data: RoomAnnouncementUpdate,
    request: Request,
    x_member_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Update room announcement. Only owner/admin can edit."""
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    requester = get_current_member(room_id, request, x_member_token, db)
    if requester.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Only owner or admin can update announcement")

    room.announcement = data.announcement
    db.commit()
    db.refresh(room)
    return room


@router.get("/{room_id}", response_model=RoomOut)
def get_room(
    room_id: int,
    request: Request,
    x_member_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Get room details."""
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    get_current_member(room_id, request, x_member_token, db)
    return room


@router.delete("/{room_id}")
def delete_room(
    room_id: int,
    request: Request,
    x_member_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Delete a room. Only owner can delete."""
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    requester = get_current_member(room_id, request, x_member_token, db)
    if requester.role != "owner":
        raise HTTPException(status_code=403, detail="Only owner can delete room")

    db.delete(room)
    db.commit()
    return {"ok": True}


@router.put("/{room_id}", response_model=RoomOut)
def update_room(
    room_id: int,
    data: RoomUpdate,
    request: Request,
    x_member_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Update room name. Only owner or admin can rename."""
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    requester = get_current_member(room_id, request, x_member_token, db)
    if requester.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Only owner or admin can rename room")

    if data.name:
        existing = db.query(Room).filter(Room.name == data.name, Room.id != room_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Room name already exists")
        room.name = data.name

    db.commit()
    db.refresh(room)
    return room
