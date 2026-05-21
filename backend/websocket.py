from typing import Dict, List
from fastapi import WebSocket
import json


class ConnectionManager:
    def __init__(self):
        # room_id -> list of websockets
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # room_id -> {agent_name: [websockets]}
        self.agent_connections: Dict[int, Dict[str, List[WebSocket]]] = {}

    async def connect(self, room_id: int, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, room_id: int, websocket: WebSocket):
        if room_id in self.active_connections:
            if websocket in self.active_connections[room_id]:
                self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
        # 清理 agent 映射
        if room_id in self.agent_connections:
            for agent_name in list(self.agent_connections[room_id].keys()):
                if websocket in self.agent_connections[room_id][agent_name]:
                    self.agent_connections[room_id][agent_name].remove(websocket)
                    if not self.agent_connections[room_id][agent_name]:
                        del self.agent_connections[room_id][agent_name]
            if not self.agent_connections[room_id]:
                del self.agent_connections[room_id]

    def register_agent(self, room_id: int, agent_name: str, websocket: WebSocket):
        """注册 agent 的 WebSocket 连接（支持多实例）"""
        if room_id not in self.agent_connections:
            self.agent_connections[room_id] = {}
        if agent_name not in self.agent_connections[room_id]:
            self.agent_connections[room_id][agent_name] = []
        if websocket not in self.agent_connections[room_id][agent_name]:
            self.agent_connections[room_id][agent_name].append(websocket)

    def unregister_agent(self, room_id: int, agent_name: str):
        """注销 agent 的所有 WebSocket 连接"""
        if room_id in self.agent_connections:
            self.agent_connections[room_id].pop(agent_name, None)
            if not self.agent_connections[room_id]:
                del self.agent_connections[room_id]

    def is_agent_connected(self, room_id: int, agent_name: str) -> bool:
        """检查 agent 是否在当前房间有活跃的 WS 连接"""
        if room_id not in self.agent_connections:
            return False
        return agent_name in self.agent_connections[room_id] and len(self.agent_connections[room_id][agent_name]) > 0

    def get_connected_agents(self, room_id: int) -> List[str]:
        """获取当前房间所有已连接 agent 的名称列表"""
        if room_id not in self.agent_connections:
            return []
        return [
            name for name, sockets in self.agent_connections[room_id].items()
            if sockets
        ]

    def get_agent_connection_count(self, room_id: int, agent_name: str) -> int:
        """获取指定 agent 在当前房间的 WS 连接数"""
        if room_id not in self.agent_connections:
            return 0
        return len(self.agent_connections[room_id].get(agent_name, []))

    async def broadcast(self, room_id: int, message: dict):
        if room_id not in self.active_connections:
            return
        payload = json.dumps(message, ensure_ascii=False)
        # 复制列表避免遍历中修改
        for connection in self.active_connections[room_id][:]:
            try:
                await connection.send_text(payload)
            except Exception:
                # 连接已断开，清理
                self.disconnect(room_id, connection)


manager = ConnectionManager()
