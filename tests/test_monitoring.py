def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"status": "ok"}
