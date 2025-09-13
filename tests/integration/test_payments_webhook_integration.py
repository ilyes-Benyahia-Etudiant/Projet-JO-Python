def test_webhook_completed_event(client):
    # Le parse_event est mocké pour retourner checkout.session.completed
    res = client.post("/api/v1/payments/webhook", json={"dummy": True})
    assert res.status_code == 200
    data = res.json()
    assert data.get("status") in ("ok", "ignored")