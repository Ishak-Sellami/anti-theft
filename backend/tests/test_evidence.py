import pytest
import hashlib
from datetime import datetime, timezone
from httpx import AsyncClient
from app.core.crypto import sign_payload


@pytest.mark.asyncio
async def test_evidence_metadata_and_integrity(client: AsyncClient, device_keypair):
    priv_pem, pub_pem, _ = device_keypair

    # Register & enroll
    await client.post("/api/v1/auth/register", json={
        "email": "evidence_owner@example.com",
        "password": "Password123!"
    })
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "evidence_owner@example.com",
        "password": "Password123!"
    })
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    init_resp = await client.post("/api/v1/devices/enroll/initiate", headers=headers, json={"device_name": "Evidence Device"})
    token = init_resp.json()["enrollment_token"]

    now = datetime.now(timezone.utc)
    nonce = "ev_enroll_nonce"
    p = {
        "enrollment_token": token,
        "device_name": "Evidence Device",
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
        "device_name": "Evidence Device",
        "nonce": nonce,
        "timestamp": now.isoformat(),
        "signature": sig
    })
    device_id = enrolled.json()["id"]

    # Submit evidence metadata
    raw_evidence_bytes = b"mock_sensor_and_cell_survey_data_2026_08_22"
    integrity_hash = hashlib.sha256(raw_evidence_bytes).hexdigest()

    ev_nonce = "nonce_evidence_001"
    ev_time = datetime.now(timezone.utc)
    ev_payload = {
        "device_id": device_id,
        "event_id": None,
        "capture_type": "AMBIENT_RF",
        "integrity_hash": integrity_hash,
        "storage_ref": "s3://anti-sarika-evidence/evidence_001.bin",
        "mime_type": "application/octet-stream",
        "device_timestamp": ev_time.isoformat(),
        "nonce": ev_nonce
    }
    ev_sig = sign_payload(ev_payload, priv_pem)

    submit_resp = await client.post("/api/v1/evidence", json={
        "device_id": device_id,
        "event_id": None,
        "capture_type": "AMBIENT_RF",
        "integrity_hash": integrity_hash,
        "storage_ref": "s3://anti-sarika-evidence/evidence_001.bin",
        "mime_type": "application/octet-stream",
        "file_size_bytes": str(len(raw_evidence_bytes)),
        "chain_of_custody_notes": "Captured during STOLEN recovery sweep",
        "device_timestamp": ev_time.isoformat(),
        "nonce": ev_nonce,
        "signature": ev_sig
    })
    assert submit_resp.status_code == 201
    assert submit_resp.json()["integrity_hash"] == integrity_hash

    # Query device evidence
    list_resp = await client.get(f"/api/v1/evidence/{device_id}", headers=headers)
    assert list_resp.status_code == 200
    evidence_list = list_resp.json()
    assert len(evidence_list) == 1
    assert evidence_list[0]["capture_type"] == "AMBIENT_RF"
