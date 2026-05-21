from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from websocket import manager

router = APIRouter(tags=["health"])


@router.get("/api/health")
def health(db: Session = Depends(get_db)):
    from sqlalchemy import text
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {e}"

    ws_status = "ok"
    ws_connections = {}
    try:
        for room_id, conns in manager.active_connections.items():
            ws_connections[room_id] = len(conns)
    except Exception as e:
        ws_status = f"error: {e}"

    return {
        "status": "ok" if db_status == "ok" and ws_status == "ok" else "degraded",
        "database": db_status,
        "websocket": {"status": ws_status, "connections": ws_connections},
    }
