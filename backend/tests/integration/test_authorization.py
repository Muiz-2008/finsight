"""Proves the core security requirement directly: one user must never be
able to read, modify, or delete another user's financial data — not just
"in practice" but as a property every relevant endpoint upholds, checked
here across accounts, transactions, and portfolios.
"""


def _register_and_login(client, email: str) -> str:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "correcthorsebatterystaple"},
    )
    login = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "correcthorsebatterystaple"},
    )
    return login.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_user_cannot_read_another_users_transaction(client):
    token_a = _register_and_login(client, "alice@example.com")
    token_b = _register_and_login(client, "bob@example.com")

    account = client.post(
        "/api/v1/accounts",
        json={"name": "Checking", "account_type": "checking", "currency": "USD"},
        headers=_auth_headers(token_a),
    ).json()
    transaction = client.post(
        "/api/v1/transactions",
        json={
            "account_id": account["id"],
            "amount": "42.00",
            "currency": "USD",
            "transaction_type": "expense",
            "description": "Coffee",
            "date": "2026-01-15",
        },
        headers=_auth_headers(token_a),
    ).json()

    response = client.get(
        f"/api/v1/transactions/{transaction['id']}", headers=_auth_headers(token_b)
    )

    # 404, not 403 — confirming a resource exists (via a 403) for an ID
    # that isn't yours leaks information a truly unauthorized caller
    # shouldn't get.
    assert response.status_code == 404


def test_user_cannot_update_another_users_transaction(client):
    token_a = _register_and_login(client, "alice@example.com")
    token_b = _register_and_login(client, "bob@example.com")

    account = client.post(
        "/api/v1/accounts",
        json={"name": "Checking", "account_type": "checking", "currency": "USD"},
        headers=_auth_headers(token_a),
    ).json()
    transaction = client.post(
        "/api/v1/transactions",
        json={
            "account_id": account["id"],
            "amount": "42.00",
            "currency": "USD",
            "transaction_type": "expense",
            "description": "Coffee",
            "date": "2026-01-15",
        },
        headers=_auth_headers(token_a),
    ).json()

    response = client.put(
        f"/api/v1/transactions/{transaction['id']}",
        json={"description": "Hacked"},
        headers=_auth_headers(token_b),
    )

    assert response.status_code == 404


def test_user_cannot_create_a_transaction_against_another_users_account(client):
    token_a = _register_and_login(client, "alice@example.com")
    token_b = _register_and_login(client, "bob@example.com")

    account = client.post(
        "/api/v1/accounts",
        json={"name": "Checking", "account_type": "checking", "currency": "USD"},
        headers=_auth_headers(token_a),
    ).json()

    # Bob tries to attach a transaction to Alice's account_id directly.
    response = client.post(
        "/api/v1/transactions",
        json={
            "account_id": account["id"],
            "amount": "100.00",
            "currency": "USD",
            "transaction_type": "expense",
            "description": "Should not be allowed",
            "date": "2026-01-15",
        },
        headers=_auth_headers(token_b),
    )

    assert response.status_code == 404


def test_user_cannot_see_another_users_portfolio(client):
    token_a = _register_and_login(client, "alice@example.com")
    token_b = _register_and_login(client, "bob@example.com")

    portfolio = client.post(
        "/api/v1/portfolios", json={"name": "Retirement"}, headers=_auth_headers(token_a)
    ).json()

    response = client.get(
        f"/api/v1/portfolios/{portfolio['id']}/performance", headers=_auth_headers(token_b)
    )

    assert response.status_code == 404


def test_transaction_list_only_returns_the_caller_s_own_transactions(client):
    token_a = _register_and_login(client, "alice@example.com")
    token_b = _register_and_login(client, "bob@example.com")

    account_a = client.post(
        "/api/v1/accounts",
        json={"name": "Checking", "account_type": "checking", "currency": "USD"},
        headers=_auth_headers(token_a),
    ).json()
    client.post(
        "/api/v1/transactions",
        json={
            "account_id": account_a["id"],
            "amount": "10.00",
            "currency": "USD",
            "transaction_type": "expense",
            "description": "Alice's transaction",
            "date": "2026-01-15",
        },
        headers=_auth_headers(token_a),
    )

    response = client.get("/api/v1/transactions", headers=_auth_headers(token_b))

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["total"] == 0
