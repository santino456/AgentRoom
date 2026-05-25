from database import get_db
from dependencies import get_current_member, get_room
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from models import Member
from schemas import MemberDescriptionUpdate, MemberOut, MemberRoleUpdate, MemberStatsOut
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/rooms/{room_id}/members", tags=["members"])
@router.get("", response_model=list[MemberOut])
def list_members(
    room_id: int,
    request: Request,
    x_member_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    get_room(room_id, db)
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
    get_room(room_id, db)
    requester = get_current_member(room_id, request, x_member_token, db)
    target = db.query(Member).filter(Member.id == member_id, Member.room_id == room_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Member not found")

    # Allow self-removal (quit room) or owner/admin removal
    if requester.id != target.id and requester.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Only owner or admin can remove members")

    # Cannot remove the last owner
    if target.role == "owner":
        owner_count = db.query(Member).filter(
            Member.room_id == room_id, Member.role == "owner"
        ).count()
        if owner_count <= 1:
            raise HTTPException(status_code=403, detail="Cannot remove the last owner")

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
    get_room(room_id, db)
    from models import Message
    from sqlalchemy import func

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
    get_room(room_id, db)
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
    get_room(room_id, db)
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
@router.put("/{member_id}/role", response_model=MemberOut)
def update_member_role(
    room_id: int,
    member_id: int,
    data: MemberRoleUpdate,
    request: Request,
    x_member_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Update a member's role. Only owner can change roles."""
    get_room(room_id, db)
    requester = get_current_member(room_id, request, x_member_token, db)

    if requester.role != "owner":
        raise HTTPException(status_code=403, detail="Only owner can change member roles")

    member = db.query(Member).filter(Member.id == member_id, Member.room_id == room_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Cannot demote the last owner
    if member.role == "owner" and data.role != "owner":
        owner_count = db.query(Member).filter(
            Member.room_id == room_id, Member.role == "owner"
        ).count()
        if owner_count <= 1:
            raise HTTPException(status_code=403, detail="Cannot demote the last owner")

    member.role = data.role
    db.commit()
    db.refresh(member)
    return member
