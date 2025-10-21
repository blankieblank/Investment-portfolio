import pytest
from httpx import AsyncClient
from typing import Dict


async def create_user_and_get_token(async_client: AsyncClient, email: str, password: str) -> Dict[str, str]:
    await async_client.post("/auth/register", json={"email": email, "password": password})
    login_response = await async_client.post(
        "/auth/token",
        data={"username": email, "password": password}
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_register_user(async_client: AsyncClient):
    response = await async_client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_portfolio_unauthorized(async_client: AsyncClient):
    response = await async_client.post(
        "/portfolios/",
        json={"name": "My Tech Stocks"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_and_get_portfolios(async_client: AsyncClient):
    headers = await create_user_and_get_token(async_client, "user1@test.com", "pass1")
    response_create_1 = await async_client.post(
        "/portfolios/",
        json={"name": "Growth Stocks"},
        headers=headers
    )
    assert response_create_1.status_code == 201
    response_create_2 = await async_client.post(
        "/portfolios/",
        json={"name": "Value Stocks"},
        headers=headers
    )
    assert response_create_2.status_code == 201
    response_get = await async_client.get("/portfolios/", headers=headers)
    assert response_get.status_code == 200
    data = response_get.json()
    assert len(data) == 2
    portfolio_names = {p["name"] for p in data}
    assert portfolio_names == {"Growth Stocks", "Value Stocks"}


@pytest.mark.asyncio
async def test_add_transaction_to_portfolio(async_client: AsyncClient):
    headers = await create_user_and_get_token(async_client, "user2@test.com", "pass2")
    portfolio_response = await async_client.post(
        "/portfolios/",
        json={"name": "Crypto"},
        headers=headers
    )
    portfolio_id = portfolio_response.json()["id"]
    transaction_data = {
        "ticker": "BTC",
        "asset_type": "crypto",
        "transaction_type": "buy",
        "quantity": 0.5,
        "price_per_share": 30000.0,
        "transaction_date": "2025-10-26T10:00:00Z"
    }
    response_add_tx = await async_client.post(
        f"/portfolios/{portfolio_id}/transactions/",
        json=transaction_data,
        headers=headers
    )

    assert response_add_tx.status_code == 201
    created_tx = response_add_tx.json()
    assert created_tx["quantity"] == 0.5
    assert created_tx["price_per_share"] == 30000.0

    response_get = await async_client.get("/portfolios/", headers=headers)
    portfolio_data = response_get.json()[0]
    assert len(portfolio_data["transactions"]) == 1
    assert portfolio_data["transactions"][0]["id"] == created_tx["id"]


@pytest.mark.asyncio
async def test_portfolio_isolation_between_users(async_client: AsyncClient):
    headers_user_A = await create_user_and_get_token(async_client, "userA@test.com", "passA")
    headers_user_B = await create_user_and_get_token(async_client, "userB@test.com", "passB")

    await async_client.post("/portfolios/", json={"name": "Portfolio A"}, headers=headers_user_A)
    response_user_B = await async_client.get("/portfolios/", headers=headers_user_B)
    assert response_user_B.status_code == 200
    assert len(response_user_B.json()) == 0

    response_user_A = await async_client.get("/portfolios/", headers=headers_user_A)
    assert response_user_A.status_code == 200
    assert len(response_user_A.json()) == 1
    assert response_user_A.json()[0]["name"] == "Portfolio A"


@pytest.mark.asyncio
async def test_cannot_add_transaction_to_foreign_portfolio(async_client: AsyncClient):
    headers_user_A = await create_user_and_get_token(async_client, "userA@test.com", "passA")
    headers_user_B = await create_user_and_get_token(async_client, "userB@test.com", "passB")
    portfolio_A_response = await async_client.post("/portfolios/", json={"name": "Portfolio A"}, headers=headers_user_A)
    portfolio_A_id = portfolio_A_response.json()["id"]
    transaction_data = {
        "ticker": "FRAUD",
        "transaction_type": "buy",
        "quantity": 100,
        "price_per_share": 1.0,
        "transaction_date": "2025-10-26T12:00:00Z"
    }
    response_fraud = await async_client.post(
        f"/portfolios/{portfolio_A_id}/transactions/",
        json=transaction_data,
        headers=headers_user_B
    )
    assert response_fraud.status_code == 403
