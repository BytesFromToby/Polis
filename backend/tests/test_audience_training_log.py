"""
tests/test_audience_training_log.py — the audience training log writer
(audience_spec.md — Training Log). Drives log_audience directly with a hand-built state.
"""
from __future__ import annotations
import json
from types import SimpleNamespace

from engine.llm.audience_log import log_audience


def _faction():
    return SimpleNamespace(
        id="f1", name="The Tanners", domain_primary="guilds",
        traits=[SimpleNamespace(trait="industrious"), SimpleNamespace(trait="ambitious")],
    )


def _state(provider="anthropic"):
    return {
        "system": "You are the leader of The Tanners...",
        "messages": [
            {"role": "assistant", "content": "STEP1 opening"},
            {"role": "user", "content": "MAYOR OPENING"},
            {"role": "assistant", "content": "STEP3 response"},
        ],
        "step1_narrative": "STEP1 opening",
        "step3_narrative": "STEP3 response",
        "mayor_closing": "MAYOR CLOSING",
        "step5_raw": 'STEP5 closing\n<deal>{"accepted": false}</deal>',
        "pending_parsed": SimpleNamespace(
            accepted=False, narrative="STEP5 closing",
            mayor_terms=[], faction_terms=[], memory_note="no deal",
        ),
        "llm_config": SimpleNamespace(provider=provider, model="claude-sonnet-4-6"),
    }


def _read(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_live_audience_writes_one_wellformed_record(tmp_path):
    p = tmp_path / "audiences.jsonl"
    assert log_audience(_state(), _faction(), "run1", 7, "accepted_confirmed", path=str(p)) is True
    records = _read(p)
    assert len(records) == 1
    r = records[0]
    for key in ("schema_version", "timestamp", "run_id", "cycle", "provider", "model",
                "faction", "system_prompt", "turns", "step5_raw", "parsed_deal", "outcome"):
        assert key in r, f"missing key {key}"
    assert r["run_id"] == "run1" and r["cycle"] == 7
    assert r["faction"]["traits"] == ["industrious", "ambitious"]


def test_stub_audience_writes_nothing(tmp_path):
    p = tmp_path / "audiences.jsonl"
    assert log_audience(_state(provider="stub"), _faction(), "run1", 1, "faction_declined", path=str(p)) is False
    assert not p.exists()


def test_turns_order_and_content(tmp_path):
    p = tmp_path / "audiences.jsonl"
    log_audience(_state(), _faction(), "run1", 1, "faction_declined", path=str(p))
    turns = _read(p)[0]["turns"]
    assert [(t["role"], t["step"]) for t in turns] == [
        ("faction", 1), ("mayor", 2), ("faction", 3), ("mayor", 4), ("faction", 5)]
    assert turns[0]["text"] == "STEP1 opening"
    assert turns[1]["text"] == "MAYOR OPENING"
    assert turns[2]["text"] == "STEP3 response"
    assert turns[3]["text"] == "MAYOR CLOSING"
    assert turns[4]["text"] == "STEP5 closing"


def test_step5_raw_distinct_from_parsed_deal(tmp_path):
    p = tmp_path / "audiences.jsonl"
    log_audience(_state(), _faction(), "run1", 1, "faction_declined", path=str(p))
    r = _read(p)[0]
    assert "<deal>" in r["step5_raw"]
    assert r["step5_raw"] != json.dumps(r["parsed_deal"])
    assert r["parsed_deal"]["accepted"] is False


def test_provider_model_present_no_secrets(tmp_path):
    p = tmp_path / "audiences.jsonl"
    log_audience(_state(), _faction(), "run1", 1, "accepted_confirmed", path=str(p))
    line = p.read_text(encoding="utf-8")
    r = json.loads(line)
    assert r["provider"] == "anthropic" and r["model"] == "claude-sonnet-4-6"
    for secret in ("api_key", "encrypted_api_key", "base_url"):
        assert secret not in line


def test_outcome_value_round_trips(tmp_path):
    for outcome in ("faction_declined", "accepted_confirmed", "accepted_mayor_declined"):
        p = tmp_path / f"{outcome}.jsonl"
        log_audience(_state(), _faction(), "run1", 1, outcome, path=str(p))
        assert _read(p)[0]["outcome"] == outcome


# ── Call-site wiring (routes invoke log_audience with the right outcome) ────────
# Monkeypatch the engine step functions (canned results — no LLM/DB) and spy on
# log_audience to assert the conclude/finalize routes wire the correct outcome.

import engine.llm.audiences as audiences_mod
import api.routes.mayor as mayor_mod
from api.routes.mayor import audience_conclude, audience_finalize
from api.schemas import AudienceConcludeRequest, AudienceFinalizeRequest
from api.sessions import SimSession, set_session, clear_session
from engine.models import WorldState, Mayor, Faction, Leader
from db.models import User


def _session_with_state():
    faction = Faction(id="f1", name="The Tanners", domain_primary="guilds",
                      rating=3.0, leader=Leader(name="Elder"))
    session = SimSession(
        run_id="run1", world=WorldState(cycle=4), factions={"f1": faction},
        domains={}, mayor=Mayor(action_points=3),
    )
    session.audience_state = {
        "faction_id": "f1",
        "llm_config": SimpleNamespace(provider="anthropic", model="claude-sonnet-4-6"),
        "system": "sys", "messages": [{"role": "user", "content": "m1"}],
        "step1_narrative": "s1", "step3_narrative": "s3", "mayor_closing": "m2",
        "step5_raw": "<deal>{}</deal>",
        "pending_parsed": SimpleNamespace(accepted=True, narrative="s5",
                                          mayor_terms=[], faction_terms=[], memory_note="n"),
    }
    set_session("u1", session)
    return session


_USER = User(user_id="u1", username="t", password_hash="x", is_gm=True)


def _fake_conclude_result():
    return SimpleNamespace(step1_narrative="s1", step3_narrative="s3", step5_narrative="s5",
                           accepted=False, finalized=True, mayor_terms=[], faction_terms=[],
                           deal_id=None, memory_note="n", parse_error="")


def _fake_finalize_result():
    return SimpleNamespace(accepted=True, deal_id=None, memory_note="n")


def test_conclude_logs_faction_declined(monkeypatch):
    _session_with_state()
    spy = {}
    monkeypatch.setattr(audiences_mod, "conclude_audience_step", lambda **k: _fake_conclude_result())
    monkeypatch.setattr(mayor_mod, "log_audience",
                        lambda *a, **k: spy.update(outcome=k.get("outcome")))
    try:
        audience_conclude("u1", AudienceConcludeRequest(mayor_closing="m2"), _USER, None)
        assert spy.get("outcome") == "faction_declined"
    finally:
        clear_session("u1")


def test_finalize_logs_accepted_outcomes(monkeypatch):
    monkeypatch.setattr(audiences_mod, "finalize_audience", lambda **k: _fake_finalize_result())
    for accepts, expected in ((True, "accepted_confirmed"), (False, "accepted_mayor_declined")):
        _session_with_state()
        spy = {}
        monkeypatch.setattr(mayor_mod, "log_audience",
                            lambda *a, **k: spy.update(outcome=k.get("outcome")))
        try:
            audience_finalize("u1", AudienceFinalizeRequest(mayor_accepts=accepts), _USER, None)
            assert spy.get("outcome") == expected
        finally:
            clear_session("u1")
