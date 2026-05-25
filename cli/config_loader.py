"""
AgentRoom 配置加载器
支持 YAML 配置文件 + 环境变量替换
"""
import os
import re
from typing import List, Dict, Any


def _expand_env(value: Any) -> Any:
    """递归替换字符串中的 ${ENV_VAR} 为环境变量值"""
    if isinstance(value, str):
        pattern = re.compile(r"\$\{(\w+)\}")
        def replacer(m):
            env_name = m.group(1)
            return os.environ.get(env_name, m.group(0))
        return pattern.sub(replacer, value)
    if isinstance(value, dict):
        return {k: _expand_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env(v) for v in value]
    return value


def load_config(path: str = "config/agents.yaml") -> Dict[str, Any]:
    """加载并解析配置文件"""
    try:
        import yaml
    except ImportError:
        raise ImportError("PyYAML not installed. Run: uv pip install pyyaml")

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    return _expand_env(raw)


def get_agent_config(config: Dict[str, Any], agent_name: str) -> Dict[str, Any]:
    """根据 name 获取单个 Agent 配置"""
    agents = config.get("agents", [])
    for agent in agents:
        if agent.get("name") == agent_name:
            return agent
    raise ValueError(f"Agent '{agent_name}' not found in config")


def list_agents(config: Dict[str, Any]) -> List[str]:
    """列出所有 Agent 名称"""
    return [a.get("name", "unknown") for a in config.get("agents", [])]


def get_global_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """获取全局配置"""
    return config.get("global", {})
