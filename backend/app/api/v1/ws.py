import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.security import decode_access_token
from app.services.ws_manager import ws_manager

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token passed as query parameter for authentication")
):
    """
    Authenticated WebSocket connection for Web Dashboard real-time telemetry, state changes, and security alerts.
    """
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        role = payload.get("role", "OWNER")
        if not user_id:
            await websocket.close(code=4001, reason="Invalid token subject")
            return
    except Exception:
        await websocket.close(code=4001, reason="Authentication failed")
        return

    await ws_manager.connect(websocket, user_id=user_id, role=role)

    # Send initial welcome / handshake confirmation
    await websocket.send_text(json.dumps({
        "type": "CONNECTION_ESTABLISHED",
        "user_id": user_id,
        "role": role
    }))

    try:
        while True:
            # Handle incoming ping / messages from client
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "PING":
                    await websocket.send_text(json.dumps({"type": "PONG"}))
            except Exception:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id=user_id)
    except Exception:
        ws_manager.disconnect(websocket, user_id=user_id)
