"""
tests/test_sim_llm_profile.py — Run-level LLM profile persistence (llm-profiles_spec.md).

Covers the "loading a run keeps its own AI setting" Done-when item: a profile chosen
at /sim/start is stored on the SimRun, and resuming via /sim/switch restores it from the
DB even after the in-memory session is gone. Uses in-memory SQLite + mocked auth.
"""
from __future__ import annotations
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db.models import Base, City, SimRun, User
from db.session import get_db
from api.deps import get_current_user
from api.server import app
from api.sessions import get_session, clear_session
from engine.models import WorldState
from serializer import serialize_world_state


# ── Test DB setup (mirrors test_player_identity) ────────────────────────────────

@pytest.fixture()
def test_db():
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

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = lambda: fake_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    clear_session("u1")


def _seed_setup(session) -> str:
    """Insert a minimal City + status='setup' SimRun for user u1. Returns run_id."""
    city = City(
        city_name="Polis", author="tester", setting="Greek",
        is_official=False, published=False, owner_id="u1",
        domains_json="{}", factions_json="{}",
        world_state_json=json.dumps(serialize_world_state(WorldState(cycle=0, chaos={}))),
    )
    session.add(city)
    session.flush()
    run = SimRun(user_id="u1", city_id=city.city_id, status="setup", setting="Greek")
    session.add(run)
    session.commit()
    return run.run_id


def _make_profile(client) -> str:
    r = client.post("/llm-profiles", json={
        "name": "Switch Test", "provider": "openai_compat", "model": "llama3.2",
        "api_key": "", "base_url": "http://localhost:11434/v1",
    })
    assert r.status_code == 201
    return r.json()["profile_id"]


# ── Tests ───────────────────────────────────────────────────────────────────────

def test_start_persists_profile_on_run(client, test_db):
    """A profile passed to /sim/start is stored on the SimRun and reported by status."""
    s = test_db(); run_id = _seed_setup(s); s.close()
    pid = _make_profile(client)

    r = client.post("/users/u1/sim/start", json={"llm_profile_id": pid})
    assert r.status_code == 200

    s2 = test_db()
    run = s2.query(SimRun).filter_by(run_id=run_id).first()
    assert run.llm_profile_id == pid
    s2.close()

    assert client.get("/users/u1/sim/status").json()["llm_profile_id"] == pid


def test_start_without_profile_is_stub(client, test_db):
    """No profile → run is stub mode (llm_profile_id is null)."""
    s = test_db(); run_id = _seed_setup(s); s.close()

    assert client.post("/users/u1/sim/start", json={}).status_code == 200

    s2 = test_db()
    assert s2.query(SimRun).filter_by(run_id=run_id).first().llm_profile_id is None
    s2.close()


def test_switch_restores_profile_after_session_lost(client, test_db):
    """Resuming via /sim/switch restores the run's own profile from the DB even when
    the in-memory session has been dropped (simulating a fresh process)."""
    s = test_db(); run_id = _seed_setup(s); s.close()
    pid = _make_profile(client)

    client.post("/users/u1/sim/start", json={"llm_profile_id": pid})
    client.post("/users/u1/sim/step")          # snapshot at cycle 1
    clear_session("u1")                          # in-memory session gone
    assert get_session("u1") is None

    r = client.post(f"/users/u1/sim/switch/{run_id}")
    assert r.status_code == 200
    assert r.json()["llm_profile_id"] == pid
    assert get_session("u1").llm_profile_id == pid
