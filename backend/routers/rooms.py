import secrets
from urllib.parse import quote, unquote

from database import get_db
from dependencies import get_current_member
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from models import Member, Room
from rate_limiter import limiter
from schemas import RoomAnnouncementUpdate, RoomCreate, RoomOut, RoomUpdate
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/rooms", tags=["rooms"])


@router.get("", response_model=list[RoomOut])
def list_rooms(request: Request, db: Session = Depends(get_db)):
    """Return only rooms where the current user is a member."""
    from sqlalchemy import select

    # Try user_token cookie first
    user_token = request.cookies.get("user_token")
    if user_token:
        member_rooms = select(Member.room_id).where(Member.user_token == user_token).scalar_subquery()
        return db.query(Room).filter(Room.id.in_(member_rooms)).order_by(Room.created_at.desc()).all()

    # Fallback to member_token cookie
    member_token = request.cookies.get("member_token")
    if member_token:
        member_rooms = select(Member.room_id).where(Member.token == member_token).scalar_subquery()
        return db.query(Room).filter(Room.id.in_(member_rooms)).order_by(Room.created_at.desc()).all()

    return []


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

    # If creator has a user_token or member_token, auto-join them as owner
    user_token = request.cookies.get("user_token")
    member_token = request.cookies.get("member_token")
    if user_token or member_token:
        # Use member_name from cookie if available, otherwise "Owner"
        member_name = "Owner"
        raw_name = request.cookies.get("member_name")
        if raw_name:
            try:
                member_name = unquote(raw_name)
            except Exception:
                member_name = raw_name
        # Generate a fresh token for this room
        new_token = secrets.token_urlsafe(24)
        member = Member(
            room_id=db_room.id,
            name=member_name,
            type="human",
            token=new_token,
            user_token=user_token,
            role="owner",
        )
        db.add(member)
        db.commit()
        db.refresh(member)
        db_room.created_by_member_id = member.id
        db.commit()
        db.refresh(db_room)
        # Set cookies so frontend recognizes membership
        response.set_cookie(key="member_token", value=new_token, max_age=31536000, path="/")
        response.set_cookie(key="member_name", value=quote(member_name), max_age=31536000, path="/")

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
