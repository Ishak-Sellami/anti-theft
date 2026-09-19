import pytest
from httpx import AsyncClient
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_websocket_auth_flow(client: AsyncClient):
    # Valid token
    token = create_access_token(subject="00000000-0000-0000-0000-000000000001", role="OWNER")
    
    # We can test that unauthorized handshake closes with 4001
    # Using starlette / fastapi TestClient or httpx
    from starlette.testclient import TestClient
    from app.main import app

    with TestClient(app) as tc:
        # Invalid token rejection
        with pytest.raises(Exception):
            with tc.websocket_connect("/api/v1/ws?token=invalid_token") as ws:
                pass

        # Valid connection
        with tc.websocket_connect(f"/api/v1/ws?token={token}") as ws:
            data = ws.receive_json()
            assert data["type"] == "CONNECTION_ESTABLISHED"
            assert data["role"] == "OWNER"

            # Test Ping Pong
            ws.send_json({"type": "PING"})
            pong_resp = ws.receive_json()
            assert pong_resp["type"] == "PONG"
