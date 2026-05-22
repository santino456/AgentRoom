from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session

from database import get_db
from models import Room, Member
from schemas import MemberOut, MemberStatsOut, MemberDescriptionUpdate
from dependencies import get_current_member

router = APIRouter(prefix="/api/rooms/{room_id}/members", tags=["members"])


def _get_room(room_id: int, db: Session) -> Room:
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@router.get("", response_model=list[MemberOut])
def list_members(
    room_id: int,
    request: Request,
    x_member_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    _get_room(room_id, db)
    # Verify the requester is a member
    get_current_member(room_id, request, x_member_token, db)
    return db.query(Member).filter(Member.room_id == room_id).all()


@router.delete("/{member_id}")
def delete_member(
    room_id: int,
    member_id: int,
    request: Request,
    x_member_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    _get_room(room_id, db)
    requester = get_current_member(room_id, request, x_member_token, db)
    if requester.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Only owner or admin can remove members")

    target = db.query(Member).filter(Member.id == member_id, Member.room_id == room_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Member not found")

    if target.role == "owner" and requester.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can remove another owner")

    db.delete(target)
    db.commit()
    return {"ok": True}


@router.get("/stats", response_model=list[MemberStatsOut])
def list_member_stats(
    room_id: int,
    request: Request,
    x_member_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Return message stats for each member in the room."""
    _get_room(room_id, db)
    from dependencies import get_current_member
    get_current_member(room_id, request, x_member_token, db)

    from sqlalchemy import func
    from models import Message

    stats = []
    members = db.query(Member).filter(Member.room_id == room_id).all()
    for m in members:
        msg_count = db.query(func.count(Message.id)).filter(
            Message.room_id == room_id,
            Message.sender_id == m.id,
            Message.msg_type == "message"
        ).scalar()
        last_msg = db.query(Message).filter(
            Message.room_id == room_id,
            Message.sender_id == m.id,
            Message.msg_type == "message"
        ).order_by(Message.created_at.desc()).first()
        stats.append(MemberStatsOut(
            member_id=m.id,
            name=m.name,
            type=m.type,
            role=m.role,
            description=m.description or "",
            message_count=msg_count or 0,
            last_message_at=last_msg.created_at if last_msg else None,
        ))
    return stats


@router.get("/{member_id}/description", response_model=str)
def get_member_description(
    room_id: int,
    member_id: int,
    request: Request,
    x_member_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Get a member's description."""
    _get_room(room_id, db)
    from dependencies import get_current_member
    get_current_member(room_id, request, x_member_token, db)

    member = db.query(Member).filter(Member.id == member_id, Member.room_id == room_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member.description or ""


@router.put("/{member_id}/description", response_model=MemberOut)
def update_member_description(
    room_id: int,
    member_id: int,
    data: MemberDescriptionUpdate,
    request: Request,
    x_member_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Update a member's description. Members can update their own; owners/admins can update anyone's."""
    _get_room(room_id, db)
    from dependencies import get_current_member
    requester = get_current_member(room_id, request, x_member_token, db)

    member = db.query(Member).filter(Member.id == member_id, Member.room_id == room_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Allow self-update or owner/admin update
    if requester.id != member.id and requester.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Can only update your own description")

    member.description = data.description
    db.commit()
    db.refresh(member)
    return member
