"""
tests/test_audience_finalize.py — v3 Mayor-confirmation flow for audiences.

Covers audience_spec.md Done-when items:
- conclude no longer creates a deal when the faction accepts (deferred to finalize)
- finalize(mayor_accepts=True) creates the deal + applies terms
- finalize(mayor_accepts=False) creates no deal but still sets the cooldown
- faction-decline finalises inside conclude (no deal, memory written, cooldown set)
- a memory note is written in every finalised branch

All run without a real LLM. The accept path is driven by patching the LLM call to
return an accepting <deal>, and by building a parsed result via ResponseParser.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from engine.models import Faction, Leader, Mayor
from engine.llm.client import LLMConfig
from engine.llm.response_parser import ResponseParser
from engine.llm import audiences


_ACCEPT_TEXT = (
    "Very well, Mayor. We have an accord.\n\n"
    "<deal>\n"
    '{"accepted": true, '
    '"mayor_terms": [{"type": "tax_exemption", "duration": 4}], '
    '"faction_terms": [{"type": "committed_action", "action": "Grow", "duration": 4}], '
    '"rep_cost_if_broken_by_mayor": 20, '
    '"memory_note": "tax break for support", "reasoning": "x"}\n'
    "</deal>"
)

_REJECT_TEXT = (
    "No, Mayor. We will not be bought.\n\n"
    "<deal>\n"
    '{"accepted": false, "mayor_terms": [], "faction_terms": [], '
    '"rep_cost_if_broken_by_mayor": 20, "memory_note": "rebuffed the mayor", "reasoning": "x"}\n'
    "</deal>"
)


def _faction(fid="f1"):
    return Faction(
        id=fid, name="The Guild", domain_primary="trade",
        health=75, entrench=75, rating=2.0, leader=Leader(name="Elder Vane"),
    )


def _mayor():
    m = Mayor()
    m.set_reputation("f1", 10)
    return m


def _mock_db():
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
    db.query.return_value.filter.return_value.first.return_value = None
    return db


def _state(parsed=None):
    return {
        "llm_config": LLMConfig(provider="stub"),
        "system": "sys",
        "messages": [
            {"role": "user", "content": "The Mayor requests an audience."},
            {"role": "assistant", "content": "opening"},
            {"role": "user", "content": "my opening"},
            {"role": "assistant", "content": "counter"},
        ],
        "step1_narrative": "opening",
        "step3_narrative": "counter",
        **({"pending_parsed": parsed} if parsed is not None else {}),
    }


# ── conclude defers on accept ──────────────────────────────────────────────────

def test_conclude_does_not_commit_on_faction_accept():
    faction, mayor, db = _faction(), _mayor(), _mock_db()
    state = _state()
    with patch.object(audiences, "_call", return_value=_ACCEPT_TEXT):
        result = audiences.conclude_audience_step(
            state=state, mayor_closing="final",
            faction=faction, mayor=mayor, run_id="run1", cycle=5, db=db,
        )
    assert result.accepted is True
    assert result.finalized is False
    assert result.deal_id is None
    assert mayor.deals == {}          # no deal created at conclude
    assert "f1" not in mayor.cooldowns  # cooldown not set until finalize
    assert state["pending_parsed"].accepted is True  # stashed for finalize


# ── finalize accept / decline ───────────────────────────────────────────────────

def test_finalize_accept_creates_deal_and_applies_terms():
    faction, mayor, db = _faction(), _mayor(), _mock_db()
    parsed = ResponseParser().parse(_ACCEPT_TEXT, faction, mayor)
    state = _state(parsed)

    result = audiences.finalize_audience(
        state=state, mayor_accepts=True,
        faction=faction, mayor=mayor, run_id="run1", cycle=5, db=db,
    )
    assert result.accepted is True
    assert result.deal_id is not None
    assert len(mayor.deals) == 1
    assert mayor.exemptions.get("f1") == 4          # mayor term applied
    assert faction.committed_action == "Grow"        # faction term applied
    assert "f1" in mayor.cooldowns
    assert db.add.called                             # memory note written


def test_finalize_decline_creates_no_deal_but_sets_cooldown():
    faction, mayor, db = _faction(), _mayor(), _mock_db()
    parsed = ResponseParser().parse(_ACCEPT_TEXT, faction, mayor)
    state = _state(parsed)

    result = audiences.finalize_audience(
        state=state, mayor_accepts=False,
        faction=faction, mayor=mayor, run_id="run1", cycle=5, db=db,
    )
    assert result.accepted is False
    assert result.deal_id is None
    assert mayor.deals == {}
    assert mayor.exemptions == {}
    assert faction.committed_action == ""
    assert "f1" in mayor.cooldowns                   # cooldown still set
    assert db.add.called                             # memory note written


# ── faction decline finalises inside conclude ───────────────────────────────────

def test_faction_decline_finalises_in_conclude():
    faction, mayor, db = _faction(), _mayor(), _mock_db()
    state = _state()
    with patch.object(audiences, "_call", return_value=_REJECT_TEXT):
        result = audiences.conclude_audience_step(
            state=state, mayor_closing="final",
            faction=faction, mayor=mayor, run_id="run1", cycle=5, db=db,
        )
    assert result.accepted is False
    assert result.finalized is True
    assert mayor.deals == {}
    assert "f1" in mayor.cooldowns
    assert db.add.called                             # memory note written


# ── memory note in every finalised branch ───────────────────────────────────────

def test_memory_note_written_in_every_branch():
    # accept-confirmed
    f1, m1, db1 = _faction(), _mayor(), _mock_db()
    audiences.finalize_audience(
        state=_state(ResponseParser().parse(_ACCEPT_TEXT, f1, m1)),
        mayor_accepts=True, faction=f1, mayor=m1, run_id="r", cycle=1, db=db1,
    )
    # accept-declined
    f2, m2, db2 = _faction(), _mayor(), _mock_db()
    audiences.finalize_audience(
        state=_state(ResponseParser().parse(_ACCEPT_TEXT, f2, m2)),
        mayor_accepts=False, faction=f2, mayor=m2, run_id="r", cycle=1, db=db2,
    )
    # faction-declined (via conclude)
    f3, m3, db3 = _faction(), _mayor(), _mock_db()
    with patch.object(audiences, "_call", return_value=_REJECT_TEXT):
        audiences.conclude_audience_step(
            state=_state(), mayor_closing="final",
            faction=f3, mayor=m3, run_id="r", cycle=1, db=db3,
        )
    assert db1.add.called and db2.add.called and db3.add.called


# ── one-sided deals are rejected ────────────────────────────────────────────────

def test_accept_with_empty_faction_terms_is_rejected():
    faction, mayor = _faction(), _mayor()
    text = (
        "Agreed.\n\n"
        "<deal>\n"
        '{"accepted": true, '
        '"mayor_terms": [{"type": "endorsement"}], '
        '"faction_terms": [], '
        '"rep_cost_if_broken_by_mayor": 20, "memory_note": "one-sided", "reasoning": "x"}\n'
        "</deal>"
    )
    parsed = ResponseParser().parse(text, faction, mayor)
    assert parsed.accepted is False
    assert "one side committed nothing" in parsed.parse_error


# ── debug payload ───────────────────────────────────────────────────────────────

def test_debug_payload_captured_each_step():
    faction, mayor, db = _faction(), _mayor(), _mock_db()
    cfg = LLMConfig(provider="stub")

    state = audiences.begin_audience_step(
        faction=faction, mayor=mayor, run_id="run1", cycle=5, db=db,
        factions={"f1": faction}, domains={}, llm_config=cfg,
    )
    begin_dbg = state["debug_begin"]
    assert begin_dbg["system"]                       # non-empty system prompt
    assert isinstance(begin_dbg["messages"], list) and begin_dbg["messages"]
    assert begin_dbg["raw_response"]

    state = audiences.reply_audience_step(state=state, mayor_opening="my offer")
    assert state["debug_reply"]["raw_response"]

    result = audiences.conclude_audience_step(
        state=state, mayor_closing="final",
        faction=faction, mayor=mayor, run_id="run1", cycle=5, db=db,
    )
    conclude_dbg = state["debug_conclude"]
    # Step 5 raw response is the unparsed text including the <deal> block …
    assert "<deal>" in conclude_dbg["raw_response"]
    # … distinct from the narrative shown to the player.
    assert "<deal>" not in result.step5_narrative
