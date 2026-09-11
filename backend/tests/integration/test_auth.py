def test_register_creates_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "ada@example.com", "password": "correcthorsebatterystaple"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "ada@example.com"
    assert "hashed_password" not in body  # never leak this out of the API


def test_register_rejects_duplicate_email(client):
    payload = {"email": "ada@example.com", "password": "correcthorsebatterystaple"}
    client.post("/api/v1/auth/register", json=payload)

    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 409


def test_login_returns_token_for_correct_credentials(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "ada@example.com", "password": "correcthorsebatterystaple"},
    )

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "ada@example.com", "password": "correcthorsebatterystaple"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_rejects_wrong_password(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "ada@example.com", "password": "correcthorsebatterystaple"},
    )

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "ada@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_login_rejects_unknown_email(client):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "nobody@example.com", "password": "whatever123"},
    )

    assert response.status_code == 401


def test_me_requires_authentication(client):
    response = client.get("/api/v1/users/me")

    assert response.status_code == 401


def test_me_returns_current_user_with_valid_token(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "ada@example.com", "password": "correcthorsebatterystaple"},
    )
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "ada@example.com", "password": "correcthorsebatterystaple"},
    )
    token = login.json()["access_token"]

    response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == "ada@example.com"
