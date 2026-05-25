from database import get_db
from dependencies import get_current_member, get_room
from fastapi import APIRouter, Depends, Header, Request
from models import DraftMessage
from pydantic import BaseModel
from schemas import DraftOut
from sqlalchemy.orm import Session


class DraftUpdate(BaseModel):
    content: str

router = APIRouter(prefix="/api/rooms/{room_id}/draft", tags=["drafts"])
@router.get("", response_model=DraftOut | None)
def get_draft(
    room_id: int,
    request: Request,
    x_member_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Get the current member's draft for this room."""
    get_room(room_id, db)
    member = get_current_member(room_id, request, x_member_token, db)
    draft = db.query(DraftMessage).filter(
        DraftMessage.room_id == room_id,
        DraftMessage.member_id == member.id
    ).first()
    return draft
@router.put("", response_model=DraftOut)
def save_draft(
    room_id: int,
    data: DraftUpdate,
    request: Request,
    x_member_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Save or update the current member's draft."""
    get_room(room_id, db)
    member = get_current_member(room_id, request, x_member_token, db)

    draft = db.query(DraftMessage).filter(
        DraftMessage.room_id == room_id,
        DraftMessage.member_id == member.id
    ).first()

    if draft:
        draft.content = data.content
    else:
        draft = DraftMessage(room_id=room_id, member_id=member.id, content=data.content)
        db.add(draft)

    db.commit()
    db.refresh(draft)
    return draft
@router.delete("")
def delete_draft(
    room_id: int,
    request: Request,
    x_member_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Delete the current member's draft."""
    get_room(room_id, db)
    member = get_current_member(room_id, request, x_member_token, db)

    draft = db.query(DraftMessage).filter(
        DraftMessage.room_id == room_id,
        DraftMessage.member_id == member.id
    ).first()

    if draft:
        db.delete(draft)
        db.commit()

    return {"ok": True}
