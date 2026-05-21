import asyncio
import json

from database import get_db
from models import WebhookConfig
from logging_config import get_logger

logger = get_logger("webhook")


async def trigger_webhooks(room_id: int, message: dict):
    """Async trigger all webhooks for a room"""
    db = None
    try:
        db = next(get_db())
        configs = db.query(WebhookConfig).filter(
            WebhookConfig.room_id == room_id,
            WebhookConfig.enabled == True
        ).all()
        if not configs:
            return
        msg_type = message.get("msg_type", "message")
        payload = json.dumps(message, ensure_ascii=False)

        import httpx
        import hmac
        import hashlib
        async with httpx.AsyncClient(timeout=10) as client:
            for cfg in configs:
                events = cfg.events.split(",")
                if msg_type not in events and "*" not in events:
                    continue
                headers = {"Content-Type": "application/json"}
                if cfg.secret:
                    sig = hmac.new(cfg.secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
                    headers["X-Webhook-Signature"] = sig
                try:
                    await client.post(cfg.url, content=payload, headers=headers)
                    logger.info(
                        "webhook_delivered",
                        room_id=room_id,
                        url=cfg.url,
                        msg_id=message.get("id"),
                    )
                except Exception as e:
                    logger.warning(
                        "webhook_failed",
                        room_id=room_id,
                        url=cfg.url,
                        error=str(e),
                        msg_id=message.get("id"),
                    )
    except Exception as e:
        logger.error("webhook_error", room_id=room_id, error=str(e))
    finally:
        if db:
            db.close()
