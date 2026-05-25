from database import get_db
from dependencies import get_current_member, get_room
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/rooms/{room_id}/invite", tags=["invites"])
@router.get("")
def generate_invite_link(
    room_id: int,
    request: Request,
    x_member_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Generate an invite link for the room. Only owner/admin can generate."""
    room = get_room(room_id, db)
    requester = get_current_member(room_id, request, x_member_token, db)

    if requester.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Only owner or admin can generate invite links")

    # Build invite URL
    base_url = str(request.base_url).rstrip("/")
    invite_url = f"{base_url}/join?room={room_id}&secret={room.secret}"

    return {
        "room_id": room_id,
        "invite_url": invite_url,
        "secret": room.secret,
    }
