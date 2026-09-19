import asyncio
import json
from typing import Dict, Set, Any
from uuid import UUID
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # Map user_id -> set of active WebSockets
        self.user_connections: Dict[str, Set[WebSocket]] = {}
        # Set of admin/auditor WebSockets that receive all device events
        self.admin_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, user_id: str, role: str):
        await websocket.accept()
        if role in {"ADMIN", "INVESTIGATOR"}:
            self.admin_connections.add(websocket)

        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        self.admin_connections.discard(websocket)

    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Sends an event payload to all open sessions of a specific user."""
        message_str = json.dumps(message, default=str)
        recipients = set()
        if user_id in self.user_connections:
            recipients.update(self.user_connections[user_id])
        recipients.update(self.admin_connections)

        for ws in recipients:
            try:
                await ws.send_text(message_str)
            except Exception:
                pass

    async def broadcast_device_event(self, owner_id: UUID, event_type: str, data: Dict[str, Any]):
        """Broadcasts a device event to the device's owner and connected admins."""
        payload = {
            "type": event_type,
            "data": data,
        }
        await self.send_to_user(str(owner_id), payload)


ws_manager = ConnectionManager()
