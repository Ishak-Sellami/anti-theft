import pytest
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient
from app.core.crypto import sign_payload


@pytest.mark.asyncio
async def test_telemetry_batch_and_store_forward(client: AsyncClient, device_keypair):
    priv_pem, pub_pem, _ = device_keypair

    # Register & enroll
    await client.post("/api/v1/auth/register", json={
        "email": "telem_owner@example.com",
        "password": "Password123!"
    })
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "telem_owner@example.com",
        "password": "Password123!"
    })
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    init_resp = await client.post("/api/v1/devices/enroll/initiate", headers=headers, json={"device_name": "Telemetry Device"})
    token = init_resp.json()["enrollment_token"]

    now = datetime.now(timezone.utc)
    nonce = "telem_enroll_nonce"
    p = {
        "enrollment_token": token,
        "device_name": "Telemetry Device",
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
        "device_name": "Telemetry Device",
        "nonce": nonce,
        "timestamp": now.isoformat(),
        "signature": sig
    })
    device_id = enrolled.json()["id"]

    # Prepare offline buffered telemetry (3 points recorded over the past 30 minutes)
    t1 = now - timedelta(minutes=30)
    t2 = now - timedelta(minutes=15)
    t3 = now - timedelta(minutes=1)

    items = [
        {
            "latitude": 52.5200,
            "longitude": 13.4050,
            "altitude": 34.5,
            "accuracy": 12.0,
            "speed": 1.2,
            "bearing": 180.0,
            "provider": "gps",
            "battery_level": 90,
            "power_state": "NORMAL",
            "security_state": "NORMAL",
            "connectivity_state": "OFFLINE",
            "network_metadata": {"cell_id": "262-01-1234"},
            "recorded_at": t1.isoformat()
        },
        {
            "latitude": 52.5210,
            "longitude": 13.4060,
            "altitude": 35.0,
            "accuracy": 8.0,
            "speed": 1.5,
            "bearing": 185.0,
            "provider": "fused",
            "battery_level": 88,
            "power_state": "NORMAL",
            "security_state": "NORMAL",
            "connectivity_state": "OFFLINE",
            "network_metadata": {"cell_id": "262-01-1234"},
            "recorded_at": t2.isoformat()
        },
        {
            "latitude": 52.5225,
            "longitude": 13.4080,
            "altitude": 35.2,
            "accuracy": 5.0,
            "speed": 0.0,
            "bearing": 0.0,
            "provider": "gps",
            "battery_level": 85,
            "power_state": "NORMAL",
            "security_state": "NORMAL",
            "connectivity_state": "ONLINE",
            "network_metadata": {"wifi_ssid": "AntiSarika_AP"},
            "recorded_at": t3.isoformat()
        }
    ]

    telem_nonce = "telem_batch_nonce_001"
    telem_timestamp = datetime.now(timezone.utc)
    payload_to_sign = {
        "device_id": str(device_id),
        "items": items,
        "nonce": telem_nonce,
        "timestamp": telem_timestamp.isoformat()
    }
    telem_sig = sign_payload(payload_to_sign, priv_pem)

    ingest_resp = await client.post("/api/v1/telemetry/batch", json={
        "device_id": device_id,
        "items": items,
        "nonce": telem_nonce,
        "timestamp": telem_timestamp.isoformat(),
        "signature": telem_sig
    })
    assert ingest_resp.status_code == 201
    assert ingest_resp.json()["ingested_count"] == 3

    # Query telemetry history
    history_resp = await client.get(f"/api/v1/telemetry/{device_id}/history", headers=headers)
    assert history_resp.status_code == 200
    history = history_resp.json()
    assert len(history) == 3
    # Newest point first
    assert history[0]["latitude"] == 52.5225
    assert history[0]["received_at"] is not None

    # Check device updated last known location
    dev_resp = await client.get(f"/api/v1/devices/{device_id}", headers=headers)
    dev_data = dev_resp.json()
    assert dev_data["last_known_lat"] == 52.5225
    assert dev_data["last_known_lng"] == 13.4080
    assert dev_data["battery_level"] == 85
