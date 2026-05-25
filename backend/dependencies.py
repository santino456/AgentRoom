from database import get_db
from fastapi import Depends, Header, HTTPException, Request
from models import Member, Room
from sqlalchemy.orm import Session


def get_room(room_id: int, db: Session) -> Room:
    """Fetch a room by ID or raise 404."""
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


def get_room_secret(x_room_secret: str = Header(default="")) -> str:
    return x_room_secret


def verify_room_secret(room_id: int, secret: str, db: Session = Depends(get_db)) -> Room:
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if room.secret and room.secret != secret:
        raise HTTPException(status_code=403, detail="Invalid room secret")
    return room


def _find_member(request: Request, x_member_token: str, room_id: int, db: Session) -> Member | None:
    """Try all auth mechanisms: user_token cookie, member_token cookie, X-Member-Token header."""
    # Try user_token cookie first (human users)
    user_token = request.cookies.get("user_token")
    if user_token:
        member = db.query(Member).filter(
            Member.room_id == room_id, Member.user_token == user_token
        ).first()
        if member:
            return member

    # Try member_token cookie (set by join.py for browser users)
    member_token_cookie = request.cookies.get("member_token")
    if member_token_cookie:
        member = db.query(Member).filter(
            Member.room_id == room_id, Member.token == member_token_cookie
        ).first()
        if member:
            return member

    # Fallback to X-Member-Token header (CLI/agents)
    if x_member_token:
        member = db.query(Member).filter(
            Member.room_id == room_id, Member.token == x_member_token
        ).first()
        if member:
            return member

    return None


def get_current_member(
    room_id: int,
    request: Request,
    x_member_token: str = Header(default=""),
    db: Session = Depends(get_db),
) -> Member:
    """Identify member via user_token cookie, member_token cookie, or member_token header."""
    member = _find_member(request, x_member_token, room_id, db)
    if member:
        return member
    raise HTTPException(status_code=401, detail="Not a room member")


def get_optional_member(
    room_id: int,
    request: Request,
    x_member_token: str = Header(default=""),
    db: Session = Depends(get_db),
) -> Member | None:
    """Optional member identification. Returns None if not authenticated."""
    return _find_member(request, x_member_token, room_id, db)
