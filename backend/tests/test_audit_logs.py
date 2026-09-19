import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_tamper_evident_audit_log_chaining(client: AsyncClient):
    # 1. Register Admin
    await client.post("/api/v1/auth/register", json={
        "email": "audit_admin@example.com",
        "password": "Password123!",
        "role": "ADMIN"
    })
    admin_login = await client.post("/api/v1/auth/login", json={
        "email": "audit_admin@example.com",
        "password": "Password123!"
    })
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    # 2. Register 2 standard users (each triggers audit log entry)
    await client.post("/api/v1/auth/register", json={
        "email": "user_audit_1@example.com",
        "password": "Password123!",
        "role": "OWNER"
    })
    await client.post("/api/v1/auth/register", json={
        "email": "user_audit_2@example.com",
        "password": "Password123!",
        "role": "OWNER"
    })

    # 3. Retrieve system audit logs
    audit_resp = await client.get("/api/v1/audit", headers=admin_headers)
    assert audit_resp.status_code == 200
    logs = audit_resp.json()
    assert len(logs) >= 3

    # Verify chronological integrity of hash chain (older logs first for verification)
    sorted_logs = sorted(logs, key=lambda x: x["id"])
    for i in range(1, len(sorted_logs)):
        prev_entry = sorted_logs[i - 1]
        curr_entry = sorted_logs[i]
        assert curr_entry["prev_hash"] == prev_entry["entry_hash"], f"Broken hash chain at index {i}"
