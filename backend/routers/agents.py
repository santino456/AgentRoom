import shutil
from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

AGENTS_DIR = Path.home() / ".agentroom" / "agents"

router = APIRouter(prefix="/api/agents", tags=["agents"])


class AgentHome(BaseModel):
    name: str
    model: str = ""
    system_prompt: str = ""
    skills: list[str] = []
    owner: str = ""
    description: str = ""
    avatar: str = ""
    agents_md: str = ""


class AgentHomeCreate(BaseModel):
    model: str = ""
    system_prompt: str = ""
    skills: list[str] = []
    owner: str = ""
    description: str = ""


def _agent_path(name: str) -> Path:
    return AGENTS_DIR / name


def _load_agent(name: str) -> dict:
    home = _agent_path(name)
    yaml_path = home / "agent.yaml"
    data = {"name": name}
    if yaml_path.exists():
        with open(yaml_path, "r", encoding="utf-8") as f:
            data.update(yaml.safe_load(f) or {})
    # Read AGENTS.md if exists
    md_path = home / "AGENTS.md"
    if md_path.exists():
        with open(md_path, "r", encoding="utf-8") as f:
            data["agents_md"] = f.read()
    else:
        data["agents_md"] = ""
    return data


def _save_agent(name: str, data: dict):
    home = _agent_path(name)
    home.mkdir(parents=True, exist_ok=True)
    yaml_path = home / "agent.yaml"
    # Save metadata to agent.yaml
    meta = {
        k: v
        for k, v in data.items()
        if k not in ("name", "agents_md")
    }
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(meta, f, allow_unicode=True, sort_keys=False)
    # Save agents_md to AGENTS.md
    if "agents_md" in data:
        md_path = home / "AGENTS.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(data["agents_md"])


@router.get("")
def list_agents():
    """List all agent homes."""
    if not AGENTS_DIR.exists():
        return []
    agents = []
    for item in sorted(AGENTS_DIR.iterdir()):
        if item.is_dir():
            data = _load_agent(item.name)
            agents.append(
                {
                    "name": data.get("name", item.name),
                    "description": data.get("description", ""),
                    "owner": data.get("owner", ""),
                    "avatar": data.get("avatar", ""),
                }
            )
    return agents


@router.get("/{name}")
def get_agent(name: str):
    """Get agent home details."""
    home = _agent_path(name)
    if not home.exists():
        raise HTTPException(status_code=404, detail="Agent not found")
    return _load_agent(name)


@router.post("/{name}")
def create_or_update_agent(name: str, data: AgentHomeCreate):
    """Create or update an agent home."""
    payload = data.model_dump()
    payload["name"] = name
    _save_agent(name, payload)
    return _load_agent(name)


@router.delete("/{name}")
def delete_agent(name: str):
    """Delete an agent home."""
    home = _agent_path(name)
    if not home.exists():
        raise HTTPException(status_code=404, detail="Agent not found")
    shutil.rmtree(home)
    return {"ok": True}
