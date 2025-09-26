# Top-level module edits in tests/unit/test_admin_repository.py
import pytest
from unittest.mock import MagicMock

import backend.admin.repository as repo

class _Resp:
    def __init__(self, data=None, count=None):
        self.data = data
        self.count = count

def _mk_client():
    client = MagicMock()
    table = MagicMock()
    select = MagicMock()
    single = MagicMock()
    execute = MagicMock()
    client.table.return_value = table
    table.select.return_value = select
    select.execute.return_value = _Resp()
    # pour update_user fallback
    table.select().single.return_value = single
    single.execute.return_value = _Resp(data={"id": "u1", "email": "x@y"})
    return client, table, select, single

def test_count_table_rows_with_count(monkeypatch):
    client, table, select, _ = _mk_client()
    select.execute.return_value = _Resp(count=7)
    monkeypatch.setattr("backend.admin.repository.get_service_supabase", lambda: client)
    assert repo.count_table_rows("users") == 7

def test_count_table_rows_without_count(monkeypatch):
    client, table, select, _ = _mk_client()
    select.execute.return_value = _Resp(data=[1,2,3])
    monkeypatch.setattr("backend.admin.repository.get_service_supabase", lambda: client)
    assert repo.count_table_rows("users") == 3

def test_count_table_rows_exception(monkeypatch):
    monkeypatch.setattr("backend.admin.repository.get_service_supabase", lambda: (_ for _ in ()).throw(Exception("boom")))
    assert repo.count_table_rows("users") == 0

def test_update_user_success(monkeypatch):
    client, table, select, single = _mk_client()
    # Première exécution renvoie un objet mis à jour
    select.execute.return_value = _Resp(data=[{"id": "u1", "email": "a@b"}])
    monkeypatch.setattr("backend.admin.repository.get_service_supabase", lambda: client)
    res = repo.update_user("u1", {"email": "a@b"})
    assert res == {"id": "u1", "email": "a@b"}

def test_update_user_fallback(monkeypatch):
    client, table, select, single = _mk_client()
    # Première exécution vide -> fallback lecture unique
    select.execute.return_value = _Resp(data=[])
    single.execute.return_value = _Resp(data={"id": "u1", "email": "final@x"})
    monkeypatch.setattr("backend.admin.repository.get_service_supabase", lambda: client)
    res = repo.update_user("u1", {"email": "final@x"})
    assert res == {"id": "u1", "email": "final@x"}

def test_delete_user_success(monkeypatch):
    client = MagicMock()
    table = MagicMock()
    client.table.return_value = table
    table.delete.return_value = table
    table.eq.return_value = table
    table.execute.return_value = _Resp()
    monkeypatch.setattr("backend.admin.repository.get_service_supabase", lambda: client)
    assert repo.delete_user("u1") is True

def test_delete_user_exception(monkeypatch):
    client = MagicMock()
    table = MagicMock()
    client.table.return_value = table
    table.delete.side_effect = Exception("boom")
    monkeypatch.setattr("backend.admin.repository.get_service_supabase", lambda: client)
    assert repo.delete_user("u1") is False


def _make_app():
    app = FastAPI()
    app.include_router(admin_views.router)
    # Override require_admin pour éviter la dépendance réelle
    app.dependency_overrides[require_admin] = lambda: {"id": "admin", "role": "admin", "email": "admin@example.com"}
    return app

def test_admin_stats_counts(monkeypatch):
    # count_table_rows est appelé pour users, commandes, offres
    def fake_count(table_name: str) -> int:
        return {"users": 7, "commandes": 4, "offres": 5}.get(table_name, 0)
    monkeypatch.setattr("backend.admin.repository.count_table_rows", fake_count)

    app = _make_app()
    client = TestClient(app)

    r = client.get("/admin/api/stats")
    assert r.status_code == 200
    assert r.json() == {"users_count": 7, "commandes_count": 4, "offres_count": 5}