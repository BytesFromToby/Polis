"""Tests for the OverrideLLM provider — deterministic "choose the outcome" audiences.

Spec: override-llm_spec.md (slice 1). The override client synthesises operator-supplied audience
output so the audience flow + ResponseParser are unchanged.
"""
from engine.llm.client import LLMClient, LLMConfig, OverrideLLMClient
from engine.llm.response_parser import ResponseParser
from engine.llm.audiences import _apply_faction_terms
from engine.models import Faction, Leader, Mayor


def mk_faction(fid="a"):
    return Faction(id=fid, name=fid.title(), domain_primary="trade", leader=Leader(name="L"), rating=4.0)


def conclude_messages():
    """A message list with two assistant turns → the override emits its conclude (<deal>) output."""
    return [
        {"role": "user", "content": "open"},
        {"role": "assistant", "content": "a1"},
        {"role": "user", "content": "offer"},
        {"role": "assistant", "content": "a2"},
        {"role": "user", "content": "closing"},
    ]


RALLY = {"type": "committed_action", "action": "Rally", "duration": 3}
ENDORSE = {"type": "endorsement"}  # a mayor term — the parser requires both sides to commit


# ── Provider routing / no network ─────────────────────────────────────────────────

def test_override_routes_with_no_network_config():
    # No base_url, no api_key — override never touches the network and must still build + run.
    client = LLMClient(LLMConfig(provider="override", override={"accepted": True, "faction_terms": [RALLY]}))
    assert isinstance(client._client, OverrideLLMClient)
    assert client.complete("sys", []) != ""                         # opening turn works
    assert "<deal>" in client.complete("sys", conclude_messages())  # conclude emits a deal


def test_steps_progress_by_turn():
    c = OverrideLLMClient({"narratives": {"open": "OPEN", "counter": "COUNTER", "conclude": "DONE"}})
    assert c.complete("s", []) == "OPEN"
    assert c.complete("s", [{"role": "user", "content": "x"}, {"role": "assistant", "content": "y"}]) == "COUNTER"
    assert c.complete("s", conclude_messages()).startswith("DONE")


# ── Outcome → parseable deal ──────────────────────────────────────────────────────

def test_accepted_outcome_parses_to_supplied_terms():
    client = LLMClient(LLMConfig(provider="override", override={
        "accepted": True, "mayor_terms": [{"type": "endorsement"}], "faction_terms": [RALLY],
    }))
    parsed = ResponseParser().parse(client.complete("s", conclude_messages()), mk_faction(), Mayor())
    assert parsed.parse_error == "" and parsed.accepted is True
    assert [(t.type, t.action, t.duration) for t in parsed.faction_terms] == [("committed_action", "Rally", 3)]
    assert [t.type for t in parsed.mayor_terms] == ["endorsement"]


def test_reject_outcome_has_empty_terms():
    client = LLMClient(LLMConfig(provider="override", override={"accepted": False, "faction_terms": [RALLY]}))
    parsed = ResponseParser().parse(client.complete("s", conclude_messages()), mk_faction(), Mayor())
    assert parsed.accepted is False
    assert parsed.faction_terms == [] and parsed.mayor_terms == []


def test_abstain_outcome_supported():
    abstain = {"type": "committed_abstain", "action": "Agitate", "duration": 4}
    client = LLMClient(LLMConfig(provider="override", override={
        "accepted": True, "mayor_terms": [ENDORSE], "faction_terms": [abstain]}))
    parsed = ResponseParser().parse(client.complete("s", conclude_messages()), mk_faction(), Mayor())
    assert any(t.type == "committed_abstain" and t.action == "Agitate" for t in parsed.faction_terms)


# ── Effect application ────────────────────────────────────────────────────────────

def test_chosen_deal_effects_apply():
    client = LLMClient(LLMConfig(provider="override", override={
        "accepted": True, "mayor_terms": [ENDORSE], "faction_terms": [RALLY]}))
    faction = mk_faction()
    parsed = ResponseParser().parse(client.complete("s", conclude_messages()), faction, Mayor())
    _apply_faction_terms(parsed, faction)
    assert faction.committed_action == "Rally"


# ── Counts as a usable (non-stub) AI ──────────────────────────────────────────────

def test_override_is_not_stub():
    cfg = LLMConfig(provider="override", override={
        "accepted": True, "mayor_terms": [ENDORSE], "faction_terms": [RALLY]})
    assert cfg.provider != "stub"
    # The override path produces a real, parseable conclusion (a stub always rejects).
    parsed = ResponseParser().parse(LLMClient(cfg).complete("s", conclude_messages()), mk_faction(), Mayor())
    assert parsed.accepted is True
