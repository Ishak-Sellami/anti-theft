import pytest
import hashlib
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient
from app.core.crypto import sign_payload, canonical_json_bytes


@pytest.mark.asyncio
async def test_full_android_agent_e2e_integration_flow(client: AsyncClient, device_keypair):
    priv_pem, pub_pem, _ = device_keypair

    # =========================================================================
    # 1. OWNER ONBOARDING & ENROLLMENT
    # =========================================================================
    # Register Owner
    reg_resp = await client.post("/api/v1/auth/register", json={
        "email": "sarika_owner@example.com",
        "password": "MasterSecurePassword2026!",
        "full_name": "Anti-Sarika Owner",
        "role": "OWNER"
    })
    assert reg_resp.status_code == 201

    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "sarika_owner@example.com",
        "password": "MasterSecurePassword2026!"
    })
    token = login_resp.json()["access_token"]
    owner_headers = {"Authorization": f"Bearer {token}"}

    # Step 1: Request enrollment token from backend
    init_resp = await client.post("/api/v1/devices/enroll/initiate", headers=owner_headers, json={
        "device_name": "Pixel 8 Pro - AntiSarika Edition",
        "device_model": "GPJ41",
        "os_version": "Android 14 (API 34)"
    })
    assert init_resp.status_code == 200
    enrollment_token = init_resp.json()["enrollment_token"]
    backend_pubkey = init_resp.json()["backend_public_key_pem"]
    assert enrollment_token.startswith("pair_")

    # Step 2: Android Agent completes enrollment with ECDSA signed payload
    now = datetime.now(timezone.utc)
    enroll_nonce = "android_enroll_nonce_001"
    enroll_payload = {
        "agent_version": "0.1.0",
        "device_model": "GPJ41",
        "device_name": "Pixel 8 Pro - AntiSarika Edition",
        "enrollment_token": enrollment_token,
        "nonce": enroll_nonce,
        "os_version": "Android 14 (API 34)",
        "timestamp": now.isoformat()
    }
    enroll_sig = sign_payload(enroll_payload, priv_pem)

    complete_resp = await client.post("/api/v1/devices/enroll/complete", json={
        "enrollment_token": enrollment_token,
        "public_key_pem": pub_pem,
        "device_name": "Pixel 8 Pro - AntiSarika Edition",
        "device_model": "GPJ41",
        "os_version": "Android 14 (API 34)",
        "agent_version": "0.1.0",
        "nonce": enroll_nonce,
        "timestamp": now.isoformat(),
        "signature": enroll_sig
    })
    assert complete_resp.status_code == 201
    device = complete_resp.json()
    device_id = device["id"]
    assert device["security_state"] == "NORMAL"
    assert device["connectivity_state"] == "ONLINE"
    assert device["power_state"] == "NORMAL"

    # =========================================================================
    # 2. STORE-AND-FORWARD TELEMETRY INGESTION
    # =========================================================================
    t1 = now - timedelta(minutes=10)
    t2 = now - timedelta(minutes=5)

    telemetry_items = [
        {
            "latitude": 52.5200,
            "longitude": 13.4050,
            "altitude": 42.0,
            "accuracy": 8.5,
            "speed": 0.0,
            "bearing": 0.0,
            "provider": "fused",
            "battery_level": 82,
            "power_state": "NORMAL",
            "security_state": "NORMAL",
            "connectivity_state": "ONLINE",
            "network_metadata": {"cell_id": "262-01-4451"},
            "recorded_at": t1.isoformat()
        },
        {
            "latitude": 52.5215,
            "longitude": 13.4065,
            "altitude": 42.5,
            "accuracy": 4.0,
            "speed": 1.1,
            "bearing": 45.0,
            "provider": "gps",
            "battery_level": 81,
            "power_state": "NORMAL",
            "security_state": "NORMAL",
            "connectivity_state": "ONLINE",
            "network_metadata": {"wifi_ssid": "AntiSarika_HQ"},
            "recorded_at": t2.isoformat()
        }
    ]

    telem_nonce = "telem_nonce_android_002"
    telem_ts = datetime.now(timezone.utc)
    telem_payload = {
        "device_id": str(device_id),
        "items": telemetry_items,
        "nonce": telem_nonce,
        "timestamp": telem_ts.isoformat()
    }
    telem_sig = sign_payload(telem_payload, priv_pem)

    telem_resp = await client.post("/api/v1/telemetry/batch", json={
        "device_id": device_id,
        "items": telemetry_items,
        "nonce": telem_nonce,
        "timestamp": telem_ts.isoformat(),
        "signature": telem_sig
    })
    assert telem_resp.status_code == 201
    assert telem_resp.json()["ingested_count"] == 2

    # =========================================================================
    # 3. POWER-OFF THREAT DETECTION & AUTOMATIC STOLEN MODE TRANSITION
    # =========================================================================
    ev_nonce = "sec_ev_nonce_003"
    ev_ts = datetime.now(timezone.utc)
    ev_payload = {
        "device_id": str(device_id),
        "event_type": "POWER_OFF_ATTEMPT",
        "severity": "CRITICAL",
        "security_state_before": "NORMAL",
        "security_state_after": "STOLEN",
        "payload": {"trigger": "ACTION_SHUTDOWN_INTERCEPTED", "battery": 80},
        "device_timestamp": ev_ts.isoformat(),
        "nonce": ev_nonce
    }
    ev_sig = sign_payload(ev_payload, priv_pem)

    ev_resp = await client.post("/api/v1/events", json={
        "device_id": device_id,
        "event_type": "POWER_OFF_ATTEMPT",
        "severity": "CRITICAL",
        "security_state_before": "NORMAL",
        "security_state_after": "STOLEN",
        "payload": {"trigger": "ACTION_SHUTDOWN_INTERCEPTED", "battery": 80},
        "device_timestamp": ev_ts.isoformat(),
        "nonce": ev_nonce,
        "signature": ev_sig
    })
    assert ev_resp.status_code == 201

    # Verify device state is now STOLEN
    dev_state_resp = await client.get(f"/api/v1/devices/{device_id}", headers=owner_headers)
    assert dev_state_resp.json()["security_state"] == "STOLEN"

    # =========================================================================
    # 4. REMOTE COMMAND EXECUTION & SIGNED ACKNOWLEDGEMENT
    # =========================================================================
    # Owner issues REMOTE_LOCK command
    cmd_resp = await client.post("/api/v1/commands", headers=owner_headers, json={
        "device_id": device_id,
        "command_type": "LOCK_DEVICE",
        "payload": {"reason": "Device stolen"},
        "ttl_seconds": 300
    })
    assert cmd_resp.status_code == 201
    cmd = cmd_resp.json()
    command_id = cmd["id"]
    assert cmd["status"] == "PENDING"

    # Device polls pending commands
    pending_cmds_resp = await client.get(f"/api/v1/commands/{device_id}/pending")
    assert pending_cmds_resp.status_code == 200
    pending_cmds = pending_cmds_resp.json()
    assert any(c["id"] == command_id for c in pending_cmds)

    # Device executes and submits signed ACK
    ack_nonce = "ack_nonce_004"
    ack_ts = datetime.now(timezone.utc)
    ack_payload = {
        "command_id": str(command_id),
        "device_id": str(device_id),
        "error_message": None,
        "nonce": ack_nonce,
        "result_payload": {"device_locked": "true"},
        "status": "EXECUTED",
        "timestamp": ack_ts.isoformat()
    }
    ack_sig = sign_payload(ack_payload, priv_pem)

    ack_resp = await client.post("/api/v1/commands/ack", json={
        "command_id": command_id,
        "device_id": device_id,
        "status": "EXECUTED",
        "result_payload": {"device_locked": "true"},
        "error_message": None,
        "nonce": ack_nonce,
        "timestamp": ack_ts.isoformat(),
        "signature": ack_sig
    })
    assert ack_resp.status_code == 200
    assert ack_resp.json()["status"] == "EXECUTED"

    # =========================================================================
    # 5. ANTI-THEFT EVIDENCE CAPTURE IN STOLEN MODE
    # =========================================================================
    # Device in STOLEN mode captures forensic RF/sensor snapshot
    raw_evidence = b"stolen_incident_rf_survey_cells_and_wifi_beacons_2026_08_31"
    evidence_hash = hashlib.sha256(raw_evidence).hexdigest()

    ev_cap_nonce = "ev_cap_nonce_005"
    ev_cap_ts = datetime.now(timezone.utc)
    ev_cap_payload = {
        "capture_type": "AMBIENT_RF",
        "device_id": str(device_id),
        "device_timestamp": ev_cap_ts.isoformat(),
        "event_id": None,
        "integrity_hash": evidence_hash,
        "mime_type": "application/json",
        "nonce": ev_cap_nonce,
        "storage_ref": "local:///stolen_evidence_vault/ev_test_001.json"
    }
    ev_cap_sig = sign_payload(ev_cap_payload, priv_pem)

    ev_submit_resp = await client.post("/api/v1/evidence", json={
        "device_id": device_id,
        "event_id": None,
        "capture_type": "AMBIENT_RF",
        "integrity_hash": evidence_hash,
        "storage_ref": "local:///stolen_evidence_vault/ev_test_001.json",
        "mime_type": "application/json",
        "file_size_bytes": str(len(raw_evidence)),
        "chain_of_custody_notes": "STOLEN mode ambient RF survey capture",
        "device_timestamp": ev_cap_ts.isoformat(),
        "nonce": ev_cap_nonce,
        "signature": ev_cap_sig
    })
    assert ev_submit_resp.status_code == 201
    assert ev_submit_resp.json()["integrity_hash"] == evidence_hash

    # =========================================================================
    # 6. EVIDENCE ACCESS CONTROL (OWNER ONLY, REJECT UNAUTHORIZED)
    # =========================================================================
    # Legitimate owner queries evidence -> 200 OK
    owner_ev_resp = await client.get(f"/api/v1/evidence/{device_id}", headers=owner_headers)
    assert owner_ev_resp.status_code == 200
    evidence_records = owner_ev_resp.json()
    assert len(evidence_records) == 1
    assert evidence_records[0]["integrity_hash"] == evidence_hash

    # Attacker / Non-owner queries evidence -> 403 FORBIDDEN
    await client.post("/api/v1/auth/register", json={
        "email": "unauthorized_user@example.com",
        "password": "Password123!",
        "role": "OWNER"
    })
    unauth_login = await client.post("/api/v1/auth/login", json={
        "email": "unauthorized_user@example.com",
        "password": "Password123!"
    })
    unauth_headers = {"Authorization": f"Bearer {unauth_login.json()['access_token']}"}

    unauth_ev_resp = await client.get(f"/api/v1/evidence/{device_id}", headers=unauth_headers)
    assert unauth_ev_resp.status_code == 403
    assert unauth_ev_resp.json()["error_code"] == "PERMISSION_DENIED"
