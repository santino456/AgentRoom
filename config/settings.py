"""
AgentRoom 统一配置系统

加载优先级（从高到低）：
1. 环境变量（AGENTROOM_* 前缀）
2. ~/.agentroom/config.yaml
3. 内置默认值

使用方式：
    from config import settings
    print(settings.server.port)
"""

from pathlib import Path
from typing import Any

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings

DEFAULT_CONFIG_DIR = Path.home() / ".agentroom"
DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "config.yaml"


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load YAML config if exists."""
    if not path.exists():
        return {}
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        return {}


def _flatten_yaml(data: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Flatten nested YAML dict to dot-notation keys for env var compatibility."""
    result: dict[str, Any] = {}
    for key, value in data.items():
        full_key = f"{prefix}{key}" if not prefix else f"{prefix}_{key}"
        if isinstance(value, dict):
            result.update(_flatten_yaml(value, full_key))
        elif isinstance(value, list):
            # Convert list to comma-separated string for env var compatibility
            result[full_key] = ",".join(str(v) for v in value)
        else:
            result[full_key] = value
    return result


class ServerSettings(BaseSettings):
    host: str = "127.0.0.1"
    port: int = 8080


class DatabaseSettings(BaseSettings):
    url: str = Field(default=f"sqlite:///{DEFAULT_CONFIG_DIR}/agentroom.db")


class CorsSettings(BaseSettings):
    origins: list[str] = Field(default=["http://localhost:8080", "http://127.0.0.1:8080"])


class LimitSettings(BaseSettings):
    max_message_length: int = 4000
    max_room_name_length: int = 50
    max_member_name_length: int = 30
    default_lock_ttl: int = 300
    max_attachment_size_mb: int = 10


class LoggingSettings(BaseSettings):
    debug: bool = False
    json_format: bool = True


class Settings(BaseSettings):
    """AgentRoom unified settings."""

    model_config = ConfigDict(env_prefix="AGENTROOM_", case_sensitive=False)

    server: ServerSettings = Field(default_factory=ServerSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    cors: CorsSettings = Field(default_factory=CorsSettings)
    limits: LimitSettings = Field(default_factory=LimitSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    @property
    def database_url(self) -> str:
        return self.database.url

    @property
    def cors_origins(self) -> list[str]:
        return self.cors.origins

    @property
    def max_message_length(self) -> int:
        return self.limits.max_message_length

    @property
    def max_room_name_length(self) -> int:
        return self.limits.max_room_name_length

    @property
    def max_member_name_length(self) -> int:
        return self.limits.max_member_name_length

    @property
    def default_lock_ttl(self) -> int:
        return self.limits.default_lock_ttl

    @property
    def max_attachment_size_mb(self) -> int:
        return self.limits.max_attachment_size_mb

    @property
    def debug(self) -> bool:
        return self.logging.debug


def _merge_yaml_into_settings(yaml_data: dict[str, Any]) -> dict[str, Any]:
    """Convert nested YAML dict to Settings constructor kwargs."""
    result: dict[str, Any] = {}
    for section, values in yaml_data.items():
        if isinstance(values, dict):
            result[section] = values
    return result


def load_settings(config_path: Path | None = None) -> Settings:
    """Load settings from YAML + env vars."""
    path = config_path or DEFAULT_CONFIG_PATH
    yaml_data = _load_yaml(path)

    # Flatten for env var parsing
    flat = _flatten_yaml(yaml_data)

    # Build nested dict from flat keys
    nested: dict[str, Any] = {}
    for key, value in flat.items():
        parts = key.split("_")
        current = nested
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value

    return Settings(**nested)


# Global singleton
settings = load_settings()
