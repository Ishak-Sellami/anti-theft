import pytest
from datetime import datetime, timezone
from httpx import AsyncClient
from app.core.crypto import sign_payload


@pytest.mark.asyncio
async def test_power_off_and_factory_reset_security_events(client: AsyncClient, device_keypair):
    priv_pem, pub_pem, _ = device_keypair

    # Register & enroll
    await client.post("/api/v1/auth/register", json={
        "email": "event_owner@example.com",
        "password": "Password123!"
    })
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "event_owner@example.com",
        "password": "Password123!"
    })
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    init_resp = await client.post("/api/v1/devices/enroll/initiate", headers=headers, json={"device_name": "SecEvent Device"})
    token = init_resp.json()["enrollment_token"]

    now = datetime.now(timezone.utc)
    nonce = "sec_enroll_nonce"
    p = {
        "enrollment_token": token,
        "device_name": "SecEvent Device",
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
        "device_name": "SecEvent Device",
        "nonce": nonce,
        "timestamp": now.isoformat(),
        "signature": sig
    })
    device_id = enrolled.json()["id"]

    # 1. Device reports POWER_OFF_ATTEMPT (Triggers state shift to STOLEN)
    event_time = datetime.now(timezone.utc)
    ev_nonce1 = "nonce_power_off_001"
    ev1_payload = {
        "device_id": device_id,
        "event_type": "POWER_OFF_ATTEMPT",
        "severity": "CRITICAL",
        "security_state_before": "NORMAL",
        "security_state_after": "STOLEN",
        "payload": {"trigger": "KEYGUARD_POWER_MENU_INTERCEPTED", "battery": 76},
        "device_timestamp": event_time.isoformat(),
        "nonce": ev_nonce1
    }
    ev1_sig = sign_payload(ev1_payload, priv_pem)

    ev1_resp = await client.post("/api/v1/events", json={
        "device_id": device_id,
        "event_type": "POWER_OFF_ATTEMPT",
        "severity": "CRITICAL",
        "security_state_before": "NORMAL",
        "security_state_after": "STOLEN",
        "payload": {"trigger": "KEYGUARD_POWER_MENU_INTERCEPTED", "battery": 76},
        "device_timestamp": event_time.isoformat(),
        "nonce": ev_nonce1,
        "signature": ev1_sig
    })
    assert ev1_resp.status_code == 201
    assert ev1_resp.json()["event_type"] == "POWER_OFF_ATTEMPT"

    # Verify device is now STOLEN
    dev_resp = await client.get(f"/api/v1/devices/{device_id}", headers=headers)
    assert dev_resp.json()["security_state"] == "STOLEN"

    # 2. Device reports FACTORY_RESET_ATTEMPT
    ev_nonce2 = "nonce_factory_reset_001"
    ev2_time = datetime.now(timezone.utc)
    ev2_payload = {
        "device_id": device_id,
        "event_type": "FACTORY_RESET_ATTEMPT",
        "severity": "CRITICAL",
        "security_state_before": "STOLEN",
        "security_state_after": "STOLEN",
        "payload": {"blocked_by": "DPC_DISALLOW_FACTORY_RESET", "user_authenticated": False},
        "device_timestamp": ev2_time.isoformat(),
        "nonce": ev_nonce2
    }
    ev2_sig = sign_payload(ev2_payload, priv_pem)

    ev2_resp = await client.post("/api/v1/events", json={
        "device_id": device_id,
        "event_type": "FACTORY_RESET_ATTEMPT",
        "severity": "CRITICAL",
        "security_state_before": "STOLEN",
        "security_state_after": "STOLEN",
        "payload": {"blocked_by": "DPC_DISALLOW_FACTORY_RESET", "user_authenticated": False},
        "device_timestamp": ev2_time.isoformat(),
        "nonce": ev_nonce2,
        "signature": ev2_sig
    })
    assert ev2_resp.status_code == 201

    # Query device events
    events_resp = await client.get(f"/api/v1/events/{device_id}", headers=headers)
    assert events_resp.status_code == 200
    events = events_resp.json()
    assert len(events) == 2
