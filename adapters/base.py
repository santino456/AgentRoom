"""
Agent Adapter 基类
所有 AI 工具适配器都需要实现这个接口
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Callable


class AgentAdapter(ABC):
    """Agent 适配器基类"""

    name: str = "base"

    @abstractmethod
    def start_listening(self, room_id: int, on_mention: Callable[[List[Dict]], None]):
        """
        开始监听聊天室消息
        当检测到有 @本Agent 的消息时，调用 on_mention(messages)
        """
        pass

    @abstractmethod
    def send_message(self, room_id: int, content: str) -> bool:
        """发送消息到聊天室"""
        pass

    @abstractmethod
    def stop(self):
        """停止监听"""
        pass
