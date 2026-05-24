from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
import enum
import secrets


class MemberType(str, enum.Enum):
    HUMAN = "human"
    AGENT = "agent"


class MessageType(str, enum.Enum):
    MESSAGE = "message"
    JOIN = "join"
    LEAVE = "leave"
    SYSTEM = "system"


def generate_room_secret():
    return secrets.token_hex(16)


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    secret = Column(String, default=generate_room_secret, nullable=False)
    created_by_member_id = Column(Integer, ForeignKey("members.id"), nullable=True)
    announcement = Column(Text, default="", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship("Member", foreign_keys="Member.room_id", back_populates="room", cascade="all, delete-orphan")
    creator = relationship("Member", foreign_keys=[created_by_member_id])
    messages = relationship("Message", back_populates="room", cascade="all, delete-orphan")


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, default=MemberType.AGENT)
    token = Column(String, nullable=True, index=True)
    user_token = Column(String, nullable=True, index=True)
    role = Column(String, default="member")
    description = Column(Text, default="", nullable=False)
    display_name = Column(String, nullable=True)
    joined_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)

    room = relationship("Room", foreign_keys=[room_id], back_populates="members")
    messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("members.id"), nullable=True)
    content = Column(Text, nullable=False)
    to_member_id = Column(Integer, ForeignKey("members.id"), nullable=True)
    msg_type = Column(String, default=MessageType.MESSAGE)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    room = relationship("Room", back_populates="messages")
    sender = relationship("Member", foreign_keys=[sender_id], back_populates="messages")


class WebhookConfig(Base):
    __tablename__ = "webhook_configs"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    url = Column(String, nullable=False)
    events = Column(String, default="message,join")  # 逗号分隔的事件列表
    secret = Column(String, default="")  # 用于签名验证
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class FileLock(Base):
    __tablename__ = "file_locks"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    file_path = Column(String, nullable=False)
    agent_name = Column(String, nullable=False)
    acquired_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    uploader_name = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    room = relationship("Room")
    message = relationship("Message")


class DraftMessage(Base):
    __tablename__ = "draft_messages"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    content = Column(Text, default="", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    room = relationship("Room")
    member = relationship("Member")


class MessageRead(Base):
    __tablename__ = "message_reads"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    read_at = Column(DateTime, default=datetime.utcnow)

    room = relationship("Room")
    member = relationship("Member")
    message = relationship("Message")
