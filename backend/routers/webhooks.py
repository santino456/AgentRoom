from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Room, WebhookConfig
from schemas import WebhookCreate, WebhookOut

router = APIRouter(tags=["webhooks"])


def _get_room(room_id: int, db: Session) -> Room:
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@router.post("/api/rooms/{room_id}/webhooks", response_model=WebhookOut)
def create_webhook(room_id: int, cfg: WebhookCreate, db: Session = Depends(get_db)):
    _get_room(room_id, db)
    db_cfg = WebhookConfig(
        room_id=room_id,
        url=cfg.url,
        events=cfg.events,
        secret=cfg.secret,
        enabled=cfg.enabled,
    )
    db.add(db_cfg)
    db.commit()
    db.refresh(db_cfg)
    return db_cfg


@router.get("/api/rooms/{room_id}/webhooks", response_model=list[WebhookOut])
def list_webhooks(room_id: int, db: Session = Depends(get_db)):
    _get_room(room_id, db)
    return db.query(WebhookConfig).filter(WebhookConfig.room_id == room_id).all()


@router.delete("/api/webhooks/{webhook_id}")
def delete_webhook(webhook_id: int, db: Session = Depends(get_db)):
    cfg = db.query(WebhookConfig).filter(WebhookConfig.id == webhook_id).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="Webhook not found")
    db.delete(cfg)
    db.commit()
    return {"ok": True}
