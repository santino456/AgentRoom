import secrets

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["auth"])


class IdentifyRequest(BaseModel):
    name: str


@router.post("/me")
def identify(request: Request, response: Response, body: IdentifyRequest):
    """Get or create a persistent user identity. Sets user_token cookie."""
    existing = request.cookies.get("user_token")
    if existing:
        return {"user_token": existing, "name": body.name}

    user_token = secrets.token_urlsafe(24)
    response.set_cookie(key="user_token", value=user_token, max_age=31536000, path="/")
    return {"user_token": user_token, "name": body.name}
