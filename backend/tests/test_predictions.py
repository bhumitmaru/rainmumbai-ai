from tests.helpers import auth_header, register_user


def test_latest_prediction_has_disclaimer(client):
    data = register_user(client, "pred@example.com")
    token = data["access_token"]
    resp = client.get("/api/predictions/latest", headers=auth_header(token))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["direction"] in ("Increase", "No Change", "Decrease")
    probs = body["probabilities"]
    assert abs(probs["increase"] + probs["no_change"] + probs["decrease"] - 100.0) < 0.02
    assert "do not guarantee future outcomes" in body["disclaimer"].lower()
    assert body["confidence"]["overall"] >= 0


def test_history_returns_items(client):
    data = register_user(client, "hist@example.com")
    token = data["access_token"]
    resp = client.get("/api/predictions/history", headers=auth_header(token))
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert body["total"] >= 1
