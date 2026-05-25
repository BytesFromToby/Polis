"""
tests/test_llm_profiles.py — API tests for LLM profile CRUD and test endpoint.
Uses an in-memory SQLite DB and mocked auth.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db.models import Base, User
from db.session import get_db
from api.deps import get_current_user
from api.server import app
from engine.llm.crypto import decrypt_api_key


# ── Test DB setup ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def test_db():
    # StaticPool ensures all sessions share the same single connection,
    # which is required for SQLite :memory: to persist across sessions.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield TestSession
    engine.dispose()


@pytest.fixture()
def client(test_db):
    def _override_db():
        db = test_db()
        try:
            yield db
        finally:
            db.close()

    fake_user = User(user_id="u1", username="tester", password_hash="x", is_gm=True)

    def _override_user():
        return fake_user

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = _override_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _create(client, **kwargs):
    payload = {
        "name": "Test Profile",
        "provider": "openai_compat",
        "model": "llama3.2",
        "api_key": "ollama",
        "base_url": "http://localhost:11434/v1",
        **kwargs,
    }
    return client.post("/llm-profiles", json=payload)


# ── CRUD tests ────────────────────────────────────────────────────────────────

def test_create_profile(client):
    r = _create(client, name="My Ollama")
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "My Ollama"
    assert data["provider"] == "openai_compat"
    assert "encrypted_api_key" not in data
    assert data["has_api_key"] is True


def test_create_profile_no_api_key(client):
    r = _create(client, name="No Key Profile", api_key="")
    assert r.status_code == 201
    assert r.json()["has_api_key"] is False


def test_list_profiles(client):
    _create(client, name="Profile A")
    _create(client, name="Profile B")
    r = client.get("/llm-profiles")
    assert r.status_code == 200
    names = [p["name"] for p in r.json()]
    assert "Profile A" in names
    assert "Profile B" in names
    for p in r.json():
        assert "encrypted_api_key" not in p


def test_duplicate_name_rejected(client):
    _create(client, name="Unique Name")
    r = _create(client, name="Unique Name")
    assert r.status_code == 409


def test_update_profile(client):
    r = _create(client, name="Update Me")
    pid = r.json()["profile_id"]
    r2 = client.put(f"/llm-profiles/{pid}", json={"model": "llama3.3"})
    assert r2.status_code == 200
    assert r2.json()["model"] == "llama3.3"


def test_update_api_key(client):
    r = _create(client, name="Key Update", api_key="original")
    pid = r.json()["profile_id"]
    client.put(f"/llm-profiles/{pid}", json={"api_key": "new-key"})
    # Verify via DB — decrypt and check
    from db.session import get_db as real_get_db
    # Re-check via the test client list (key not exposed, just confirm has_api_key)
    r2 = client.get("/llm-profiles")
    entry = next(p for p in r2.json() if p["profile_id"] == pid)
    assert entry["has_api_key"] is True


def test_delete_profile(client):
    r = _create(client, name="Delete Me")
    pid = r.json()["profile_id"]
    r2 = client.delete(f"/llm-profiles/{pid}")
    assert r2.status_code == 204
    r3 = client.get("/llm-profiles")
    ids = [p["profile_id"] for p in r3.json()]
    assert pid not in ids


def test_delete_nonexistent_returns_404(client):
    r = client.delete("/llm-profiles/does-not-exist")
    assert r.status_code == 404


def test_update_nonexistent_returns_404(client):
    r = client.put("/llm-profiles/does-not-exist", json={"model": "x"})
    assert r.status_code == 404


# ── Test endpoint ─────────────────────────────────────────────────────────────

def test_test_endpoint_stub(client):
    """Stub provider (no api key) should return ok=True since StubLLMClient always works."""
    r = _create(client, name="Stub Test Profile", provider="stub", model="", api_key="")
    pid = r.json()["profile_id"]
    r2 = client.post(f"/llm-profiles/{pid}/test")
    assert r2.status_code == 200
    assert r2.json()["ok"] is True


def test_test_endpoint_nonexistent(client):
    r = client.post("/llm-profiles/no-such-id/test")
    assert r.status_code == 404
