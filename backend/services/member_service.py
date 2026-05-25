import secrets

from models import Member
from sqlalchemy.orm import Session


def get_or_create_member(db: Session, room_id: int, name: str, type_: str = "agent", role: str = None) -> Member:
    member = db.query(Member).filter(Member.room_id == room_id, Member.name == name).first()
    if not member:
        # First member in the room becomes owner by default
        existing_count = db.query(Member).filter(Member.room_id == room_id).count()
        if role is None:
            role = "owner" if existing_count == 0 else "member"
        member = Member(room_id=room_id, name=name, type=type_, token=secrets.token_urlsafe(24), role=role)
        db.add(member)
        db.commit()
        db.refresh(member)
    if not member.token:
        member.token = secrets.token_urlsafe(24)
        db.commit()
        db.refresh(member)
    return member
