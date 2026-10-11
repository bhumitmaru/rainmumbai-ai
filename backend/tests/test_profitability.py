from tests.helpers import auth_header, register_user


def test_profitability_structure(client):
    data = register_user(client, "profit@example.com")
    token = data["access_token"]
    resp = client.get("/api/profitability", headers=auth_header(token))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["decision_rule"] == "directional"
    assert body["lots"] == 1
    assert "do not guarantee future outcomes" in body["disclaimer"].lower()


def test_performance_structure(client):
    data = register_user(client, "perf@example.com")
    token = data["access_token"]
    resp = client.get("/api/performance", headers=auth_header(token))
    assert resp.status_code == 200
    body = resp.json()
    assert "mae" in body and "rmse" in body
    assert "sample_count" in body
    assert "baseline" in body
    assert "error_series" in body
    assert "cumulative_accuracy_series" in body
    assert isinstance(body["evaluation_runs"], list)
    assert isinstance(body["samples"], list)
