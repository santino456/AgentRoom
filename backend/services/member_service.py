from sqlalchemy.orm import Session

from models import Member


def get_or_create_member(db: Session, room_id: int, name: str, type_: str = "agent") -> Member:
    member = db.query(Member).filter(Member.room_id == room_id, Member.name == name).first()
    if not member:
        member = Member(room_id=room_id, name=name, type=type_)
        db.add(member)
        db.commit()
        db.refresh(member)
    return member
