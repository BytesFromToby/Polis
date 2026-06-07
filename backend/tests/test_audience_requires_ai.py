"""
tests/test_audience_requires_ai.py — Active-AI requirement for audiences (audience_spec v5).

An audience requires a valid active AI on the run. /mayor/audience/begin rejects with HTTP 400
and spends no action point when the run's llm_profile_id is unset, or set but not resolving to
an existing LLMProfile; it proceeds normally when a valid profile is set. The valid-profile case
uses a provider="stub" profile so the audience runs deterministically with no network call.

Drives the audience_begin route function directly against a hand-built in-memory SimSession, so
no City/SimRun seeding is needed (begin reads identity with defaults when the run row is absent).
"""
from __future__ import annotations

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.routes.mayor import audience_begin
from api.schemas import AudienceBeginRequest
from api.sessions import SimSession, set_session, clear_session
from db.models import Base, User, LLMProfile
from engine.models import WorldState, Faction, Leader, Mayor


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


FAKE_USER = User(user_id="u1", username="tester", password_hash="x", is_gm=True)


def _make_session(profile_id=None, action_points=3) -> SimSession:
    faction = Faction(
        id="f1", name="The Tanners", domain_primary="guilds",
        rating=3.0, leader=Leader(name="Tanner Elder"),
    )
    session = SimSession(
        run_id="run1",
        world=WorldState(cycle=0, chaos={}),
        factions={"f1": faction},
        domains={},
        mayor=Mayor(action_points=action_points),
        llm_profile_id=profile_id,
    )
    set_session("u1", session)
    return session


def _begin(db):
    return audience_begin(
        user_id="u1",
        req=AudienceBeginRequest(faction_id="f1"),
        current_user=FAKE_USER,
        db=db,
    )


def test_begin_rejected_when_no_profile(test_db):
    """llm_profile_id unset -> HTTP 400, no AP spent."""
    session = _make_session(profile_id=None, action_points=3)
    db = test_db()
    try:
        with pytest.raises(HTTPException) as exc:
            _begin(db)
        assert exc.value.status_code == 400
        assert session.mayor.action_points == 3   # no AP spent
    finally:
        db.close()
        clear_session("u1")


def test_begin_rejected_when_profile_missing(test_db):
    """llm_profile_id set but no matching profile row -> HTTP 400, no AP spent."""
    session = _make_session(profile_id="does-not-exist", action_points=3)
    db = test_db()
    try:
        with pytest.raises(HTTPException) as exc:
            _begin(db)
        assert exc.value.status_code == 400
        assert session.mayor.action_points == 3   # no AP spent
    finally:
        db.close()
        clear_session("u1")


def test_begin_proceeds_with_valid_profile(test_db):
    """A valid (stub-provider) profile -> audience proceeds, 1 AP spent, step-1 text returned."""
    db = test_db()
    try:
        profile = LLMProfile(name="Stub", provider="stub", model="stub", encrypted_api_key="")
        db.add(profile)
        db.commit()
        pid = profile.profile_id

        session = _make_session(profile_id=pid, action_points=3)
        resp = _begin(db)

        assert resp.action_points == 2            # one AP spent
        assert session.mayor.action_points == 2
        assert resp.step1_narrative.strip()       # stub produced opening text
    finally:
        db.close()
        clear_session("u1")
