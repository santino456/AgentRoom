from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session

from database import get_db
from models import Room, Member
from schemas import RoomCreate, RoomOut, RoomAnnouncementUpdate
from rate_limiter import limiter

router = APIRouter(prefix="/api/rooms", tags=["rooms"])


@router.get("", response_model=list[RoomOut])
def list_rooms(request: Request, db: Session = Depends(get_db)):
    """Return only rooms where the current user is a member."""
    # Try user_token cookie first
    user_token = request.cookies.get("user_token")
    if user_token:
        member_rooms = db.query(Member.room_id).filter(Member.user_token == user_token).subquery()
        return db.query(Room).filter(Room.id.in_(member_rooms)).order_by(Room.created_at.desc()).all()

    # Fallback to member_token cookie
    member_token = request.cookies.get("member_token")
    if member_token:
        member_rooms = db.query(Member.room_id).filter(Member.token == member_token).subquery()
        return db.query(Room).filter(Room.id.in_(member_rooms)).order_by(Room.created_at.desc()).all()

    return []


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

    # If creator has a user_token or member_token, auto-join them as owner
    user_token = request.cookies.get("user_token")
    member_token = request.cookies.get("member_token")
    if user_token or member_token:
        member = Member(
            room_id=db_room.id,
            name="Owner",
            type="human",
            token=member_token or "",
            user_token=user_token,
            role="owner",
        )
        db.add(member)
        db.commit()
        db.refresh(member)
        db_room.created_by_member_id = member.id
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
    from dependencies import get_current_member
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

    from dependencies import get_current_member
    requester = get_current_member(room_id, request, x_member_token, db)
    if requester.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Only owner or admin can update announcement")

    room.announcement = data.announcement
    db.commit()
    db.refresh(room)
    return room
