import re

def test_root_redirect(client):
    res = client.get("/", allow_redirects=False)
    assert res.status_code in (301, 302, 303, 307, 308)
    assert "/public/index.html" in res.headers.get("location", "")

def test_index_accessible(client):
    res = client.get("/public/index.html")
    assert res.status_code == 200
    assert "html" in res.text.lower()

def test_session_page_authenticated(client):
    res = client.get("/session")
    assert res.status_code == 200
    assert re.search(r"Panier|Catalogue", res.text, re.I)