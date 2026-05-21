from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, Boolean
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
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship("Member", back_populates="room", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="room", cascade="all, delete-orphan")


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, default=MemberType.AGENT)
    joined_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)

    room = relationship("Room", back_populates="members")
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
