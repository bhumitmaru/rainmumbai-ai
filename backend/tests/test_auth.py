from tests.helpers import auth_header, register_user


def test_register_login_me_logout(client):
    email = "auth1@example.com"
    data = register_user(client, email)
    token = data["access_token"]
    assert data["user"]["email"] == email

    me = client.get("/api/auth/me", headers=auth_header(token))
    assert me.status_code == 200
    assert me.json()["email"] == email

    # Logout revokes the token.
    out = client.post("/api/auth/logout", headers=auth_header(token))
    assert out.status_code == 200
    revoked = client.get("/api/auth/me", headers=auth_header(token))
    assert revoked.status_code == 401


def test_register_duplicate_rejected(client):
    email = "auth2@example.com"
    register_user(client, email)
    resp = client.post(
        "/api/auth/register",
        json={
            "full_name": "Test User",
            "email": email,
            "contact_number": "9876543210",
            "password": "password123",
            "confirm_password": "password123",
        },
    )
    assert resp.status_code == 409


def test_login_wrong_password(client):
    register_user(client, "auth3@example.com")
    resp = client.post("/api/auth/login", json={"email": "auth3@example.com", "password": "wrong-password"})
    assert resp.status_code == 401


def test_protected_requires_token(client):
    assert client.get("/api/predictions/latest").status_code == 401
