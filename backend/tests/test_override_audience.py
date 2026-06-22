"""
tests/test_override_audience.py — dev-mode OverrideLLM audience via the routes (override-llm_spec
slice 2). Drives audience_begin/reply/conclude/finalize against a hand-built in-memory SimSession
(mirrors test_audience_requires_ai), with POLIS_DEV_MODE toggled by monkeypatch.
"""
from __future__ import annotations

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.routes.mayor import audience_begin, audience_reply, audience_conclude, audience_finalize
from api.schemas import (AudienceBeginRequest, AudienceReplyRequest,
                         AudienceConcludeRequest, AudienceFinalizeRequest)
from api.sessions import SimSession, set_session, clear_session
from db.models import Base, User
from engine.models import WorldState, Faction, Leader, Mayor


@pytest.fixture()
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    yield sessionmaker(autocommit=False, autoflush=False, bind=engine)
    engine.dispose()


FAKE_USER = User(user_id="u1", username="tester", password_hash="x", is_gm=True)


def _session():
    faction = Faction(id="f1", name="The Tanners", domain_primary="guilds", rating=3.0,
                      leader=Leader(name="Tanner Elder"))
    s = SimSession(run_id="run1", world=WorldState(cycle=0, chaos={}), factions={"f1": faction},
                   domains={}, mayor=Mayor(action_points=3), llm_profile_id=None)
    set_session("u1", s)
    return s


def _drive(db, outcome):
    """begin(override) → reply → conclude(outcome). Returns the conclude response."""
    audience_begin("u1", AudienceBeginRequest(faction_id="f1", override=True), FAKE_USER, db)
    audience_reply("u1", AudienceReplyRequest(mayor_opening="Back me and I'll endorse you."), FAKE_USER, db)
    return audience_conclude(
        "u1", AudienceConcludeRequest(mayor_closing="Final offer.", override_outcome=outcome), FAKE_USER, db)


# ── Gating ────────────────────────────────────────────────────────────────────────

def test_override_rejected_without_dev_mode(test_db, monkeypatch):
    monkeypatch.delenv("POLIS_DEV_MODE", raising=False)
    _session()
    db = test_db()
    try:
        # No profile + override ignored (dev off) → the normal active-AI gate rejects.
        with pytest.raises(HTTPException) as exc:
            audience_begin("u1", AudienceBeginRequest(faction_id="f1", override=True), FAKE_USER, db)
        assert exc.value.status_code == 400
    finally:
        db.close(); clear_session("u1")


def test_override_begin_allowed_in_dev_mode(test_db, monkeypatch):
    monkeypatch.setenv("POLIS_DEV_MODE", "1")
    s = _session()
    db = test_db()
    try:
        resp = audience_begin("u1", AudienceBeginRequest(faction_id="f1", override=True), FAKE_USER, db)
        assert resp.action_points == 2                     # 1 AP spent — audience proceeded
        assert s.audience_state["llm_config"].provider == "override"
    finally:
        db.close(); clear_session("u1")


# ── Chosen outcome drives the deal ──────────────────────────────────────────────────

def test_chosen_accept_produces_proposed_terms(test_db, monkeypatch):
    monkeypatch.setenv("POLIS_DEV_MODE", "1")
    _session()
    db = test_db()
    try:
        outcome = {"accepted": True, "mayor_terms": [{"type": "endorsement"}],
                   "faction_terms": [{"type": "committed_action", "action": "Rally", "duration": 3}]}
        res = _drive(db, outcome)
        assert res.accepted is True and res.finalized is False   # faction accepts → awaits mayor confirm
        assert any(t["type"] == "committed_action" and t["action"] == "Rally"
                   for t in res.proposed_faction_terms)
        # Mayor confirms → the deal seals and the term binds the faction.
        fin = audience_finalize("u1", AudienceFinalizeRequest(mayor_accepts=True), FAKE_USER, db)
        assert fin.accepted is True
    finally:
        db.close(); clear_session("u1")


def test_chosen_reject_yields_no_deal(test_db, monkeypatch):
    monkeypatch.setenv("POLIS_DEV_MODE", "1")
    _session()
    db = test_db()
    try:
        res = _drive(db, {"accepted": False})
        assert res.accepted is False and res.finalized is True   # rejection is terminal
    finally:
        db.close(); clear_session("u1")
