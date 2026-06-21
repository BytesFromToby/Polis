"""
tests/test_sim_difficulty.py — Run-level difficulty (balance profile) persistence (balance_spec).

Mirrors test_sim_llm_profile.py: a difficulty chosen at /sim/start is stored on the SimRun,
defaults to "normal" when omitted, falls back to "normal" on an unknown value, and is restored
when a run is resumed via /sim/switch after the in-memory session is gone.
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


# ── Tests ───────────────────────────────────────────────────────────────────────

def test_start_persists_difficulty(client, test_db):
    s = test_db(); run_id = _seed_setup(s); s.close()

    assert client.post("/users/u1/sim/start", json={"difficulty": "hard"}).status_code == 200

    s2 = test_db()
    assert s2.query(SimRun).filter_by(run_id=run_id).first().difficulty == "hard"
    s2.close()
    assert client.get("/users/u1/sim/status").json()["difficulty"] == "hard"


def test_start_defaults_to_normal(client, test_db):
    s = test_db(); run_id = _seed_setup(s); s.close()

    assert client.post("/users/u1/sim/start", json={}).status_code == 200

    s2 = test_db()
    assert s2.query(SimRun).filter_by(run_id=run_id).first().difficulty == "normal"
    s2.close()


def test_unknown_difficulty_falls_back_to_normal(client, test_db):
    s = test_db(); _seed_setup(s); s.close()

    assert client.post("/users/u1/sim/start", json={"difficulty": "brutal"}).status_code == 200
    assert client.get("/users/u1/sim/status").json()["difficulty"] == "normal"


def test_switch_restores_difficulty_after_session_lost(client, test_db):
    s = test_db(); run_id = _seed_setup(s); s.close()

    client.post("/users/u1/sim/start", json={"difficulty": "easy"})
    client.post("/users/u1/sim/step")
    clear_session("u1")
    assert get_session("u1") is None

    r = client.post(f"/users/u1/sim/switch/{run_id}")
    assert r.status_code == 200
    assert r.json()["difficulty"] == "easy"
    assert get_session("u1").difficulty == "easy"
