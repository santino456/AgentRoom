from database import get_db
from dependencies import get_current_member, get_room
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from models import WebhookConfig
from schemas import WebhookCreate, WebhookOut
from sqlalchemy.orm import Session

router = APIRouter(tags=["webhooks"])

@router.post("/api/rooms/{room_id}/webhooks", response_model=WebhookOut)
def create_webhook(
    room_id: int,
    cfg: WebhookCreate,
    request: Request,
    x_member_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    get_room(room_id, db)
    get_current_member(room_id, request, x_member_token, db)
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
def list_webhooks(
    room_id: int,
    request: Request,
    x_member_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    get_room(room_id, db)
    get_current_member(room_id, request, x_member_token, db)
    return db.query(WebhookConfig).filter(WebhookConfig.room_id == room_id).all()

@router.delete("/api/webhooks/{webhook_id}")
def delete_webhook(
    webhook_id: int,
    request: Request,
    x_member_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    cfg = db.query(WebhookConfig).filter(WebhookConfig.id == webhook_id).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="Webhook not found")
    get_current_member(cfg.room_id, request, x_member_token, db)
    db.delete(cfg)
    db.commit()
    return {"ok": True}
