from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RoomCreate(BaseModel):
    name: str


class RoomOut(BaseModel):
    id: int
    name: str
    secret: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MemberCreate(BaseModel):
    name: str
    type: str = "agent"


class MemberOut(BaseModel):
    id: int
    name: str
    type: str
    joined_at: datetime
    last_active: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    from_name: str
    content: str
    to_name: Optional[str] = None
    msg_type: str = "message"


class MessageUpdate(BaseModel):
    content: str


class MessageOut(BaseModel):
    id: int
    room_id: int
    sender_name: Optional[str]
    content: str
    to_name: Optional[str]
    msg_type: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PaginatedMessages(BaseModel):
    messages: list[MessageOut]
    total: int
    has_more: bool


class WebhookCreate(BaseModel):
    url: str
    events: str = "message,join"
    secret: str = ""
    enabled: bool = True


class WebhookOut(BaseModel):
    id: int
    room_id: int
    url: str
    events: str
    enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentStatusOut(BaseModel):
    name: str
    type: str
    process_online: bool
    listening: bool
    last_active: Optional[datetime] = None


class LockCreate(BaseModel):
    file_path: str
    agent_name: str
    ttl_seconds: int = 300


class LockOut(BaseModel):
    id: int
    room_id: int
    file_path: str
    agent_name: str
    acquired_at: datetime
    expires_at: datetime

    model_config = {"from_attributes": True}
