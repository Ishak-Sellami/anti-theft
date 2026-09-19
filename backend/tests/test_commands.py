import pytest
from datetime import datetime, timezone
from httpx import AsyncClient
from app.core.crypto import sign_payload


@pytest.mark.asyncio
async def test_command_lifecycle_and_authorization(client: AsyncClient, device_keypair):
    priv_pem, pub_pem, _ = device_keypair

    # 1. Register Owner 1 & enroll device
    await client.post("/api/v1/auth/register", json={
        "email": "cmd_owner@example.com",
        "password": "Password123!"
    })
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "cmd_owner@example.com",
        "password": "Password123!"
    })
    token1 = login_resp.json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    init_resp = await client.post("/api/v1/devices/enroll/initiate", headers=headers1, json={"device_name": "Command Device"})
    enrollment_token = init_resp.json()["enrollment_token"]

    now = datetime.now(timezone.utc)
    nonce = "cmd_enroll_nonce"
    p = {
        "enrollment_token": enrollment_token,
        "device_name": "Command Device",
        "device_model": None,
        "os_version": None,
        "agent_version": None,
        "nonce": nonce,
        "timestamp": now.isoformat()
    }
    sig = sign_payload(p, priv_pem)

    enrolled = await client.post("/api/v1/devices/enroll/complete", json={
        "enrollment_token": enrollment_token,
        "public_key_pem": pub_pem,
        "device_name": "Command Device",
        "nonce": nonce,
        "timestamp": now.isoformat(),
        "signature": sig
    })
    device_id = enrolled.json()["id"]

    # 2. Register Owner 2 (Attacker/Unauthorized user)
    await client.post("/api/v1/auth/register", json={
        "email": "attacker@example.com",
        "password": "Password123!"
    })
    login_resp2 = await client.post("/api/v1/auth/login", json={
        "email": "attacker@example.com",
        "password": "Password123!"
    })
    headers2 = {"Authorization": f"Bearer {login_resp2.json()['access_token']}"}

    # Attempt to issue command from Owner 2 -> Rejected (403)
    unauth_cmd = await client.post("/api/v1/commands", headers=headers2, json={
        "device_id": device_id,
        "command_type": "TRIGGER_ALARM",
        "payload": {"volume": 100},
        "ttl_seconds": 300
    })
    assert unauth_cmd.status_code == 403
    assert unauth_cmd.json()["error_code"] == "PERMISSION_DENIED"

    # 3. Legitimate Owner issues command
    auth_cmd = await client.post("/api/v1/commands", headers=headers1, json={
        "device_id": device_id,
        "command_type": "TRIGGER_ALARM",
        "payload": {"volume": 100, "pattern": "SOS"},
        "ttl_seconds": 300
    })
    assert auth_cmd.status_code == 201
    cmd_data = auth_cmd.json()
    cmd_id = cmd_data["id"]
    assert cmd_data["status"] == "PENDING"
    assert cmd_data["signature"] is not None

    # 4. Device polls pending commands
    pending_resp = await client.get(f"/api/v1/commands/{device_id}/pending")
    assert pending_resp.status_code == 200
    pending_list = pending_resp.json()
    assert len(pending_list) == 1
    assert pending_list[0]["id"] == cmd_id

    # 5. Device executes and acknowledges command with signature
    ack_nonce = "nonce_cmd_ack_001"
    ack_time = datetime.now(timezone.utc)
    ack_payload = {
        "command_id": cmd_id,
        "device_id": device_id,
        "status": "EXECUTED",
        "result_payload": {"alarm_playing": True, "decibels": 95},
        "error_message": None,
        "nonce": ack_nonce,
        "timestamp": ack_time.isoformat()
    }
    ack_sig = sign_payload(ack_payload, priv_pem)

    ack_resp = await client.post("/api/v1/commands/ack", json={
        "command_id": cmd_id,
        "device_id": device_id,
        "status": "EXECUTED",
        "result_payload": {"alarm_playing": True, "decibels": 95},
        "error_message": None,
        "nonce": ack_nonce,
        "timestamp": ack_time.isoformat(),
        "signature": ack_sig
    })
    assert ack_resp.status_code == 200
    assert ack_resp.json()["status"] == "EXECUTED"
    assert ack_resp.json()["executed_at"] is not None
