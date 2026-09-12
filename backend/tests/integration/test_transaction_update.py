"""Covers a real bug: TransactionUpdate previously didn't accept
account_id/transaction_type at all (silently dropped by Pydantic), and
category_id's "is not None" check meant a category could never actually
be cleared once set, since None was ambiguous between "field omitted"
and "explicitly clear it". Fixed via exclude_unset — these tests pin
that fix in place.
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


def _create_account(client, token: str, name: str = "Checking") -> str:
    return client.post(
        "/api/v1/accounts",
        json={"name": name, "account_type": "checking", "currency": "USD"},
        headers=_auth_headers(token),
    ).json()["id"]


def _create_category(client, token: str, name: str) -> str:
    return client.post(
        "/api/v1/categories", json={"name": name}, headers=_auth_headers(token)
    ).json()["id"]


def test_explicit_null_category_id_clears_an_existing_category(client):
    token = _register_and_login(client, "alice@example.com")
    account = _create_account(client, token)
    category = _create_category(client, token, "Custom Category")

    txn = client.post(
        "/api/v1/transactions",
        json={
            "account_id": account,
            "category_id": category,
            "amount": "10.00",
            "currency": "USD",
            "transaction_type": "expense",
            "description": "Coffee",
            "date": "2026-01-15",
        },
        headers=_auth_headers(token),
    ).json()
    assert txn["category_id"] == category

    response = client.put(
        f"/api/v1/transactions/{txn['id']}",
        json={"category_id": None},
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["category_id"] is None


def test_account_id_and_transaction_type_can_be_updated(client):
    token = _register_and_login(client, "alice@example.com")
    account_a = _create_account(client, token, "Checking")
    account_b = _create_account(client, token, "Savings")

    txn = client.post(
        "/api/v1/transactions",
        json={
            "account_id": account_a,
            "amount": "10.00",
            "currency": "USD",
            "transaction_type": "expense",
            "description": "Refund",
            "date": "2026-01-15",
        },
        headers=_auth_headers(token),
    ).json()

    response = client.put(
        f"/api/v1/transactions/{txn['id']}",
        json={"account_id": account_b, "transaction_type": "income"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["account_id"] == account_b
    assert body["transaction_type"] == "income"


def test_cannot_reassign_a_transaction_to_another_users_account(client):
    token_a = _register_and_login(client, "alice@example.com")
    token_b = _register_and_login(client, "bob@example.com")
    account_a = _create_account(client, token_a)
    account_b = _create_account(client, token_b)

    txn = client.post(
        "/api/v1/transactions",
        json={
            "account_id": account_a,
            "amount": "10.00",
            "currency": "USD",
            "transaction_type": "expense",
            "description": "Coffee",
            "date": "2026-01-15",
        },
        headers=_auth_headers(token_a),
    ).json()

    response = client.put(
        f"/api/v1/transactions/{txn['id']}",
        json={"account_id": account_b},
        headers=_auth_headers(token_a),
    )

    assert response.status_code == 404


def test_partial_update_leaves_other_fields_untouched(client):
    token = _register_and_login(client, "alice@example.com")
    account = _create_account(client, token)

    txn = client.post(
        "/api/v1/transactions",
        json={
            "account_id": account,
            "amount": "10.00",
            "currency": "USD",
            "transaction_type": "expense",
            "description": "Coffee",
            "date": "2026-01-15",
        },
        headers=_auth_headers(token),
    ).json()

    response = client.put(
        f"/api/v1/transactions/{txn['id']}",
        json={"amount": "99.00"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["amount"] == "99.00"
    assert body["description"] == "Coffee"
    assert body["transaction_type"] == "expense"
