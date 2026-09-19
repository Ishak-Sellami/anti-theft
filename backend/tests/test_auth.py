import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_user_registration_and_login(client: AsyncClient):
    # Register new user
    reg_response = await client.post("/api/v1/auth/register", json={
        "email": "owner@example.com",
        "password": "SecurePassword123!",
        "full_name": "Test Owner",
        "role": "OWNER"
    })
    assert reg_response.status_code == 201
    user_data = reg_response.json()
    assert user_data["email"] == "owner@example.com"
    assert "id" in user_data

    # Login with valid credentials
    login_response = await client.post("/api/v1/auth/login", json={
        "email": "owner@example.com",
        "password": "SecurePassword123!"
    })
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert token_data["role"] == "OWNER"

    # Access protected /me endpoint
    me_response = await client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {token_data['access_token']}"
    })
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "owner@example.com"


@pytest.mark.asyncio
async def test_invalid_login_rejection(client: AsyncClient):
    # Register user
    await client.post("/api/v1/auth/register", json={
        "email": "user2@example.com",
        "password": "CorrectPassword123!",
        "role": "OWNER"
    })

    # Wrong password
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "user2@example.com",
        "password": "WrongPassword!"
    })
    assert login_resp.status_code == 401
    assert login_resp.json()["error_code"] == "AUTHENTICATION_FAILED"


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401
