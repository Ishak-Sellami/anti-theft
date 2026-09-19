import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_recovery_policy_management(client: AsyncClient):
    # 1. Register Admin and Owner
    await client.post("/api/v1/auth/register", json={
        "email": "admin@example.com",
        "password": "Password123!",
        "role": "ADMIN"
    })
    admin_login = await client.post("/api/v1/auth/login", json={
        "email": "admin@example.com",
        "password": "Password123!"
    })
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    await client.post("/api/v1/auth/register", json={
        "email": "reg_user@example.com",
        "password": "Password123!",
        "role": "OWNER"
    })
    user_login = await client.post("/api/v1/auth/login", json={
        "email": "reg_user@example.com",
        "password": "Password123!"
    })
    user_headers = {"Authorization": f"Bearer {user_login.json()['access_token']}"}

    # 2. List default policies
    list_resp = await client.get("/api/v1/policies", headers=user_headers)
    assert list_resp.status_code == 200
    policies = list_resp.json()
    assert len(policies) >= 1
    assert any(p["id"] == "pol_stolen_default_v1" for p in policies)

    # 3. Non-admin attempting to create a policy is forbidden
    unauth_create = await client.post("/api/v1/policies", headers=user_headers, json={
        "id": "pol_custom_v1",
        "name": "Custom Policy",
        "is_default": False,
        "config": {
            "policy_version": 1,
            "policy_id": "pol_custom_v1",
            "security_state": "STOLEN",
            "power_state_overrides": {
                "NORMAL": {
                    "location_interval_ms": 20000,
                    "location_fastest_interval_ms": 10000,
                    "location_accuracy": "HIGH_ACCURACY",
                    "heartbeat_interval_ms": 60000,
                    "telemetry_batch_size": 2,
                    "enable_ble_beacon": False
                }
            },
            "retry_config": {
                "initial_retry_interval_ms": 5000,
                "max_retry_interval_ms": 60000,
                "backoff_multiplier": 2.0,
                "max_jitter_ms": 500
            },
            "storage_limits": {
                "offline_queue_max_records": 5000,
                "eviction_strategy": "DROP_OLDEST"
            }
        }
    })
    assert unauth_create.status_code == 403

    # 4. Admin creates valid policy
    admin_create = await client.post("/api/v1/policies", headers=admin_headers, json={
        "id": "pol_custom_v1",
        "name": "Custom Policy",
        "description": "High frequency tactical recovery",
        "is_default": False,
        "config": {
            "policy_version": 1,
            "policy_id": "pol_custom_v1",
            "security_state": "STOLEN",
            "power_state_overrides": {
                "NORMAL": {
                    "location_interval_ms": 20000,
                    "location_fastest_interval_ms": 10000,
                    "location_accuracy": "HIGH_ACCURACY",
                    "heartbeat_interval_ms": 60000,
                    "telemetry_batch_size": 2,
                    "enable_ble_beacon": True
                }
            },
            "retry_config": {
                "initial_retry_interval_ms": 5000,
                "max_retry_interval_ms": 60000,
                "backoff_multiplier": 2.0,
                "max_jitter_ms": 500
            },
            "storage_limits": {
                "offline_queue_max_records": 5000,
                "eviction_strategy": "DROP_OLDEST"
            }
        }
    })
    assert admin_create.status_code == 201
    assert admin_create.json()["id"] == "pol_custom_v1"
