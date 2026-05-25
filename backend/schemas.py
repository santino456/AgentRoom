from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from config import settings


class RoomCreate(BaseModel):
    name: str = Field(..., max_length=settings.max_room_name_length)


class RoomOut(BaseModel):
    id: int
    name: str
    secret: str
    announcement: str = ""
    created_at: datetime

    model_config = {"from_attributes": True}


class MemberCreate(BaseModel):
    name: str = Field(..., max_length=settings.max_member_name_length)
    type: str = "agent"


class MemberOut(BaseModel):
    id: int
    name: str
    type: str
    role: str = "member"
    description: str = ""
    joined_at: datetime
    last_active: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    content: str = Field(..., max_length=settings.max_message_length)
    to_name: Optional[str] = None
    msg_type: str = "message"
    attachment_ids: Optional[list[int]] = None


class MessageUpdate(BaseModel):
    content: str = Field(..., max_length=settings.max_message_length)


class MessageOut(BaseModel):
    id: int
    room_id: int
    sender_name: Optional[str]
    content: str
    to_name: Optional[str]
    msg_type: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    attachments: list[dict] = []

    model_config = {"from_attributes": True}


class PaginatedMessages(BaseModel):
    messages: list[MessageOut]
    total: int
    has_more: bool


class WebhookCreate(BaseModel):
    url: str = Field(..., max_length=500)
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


class MemberStatsOut(BaseModel):
    member_id: int
    name: str
    type: str
    role: str
    description: str
    message_count: int
    last_message_at: Optional[datetime] = None


class MemberDescriptionUpdate(BaseModel):
    description: str = Field(..., max_length=500)



class RoomUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=settings.max_room_name_length)


class RoomAnnouncementUpdate(BaseModel):
    announcement: str = Field(..., max_length=2000)


class MemberRoleUpdate(BaseModel):
    role: str = Field(..., max_length=50)


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


class DraftOut(BaseModel):
    id: int
    room_id: int
    member_id: int
    content: str
    updated_at: datetime

    model_config = {"from_attributes": True}
