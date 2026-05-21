import os
from pathlib import Path

from pydantic import ConfigDict
from pydantic_settings import BaseSettings

DEFAULT_DB_DIR = Path.home() / ".agent-coop"
DEFAULT_DB_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_DB_URL = f"sqlite:///{DEFAULT_DB_DIR}/agent-coop.db"


class Settings(BaseSettings):
    database_url: str = DEFAULT_DB_URL
    cors_origins: list[str] = ["http://localhost:8080", "http://127.0.0.1:8080"]
    max_message_length: int = 4000
    max_room_name_length: int = 50
    max_member_name_length: int = 30
    default_lock_ttl: int = 300
    max_attachment_size_mb: int = 10
    debug: bool = False

    model_config = ConfigDict(env_prefix="AGENT_COOP_", case_sensitive=False)


settings = Settings()
