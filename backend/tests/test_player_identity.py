"""
tests/test_player_identity.py — Player Identity feature (player-identity_spec.md).

Slice 1: identity capture & persistence — a started run carries player_name /
player_title (defaulting Kallisto / Prytanis), blank inputs fall back to defaults,
and the city name persists. Uses an in-memory SQLite DB and mocked auth.
"""
from __future__ import annotations
import json
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db.models import Base, City, SimRun
from db.session import get_db
from api.deps import get_current_user
from api.server import app
from db.models import User
from engine.models import WorldState
from serializer import serialize_world_state


# ── Test DB setup (mirrors test_llm_profiles) ──────────────────────────────────

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

    def _override_user():
        return fake_user

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = _override_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Helpers ─────────────────────────────────────────────────────────────────────

def _seed_setup(session, city_name="Polis") -> tuple[str, str]:
    """Insert a minimal City + a status='setup' SimRun for user u1. Returns (city_id, run_id)."""
    city = City(
        city_name=city_name, author="tester", setting="Greek",
        is_official=False, published=False, owner_id="u1",
        domains_json="{}", factions_json="{}",
        world_state_json=json.dumps(
            serialize_world_state(WorldState(cycle=0, chaos={}))
        ),
    )
    session.add(city)
    session.flush()
    run = SimRun(user_id="u1", city_id=city.city_id, status="setup", setting="Greek")
    session.add(run)
    session.commit()
    return city.city_id, run.run_id


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_start_defaults_identity(client, test_db):
    """(a) Starting with no player fields → Kallisto / Prytanis."""
    s = test_db()
    _, run_id = _seed_setup(s)
    s.close()

    r = client.post("/users/u1/sim/start", json={})
    assert r.status_code == 200

    s2 = test_db()
    run = s2.query(SimRun).filter_by(run_id=run_id).first()
    assert run.player_name == "Kallisto"
    assert run.player_title == "Prytanis"
    s2.close()


def test_start_custom_name_and_city(client, test_db):
    """(b) Editing both fields → entered player name + city name persist."""
    s = test_db()
    city_id, run_id = _seed_setup(s)
    s.close()

    rp = client.patch("/users/u1/city", json={"city_name": "Megara"})
    assert rp.status_code == 200

    r = client.post("/users/u1/sim/start", json={"player_name": "Theron"})
    assert r.status_code == 200

    s2 = test_db()
    run = s2.query(SimRun).filter_by(run_id=run_id).first()
    city = s2.query(City).filter_by(city_id=city_id).first()
    assert run.player_name == "Theron"
    assert run.player_title == "Prytanis"   # title not supplied → default
    assert city.city_name == "Megara"
    s2.close()


def test_start_blank_name_falls_back(client, test_db):
    """(c) Blank/whitespace player name → default Kallisto."""
    s = test_db()
    _, run_id = _seed_setup(s)
    s.close()

    r = client.post("/users/u1/sim/start", json={"player_name": "   "})
    assert r.status_code == 200

    s2 = test_db()
    run = s2.query(SimRun).filter_by(run_id=run_id).first()
    assert run.player_name == "Kallisto"
    s2.close()


def test_identity_persists_in_fresh_session(client, test_db):
    """(d) Round-trip: values read back via a fresh DB session are unchanged."""
    s = test_db()
    city_id, run_id = _seed_setup(s)
    s.close()

    client.patch("/users/u1/city", json={"city_name": "Syrakousai"})
    client.post("/users/u1/sim/start", json={"player_name": "Hipparete", "player_title": "Archon"})

    fresh = test_db()
    run = fresh.query(SimRun).filter_by(run_id=run_id).first()
    city = fresh.query(City).filter_by(city_id=city_id).first()
    assert (run.player_name, run.player_title) == ("Hipparete", "Archon")
    assert city.city_name == "Syrakousai"
    fresh.close()


# ── Slice 3: identity threaded into the audience prompt ─────────────────────────

def _engine_faction():
    from engine.models import Faction, Leader
    return Faction(
        id="f1", name="The Guild", domain_primary="trade",
        health=75, rating=2.0, leader=Leader(name="Elder Vane"),
    )


def _engine_mock_db():
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
    db.query.return_value.filter.return_value.first.return_value = None
    return db


def test_begin_audience_threads_identity_into_prompt():
    """begin_audience_step forwards city/player/title into the built system prompt."""
    from engine.llm import audiences
    from engine.llm.client import LLMConfig
    from engine.models import Mayor

    faction, mayor, db = _engine_faction(), Mayor(), _engine_mock_db()
    state = audiences.begin_audience_step(
        faction=faction, mayor=mayor, run_id="r", cycle=1, db=db,
        factions={"f1": faction}, domains={},
        city_name="Megara", player_name="Theron", player_title="Archon",
        llm_config=LLMConfig(provider="stub"),
    )
    system = state["debug_begin"]["system"]
    assert "Megara" in system
    assert "Theron" in system
    assert "Archon" in system
    assert "Mayor" not in system   # renamed to the title


def test_stub_audience_still_parses_after_rename():
    """A full stub audience still yields a parseable conclusion (deal contract intact)."""
    from engine.llm import audiences
    from engine.llm.client import LLMConfig
    from engine.models import Mayor

    faction, mayor, db = _engine_faction(), Mayor(), _engine_mock_db()
    state = audiences.begin_audience_step(
        faction=faction, mayor=mayor, run_id="r", cycle=1, db=db,
        factions={"f1": faction}, domains={}, llm_config=LLMConfig(provider="stub"),
    )
    state = audiences.reply_audience_step(state=state, mayor_opening="my offer")
    result = audiences.conclude_audience_step(
        state=state, mayor_closing="final",
        faction=faction, mayor=mayor, run_id="r", cycle=1, db=db,
    )
    assert result.parse_error == ""
    assert result.finalized is True
    assert "<deal>" in state["debug_conclude"]["raw_response"]


def test_get_audience_identity_reads_run(test_db):
    """The route helper returns the run's player name/title and the city's name."""
    from api.routes.mayor import _get_audience_identity

    s = test_db()
    city = City(
        city_name="Korinthos", author="t", setting="Greek",
        is_official=False, published=False, owner_id="u1",
        domains_json="{}", factions_json="{}", world_state_json="{}",
    )
    s.add(city)
    s.flush()
    run = SimRun(
        user_id="u1", city_id=city.city_id, status="running",
        player_name="Solon", player_title="Archon",
    )
    s.add(run)
    s.commit()

    fake_session = MagicMock()
    fake_session.run_id = run.run_id
    assert _get_audience_identity(fake_session, s) == ("Korinthos", "Solon", "Archon")
    s.close()
