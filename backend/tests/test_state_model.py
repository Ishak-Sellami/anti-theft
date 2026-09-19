import pytest
from datetime import datetime, timezone
from httpx import AsyncClient
from app.core.crypto import sign_payload


@pytest.mark.asyncio
async def test_three_dimensional_state_model(client: AsyncClient, device_keypair):
    priv_pem, pub_pem, _ = device_keypair

    # Register and enroll
    await client.post("/api/v1/auth/register", json={
        "email": "state_owner@example.com",
        "password": "Password123!"
    })
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "state_owner@example.com",
        "password": "Password123!"
    })
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    init_resp = await client.post("/api/v1/devices/enroll/initiate", headers=headers, json={"device_name": "State Test Phone"})
    token = init_resp.json()["enrollment_token"]

    now = datetime.now(timezone.utc)
    nonce = "nonce_state_001"
    p = {
        "enrollment_token": token,
        "device_name": "State Test Phone",
        "device_model": None,
        "os_version": None,
        "agent_version": None,
        "nonce": nonce,
        "timestamp": now.isoformat()
    }
    sig = sign_payload(p, priv_pem)

    enrolled = await client.post("/api/v1/devices/enroll/complete", json={
        "enrollment_token": token,
        "public_key_pem": pub_pem,
        "device_name": "State Test Phone",
        "nonce": nonce,
        "timestamp": now.isoformat(),
        "signature": sig
    })
    device_id = enrolled.json()["id"]

    # 1. Update Security State: NORMAL -> STOLEN
    stolen_resp = await client.patch(
        f"/api/v1/devices/{device_id}/security-state",
        headers=headers,
        json={"target_security_state": "STOLEN", "reason": "Owner reported theft"}
    )
    assert stolen_resp.status_code == 200
    assert stolen_resp.json()["security_state"] == "STOLEN"

    # 2. Simulate Heartbeat with LOW battery (15%) and OFFLINE/DEGRADED connectivity
    hb_nonce = "nonce_hb_low_pwr"
    hb_time = datetime.now(timezone.utc)
    hb_payload = {
        "device_id": device_id,
        "battery_level": 15,
        "is_charging": False,
        "connectivity_state": "DEGRADED",
        "nonce": hb_nonce,
        "timestamp": hb_time.isoformat()
    }
    hb_sig = sign_payload(hb_payload, priv_pem)

    hb_resp = await client.post("/api/v1/devices/heartbeat", json={
        "device_id": device_id,
        "battery_level": 15,
        "is_charging": False,
        "connectivity_state": "DEGRADED",
        "nonce": hb_nonce,
        "timestamp": hb_time.isoformat(),
        "signature": hb_sig
    })
    assert hb_resp.status_code == 200
    data = hb_resp.json()

    # Verify composite multi-dimensional state: STOLEN + DEGRADED + LOW
    assert data["security_state"] == "STOLEN"
    assert data["connectivity_state"] == "DEGRADED"
    assert data["power_state"] == "LOW"

    # 3. Transition STOLEN -> RECOVERY
    recovery_resp = await client.patch(
        f"/api/v1/devices/{device_id}/security-state",
        headers=headers,
        json={"target_security_state": "RECOVERY", "reason": "Recovery operation started"}
    )
    assert recovery_resp.status_code == 200
    assert recovery_resp.json()["security_state"] == "RECOVERY"

    # 4. Transition RECOVERY -> NORMAL (Authorized)
    normal_resp = await client.patch(
        f"/api/v1/devices/{device_id}/security-state",
        headers=headers,
        json={"target_security_state": "NORMAL", "reason": "Device recovered successfully"}
    )
    assert normal_resp.status_code == 200
    assert normal_resp.json()["security_state"] == "NORMAL"
