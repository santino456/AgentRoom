from database import get_db
from dependencies import get_current_member, get_room
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from models import Message
from schemas import MessageOut
from sqlalchemy import text
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/rooms/{room_id}/search", tags=["search"])
@router.get("", response_model=list[MessageOut])
def search_messages(
    room_id: int,
    q: str,
    limit: int = 20,
    request: Request = None,
    x_member_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Search messages using SQLite FTS5."""
    get_room(room_id, db)
    get_current_member(room_id, request, x_member_token, db)

    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")

    # Use FTS5 to find matching message IDs
    fts_sql = text("""
        SELECT rowid FROM messages_fts
        WHERE content MATCH :query
        ORDER BY rank
        LIMIT :limit
    """)
    result = db.execute(fts_sql, {"query": q.strip(), "limit": limit})
    message_ids = [row[0] for row in result]

    if not message_ids:
        return []

    # Fetch full messages
    messages = db.query(Message).filter(
        Message.id.in_(message_ids),
        Message.room_id == room_id
    ).all()

    # Preserve FTS5 result order
    msg_map = {m.id: m for m in messages}
    ordered = [msg_map[mid] for mid in message_ids if mid in msg_map]

    # Convert to dicts (similar to messages.py _message_to_dict)
    from routers.messages import _message_to_dict
    return [_message_to_dict(m, db) for m in ordered]
