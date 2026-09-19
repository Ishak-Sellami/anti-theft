import pytest
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient
from app.core.crypto import sign_payload


@pytest.mark.asyncio
async def test_device_enrollment_lifecycle(client: AsyncClient, device_keypair):
    priv_pem, pub_pem, _ = device_keypair

    # 1. Register owner and login
    await client.post("/api/v1/auth/register", json={
        "email": "deviceowner@example.com",
        "password": "Password123!",
        "role": "OWNER"
    })
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "deviceowner@example.com",
        "password": "Password123!"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Initiate enrollment
    init_resp = await client.post("/api/v1/devices/enroll/initiate", headers=headers, json={
        "device_name": "Pixel 8 Pro",
        "device_model": "GPJ41",
        "os_version": "Android 14 (API 34)"
    })
    assert init_resp.status_code == 200
    init_data = init_resp.json()
    enrollment_token = init_data["enrollment_token"]
    backend_pubkey = init_data["backend_public_key_pem"]
    assert enrollment_token.startswith("pair_")
    assert "-----BEGIN PUBLIC KEY-----" in backend_pubkey

    # 3. Complete enrollment (Device signs payload)
    now = datetime.now(timezone.utc)
    nonce = "test_nonce_enroll_001"
    payload_to_sign = {
        "enrollment_token": enrollment_token,
        "device_name": "Pixel 8 Pro",
        "device_model": "GPJ41",
        "os_version": "Android 14 (API 34)",
        "agent_version": "0.1.0",
        "nonce": nonce,
        "timestamp": now.isoformat()
    }
    signature = sign_payload(payload_to_sign, priv_pem)

    complete_resp = await client.post("/api/v1/devices/enroll/complete", json={
        "enrollment_token": enrollment_token,
        "public_key_pem": pub_pem,
        "device_name": "Pixel 8 Pro",
        "device_model": "GPJ41",
        "os_version": "Android 14 (API 34)",
        "agent_version": "0.1.0",
        "nonce": nonce,
        "timestamp": now.isoformat(),
        "signature": signature
    })
    assert complete_resp.status_code == 201
    device_data = complete_resp.json()
    device_id = device_data["id"]
    assert device_data["device_name"] == "Pixel 8 Pro"
    assert device_data["security_state"] == "NORMAL"
    assert device_data["connectivity_state"] == "ONLINE"
    assert device_data["power_state"] == "NORMAL"
    assert len(device_data["public_key_fingerprint"]) == 64

    # 4. Query devices list for owner
    list_resp = await client.get("/api/v1/devices", headers=headers)
    assert list_resp.status_code == 200
    devices = list_resp.json()
    assert len(devices) == 1
    assert devices[0]["id"] == device_id


@pytest.mark.asyncio
async def test_cryptographic_verification_rejection(client: AsyncClient, device_keypair):
    priv_pem, pub_pem, _ = device_keypair

    # Register & initiate
    await client.post("/api/v1/auth/register", json={
        "email": "crypto_test@example.com",
        "password": "Password123!"
    })
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "crypto_test@example.com",
        "password": "Password123!"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    init_resp = await client.post("/api/v1/devices/enroll/initiate", headers=headers, json={
        "device_name": "Galaxy S24",
    })
    enrollment_token = init_resp.json()["enrollment_token"]

    now = datetime.now(timezone.utc)
    nonce = "test_nonce_crypto_bad"
    payload_to_sign = {
        "enrollment_token": enrollment_token,
        "device_name": "Galaxy S24",
        "device_model": None,
        "os_version": None,
        "agent_version": None,
        "nonce": nonce,
        "timestamp": now.isoformat()
    }
    signature = sign_payload(payload_to_sign, priv_pem)

    # Tamper with device name in request
    bad_resp = await client.post("/api/v1/devices/enroll/complete", json={
        "enrollment_token": enrollment_token,
        "public_key_pem": pub_pem,
        "device_name": "TAMPERED_DEVICE_NAME",  # mismatch with signature!
        "device_model": None,
        "os_version": None,
        "agent_version": None,
        "nonce": nonce,
        "timestamp": now.isoformat(),
        "signature": signature
    })
    assert bad_resp.status_code == 401
    assert bad_resp.json()["error_code"] == "CRYPTO_VERIFICATION_FAILED"


@pytest.mark.asyncio
async def test_replay_protection_nonce_reuse(client: AsyncClient, device_keypair):
    priv_pem, pub_pem, _ = device_keypair

    # Register & enroll
    await client.post("/api/v1/auth/register", json={
        "email": "nonce_test@example.com",
        "password": "Password123!"
    })
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "nonce_test@example.com",
        "password": "Password123!"
    })
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    init_resp = await client.post("/api/v1/devices/enroll/initiate", headers=headers, json={"device_name": "Test Phone"})
    token1 = init_resp.json()["enrollment_token"]

    now = datetime.now(timezone.utc)
    reused_nonce = "reused_nonce_12345"

    p1 = {
        "enrollment_token": token1,
        "device_name": "Test Phone",
        "device_model": None,
        "os_version": None,
        "agent_version": None,
        "nonce": reused_nonce,
        "timestamp": now.isoformat()
    }
    sig1 = sign_payload(p1, priv_pem)

    r1 = await client.post("/api/v1/devices/enroll/complete", json={
        "enrollment_token": token1,
        "public_key_pem": pub_pem,
        "device_name": "Test Phone",
        "nonce": reused_nonce,
        "timestamp": now.isoformat(),
        "signature": sig1
    })
    assert r1.status_code == 201

    # Attempt to use same nonce for heartbeat
    hb_payload = {
        "device_id": r1.json()["id"],
        "battery_level": 85,
        "is_charging": False,
        "connectivity_state": "ONLINE",
        "nonce": reused_nonce,  # REUSED NONCE!
        "timestamp": now.isoformat()
    }
    hb_sig = sign_payload(hb_payload, priv_pem)

    hb_resp = await client.post("/api/v1/devices/heartbeat", json={
        "device_id": r1.json()["id"],
        "battery_level": 85,
        "is_charging": False,
        "connectivity_state": "ONLINE",
        "nonce": reused_nonce,
        "timestamp": now.isoformat(),
        "signature": hb_sig
    })
    assert hb_resp.status_code == 409
    assert hb_resp.json()["error_code"] == "REPLAY_DETECTED"
