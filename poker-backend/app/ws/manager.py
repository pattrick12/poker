from typing import Dict, Set
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.connections: Dict[str, Set[WebSocket]] = {}  # table_id -> websockets

    async def connect(self, websocket: WebSocket, table_id: str):
        await websocket.accept()
        if table_id not in self.connections:
            self.connections[table_id] = set()
        self.connections[table_id].add(websocket)

    async def disconnect(self, websocket: WebSocket, table_id: str):
        if table_id in self.connections:
            self.connections[table_id].discard(websocket)
            if not self.connections[table_id]:
                del self.connections[table_id]

    async def broadcast(self, table_id: str, message: dict):
        conns = list(self.connections.get(table_id, []))
        for ws in conns:
            try:
                await ws.send_json(message)
            except Exception:
                # Handle disconnected clients
                pass

manager = ConnectionManager()
