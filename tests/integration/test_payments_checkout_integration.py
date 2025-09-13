def test_checkout_returns_url(client):
    # Le fixture _override_require_user fournit un user authentifié
    payload = {"items": [{"id": "X1", "quantity": 2}, {"id": "X2", "quantity": 1}]}
    res = client.post("/api/v1/payments/checkout", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "url" in data
    assert data["url"].startswith("https://example.test/checkout")