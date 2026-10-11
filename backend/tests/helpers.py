def register_user(client, email: str) -> dict:
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
    assert resp.status_code == 201, resp.text
    return resp.json()


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
