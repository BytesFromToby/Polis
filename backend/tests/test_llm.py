"""
tests/test_llm.py — Tests for the LLM integration layer.

Covers: StubLLMClient, PromptBuilder, ResponseParser, MemoryWriter, audiences flow.
All tests run without a real LLM connection.
"""
from __future__ import annotations

import json
import pytest
from unittest.mock import MagicMock, patch

from engine.models import (
    Faction, FactionTrait, Leader, Mayor, Deal, DealTerm, Domain, WorldState,
)
from engine.llm.client import LLMConfig, LLMClient, StubLLMClient, LLMError
from engine.llm.prompt_builder import PromptBuilder, TRAIT_SENTENCES, INTENSITY_PREFIX
from engine.llm.response_parser import ResponseParser, ParsedAudienceResponse
from engine.llm.memory import MemoryWriter, _trim_to_words


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _faction(
    fid="f1",
    name="The Guild",
    domain="trade",
    health=75,
    entrench=75,
    rating=2.0,
    traits=None,
):
    return Faction(
        id=fid,
        name=name,
        domain_primary=domain,
        health=health,
        entrench=entrench,
        rating=rating,
        leader=Leader(name="Elder Vane"),
        traits=traits or [],
    )


def _mayor():
    m = Mayor()
    m.set_reputation("f1", 10)
    return m


# ── StubLLMClient ────────────────────────────────────────────────────────────

class TestStubLLMClient:
    def test_step1_no_assistant_turns(self):
        stub = StubLLMClient()
        result = stub.complete("sys", [{"role": "user", "content": "hello"}])
        assert "audience" in result.lower() or len(result) > 0
        assert "<deal>" not in result

    def test_step3_one_assistant_turn(self):
        stub = StubLLMClient()
        msgs = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "opening"},
            {"role": "user", "content": "my offer"},
        ]
        result = stub.complete("sys", msgs)
        assert "<deal>" not in result

    def test_step5_two_assistant_turns_contains_deal(self):
        stub = StubLLMClient()
        msgs = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "opening"},
            {"role": "user", "content": "offer"},
            {"role": "assistant", "content": "counter"},
            {"role": "user", "content": "final"},
        ]
        result = stub.complete("sys", msgs)
        assert "<deal>" in result
        assert "</deal>" in result

    def test_stub_deal_is_valid_json(self):
        stub = StubLLMClient()
        msgs = [
            {"role": "user", "content": "x"},
            {"role": "assistant", "content": "a"},
            {"role": "user", "content": "y"},
            {"role": "assistant", "content": "b"},
            {"role": "user", "content": "z"},
        ]
        result = stub.complete("sys", msgs)
        import re
        m = re.search(r"<deal>\s*(.*?)\s*</deal>", result, re.DOTALL)
        assert m is not None
        data = json.loads(m.group(1))
        assert "accepted" in data
        assert "memory_note" in data


# ── LLMConfig ────────────────────────────────────────────────────────────────

class TestLLMConfig:
    def test_from_env_defaults_to_stub(self, monkeypatch):
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        cfg = LLMConfig.from_env()
        assert cfg.provider == "stub"

    def test_resolve_prefers_json(self):
        cfg_json = LLMConfig(provider="stub", model="test").to_json()
        cfg = LLMConfig.resolve(city_llm_json=cfg_json)
        assert cfg.model == "test"

    def test_resolve_falls_back_to_env(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "stub")
        monkeypatch.setenv("LLM_MODEL", "env-model")
        cfg = LLMConfig.resolve(city_llm_json=None)
        assert cfg.model == "env-model"

    def test_round_trip_json(self):
        original = LLMConfig(provider="anthropic", model="claude-3", api_key="key123")
        restored = LLMConfig.from_json(original.to_json())
        assert restored.provider == "anthropic"
        assert restored.model == "claude-3"
        assert restored.api_key == "key123"


# ── PromptBuilder ────────────────────────────────────────────────────────────

class TestPromptBuilder:
    def _build(self, faction=None, mayor=None, **kwargs):
        faction = faction or _faction()
        mayor = mayor or _mayor()
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        builder = PromptBuilder()
        return builder.build(
            faction=faction,
            run_id="run1",
            mayor=mayor,
            db=db,
            factions={"f1": faction},
            domains={},
            city_setting=kwargs.get("city_setting", "Greek"),
            city_name=kwargs.get("city_name", "Polis"),
            player_name=kwargs.get("player_name", "Kallisto"),
            player_title=kwargs.get("player_title", "Prytanis"),
        )

    def test_leader_name_in_prompt(self):
        prompt = self._build()
        assert "Elder Vane" in prompt

    def test_faction_name_in_prompt(self):
        prompt = self._build()
        assert "The Guild" in prompt

    def test_trait_sentence_in_prompt(self):
        f = _faction(traits=[FactionTrait("aggressive", "strong")])
        prompt = self._build(faction=f)
        assert "push hard for advantage" in prompt

    def test_intensity_prefix_applied(self):
        f = _faction(traits=[FactionTrait("aggressive", "very")])
        prompt = self._build(faction=f)
        assert "deeply convinced" in prompt.lower()

    def test_relational_trait_resolved(self):
        f2 = _faction(fid="f2", name="Rival Corp")
        f = _faction(traits=[FactionTrait("distrusts", "moderate", target_id="f2")])
        builder = PromptBuilder()
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        prompt = builder.build(
            faction=f, run_id="r", mayor=_mayor(), db=db,
            factions={"f1": f, "f2": f2}, domains={},
        )
        assert "Rival Corp" in prompt

    def test_health_narrative_present(self):
        f = _faction(health=20)
        prompt = self._build(faction=f)
        assert "crisis" in prompt.lower() or "fighting to survive" in prompt.lower()

    def test_canonical_briefing_injected(self):
        prompt = self._build(city_name="Athenai", player_name="Perikles", player_title="Strategos")
        # Identity substituted into the briefing
        assert "Athenai" in prompt
        assert "Perikles" in prompt
        assert "Strategos" in prompt
        # Briefing signatures present, and no blank leading tone line
        assert "bows to no king" in prompt
        assert "never a master" in prompt
        assert not prompt.startswith("\n")

    def test_setting_value_does_not_change_briefing(self):
        # Single canonical theme: SETTING_TONE is gone and any/no setting yields the briefing.
        import engine.llm.prompt_builder as pb
        assert not hasattr(pb, "SETTING_TONE")
        a = self._build(city_setting="DnD")
        b = self._build(city_setting="")
        assert "bows to no king" in a and "bows to no king" in b

    def test_no_mayor_wording_uses_title(self):
        prompt = self._build(player_title="Prytanis")
        assert "Mayor" not in prompt        # player-facing copy renamed to the title
        assert "Prytanis" in prompt

    def test_voice_line_sharpened(self):
        prompt = self._build()
        assert "measured, not verbose" not in prompt
        assert "sharp and vivid" in prompt   # brevity retained with edge
        assert "sentences" in prompt

    def test_no_real_llm_calls_made(self):
        # PromptBuilder is pure data transformation — verify it imports no LLM client
        import engine.llm.prompt_builder as pb
        assert not hasattr(pb, "LLMClient"), "PromptBuilder must not import LLMClient"
        self._build()  # should complete without network calls


# ── ResponseParser ────────────────────────────────────────────────────────────

class TestResponseParser:
    def _parse(self, text, faction=None, mayor=None):
        faction = faction or _faction()
        mayor = mayor or _mayor()
        return ResponseParser().parse(text, faction, mayor)

    def test_no_deal_block(self):
        result = self._parse("Just talking, no deal today.")
        assert result.accepted is False
        assert "no <deal> block" in result.parse_error

    def test_rejected_deal_accepted_false(self):
        text = (
            "Sorry, no agreement possible.\n\n"
            '<deal>\n{"accepted": false, "mayor_terms": [], "faction_terms": [], '
            '"rep_cost_if_broken_by_mayor": 15, "memory_note": "no deal reached", '
            '"reasoning": "test"}\n</deal>'
        )
        result = self._parse(text)
        assert result.accepted is False
        assert result.memory_note == "no deal reached"

    def test_accepted_deal_with_tax_exemption(self):
        text = (
            "We have an accord.\n\n"
            '<deal>\n{"accepted": true, '
            '"mayor_terms": [{"type": "tax_exemption", "action": "", "target_id": "", "duration": 3}], '
            '"faction_terms": [{"type": "committed_action", "action": "BuildProject", "target_id": "", "duration": 3}], '
            '"rep_cost_if_broken_by_mayor": 20, "memory_note": "deal agreed", '
            '"reasoning": "test"}\n</deal>'
        )
        result = self._parse(text)
        assert result.accepted is True
        assert len(result.mayor_terms) == 1
        assert result.mayor_terms[0].type == "tax_exemption"
        assert len(result.faction_terms) == 1
        assert result.faction_terms[0].action == "BuildProject"

    def test_invalid_committed_action_rejected(self):
        text = (
            "Deal reached.\n\n"
            '<deal>\n{"accepted": true, '
            '"mayor_terms": [], '
            '"faction_terms": [{"type": "committed_action", "action": "DestroyCity", "target_id": "", "duration": 2}], '
            '"rep_cost_if_broken_by_mayor": 20, "memory_note": "bad action", '
            '"reasoning": "test"}\n</deal>'
        )
        result = self._parse(text)
        assert result.accepted is False
        assert "invalid committed_action" in result.parse_error

    def test_rep_cost_clamped(self):
        text = (
            "Fine.\n\n"
            '<deal>\n{"accepted": false, "mayor_terms": [], "faction_terms": [], '
            '"rep_cost_if_broken_by_mayor": 999, "memory_note": "x", '
            '"reasoning": "test"}\n</deal>'
        )
        result = self._parse(text)
        assert result.rep_cost_if_broken == 35

    def test_domain_has_exemption_blocks_new_exemption(self):
        mayor = _mayor()
        mayor.exemptions["f2"] = 3  # f2 in same domain "trade" is already exempt
        f2 = _faction(fid="f2", domain="trade")
        faction = _faction(fid="f1", domain="trade")

        text = (
            "Deal reached.\n\n"
            '<deal>\n{"accepted": true, '
            '"mayor_terms": [{"type": "tax_exemption", "action": "", "target_id": "", "duration": 3}], '
            '"faction_terms": [], '
            '"rep_cost_if_broken_by_mayor": 20, "memory_note": "deal", '
            '"reasoning": "test"}\n</deal>'
        )
        # Need factions dict so parser can check domains — but parser only checks mayor.exemptions
        result = ResponseParser().parse(text, faction, mayor)
        assert result.accepted is False
        assert "domain already has an exempt faction" in result.parse_error

    def test_narrative_extracted(self):
        text = (
            "This is the narrative part.\n\n"
            '<deal>\n{"accepted": false, "mayor_terms": [], "faction_terms": [], '
            '"rep_cost_if_broken_by_mayor": 15, "memory_note": "done", '
            '"reasoning": "test"}\n</deal>'
        )
        result = self._parse(text)
        assert result.narrative == "This is the narrative part."

    def test_malformed_json_returns_no_deal(self):
        text = "<deal>\nnot valid json\n</deal>"
        result = self._parse(text)
        assert result.accepted is False
        assert "JSON decode error" in result.parse_error


# ── MemoryWriter ─────────────────────────────────────────────────────────────

class TestMemoryWriter:
    def _mock_db(self, existing_notes=None):
        from db.models import FactionMemory
        db = MagicMock()
        rows = existing_notes or []
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = rows
        return db

    def _make_row(self, note, cycle=1):
        row = MagicMock()
        row.note = note
        row.cycle = cycle
        return row

    def test_write_note_adds_row(self):
        db = self._mock_db(existing_notes=[])
        writer = MemoryWriter()
        writer.write_note("run1", "f1", 5, "dealt with mayor today", "audience", db)
        db.add.assert_called_once()
        db.flush.assert_called()

    def test_note_trimmed_to_10_words(self):
        assert _trim_to_words("one two three four five six seven eight nine ten eleven") == \
               "one two three four five six seven eight nine ten"

    def test_compression_triggered_at_max_notes(self):
        existing = [self._make_row(f"note {i}", i) for i in range(8)]
        db = self._mock_db(existing_notes=existing)
        writer = MemoryWriter()
        # Should trigger compression: delete 5 oldest, add summary, then add new note
        writer.write_note("run1", "f1", 10, "new note this cycle", "audience", db)
        # delete called for each of the 5 oldest
        assert db.delete.call_count == 5
        # add called twice: once for summary, once for new note
        assert db.add.call_count == 2

    def test_compression_fallback_on_no_llm(self):
        existing = [self._make_row(f"note {i}", i) for i in range(8)]
        db = self._mock_db(existing_notes=existing)
        writer = MemoryWriter()
        writer.write_note("run1", "f1", 10, "new", "audience", db, llm_client=None)
        # Summary row should use canned fallback text
        added_rows = [call.args[0] for call in db.add.call_args_list]
        summary_row = added_rows[0]
        assert "older interactions summary:" in summary_row.note


# ── Audiences (stub flow) ─────────────────────────────────────────────────────

class TestAudiencesStubFlow:
    """Run the full audience flow using StubLLMClient — no real LLM needed."""

    def _make_db(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        db.query.return_value.filter.return_value.first.return_value = None
        return db

    def test_stub_flow_completes(self):
        from engine.llm.audiences import run_audience
        faction = _faction()
        mayor = _mayor()
        db = self._make_db()
        cfg = LLMConfig(provider="stub")

        result = run_audience(
            faction=faction,
            mayor=mayor,
            run_id="run1",
            cycle=5,
            mayor_opening="I offer a tax exemption for three cycles.",
            mayor_closing="My final offer stands.",
            db=db,
            factions={"f1": faction},
            domains={},
            llm_config=cfg,
        )

        assert result.step1_narrative
        assert result.step3_narrative
        assert result.step5_narrative
        # Stub always rejects
        assert result.accepted is False
        assert result.memory_note  # always present

    def test_stub_memory_note_written(self):
        from engine.llm.audiences import run_audience
        faction = _faction()
        mayor = _mayor()
        db = self._make_db()
        cfg = LLMConfig(provider="stub")

        run_audience(
            faction=faction,
            mayor=mayor,
            run_id="run1",
            cycle=3,
            mayor_opening="offer",
            mayor_closing="final",
            db=db,
            factions={"f1": faction},
            domains={},
            llm_config=cfg,
        )
        # Memory note should have been written (db.add called at least once)
        assert db.add.called


# ── Serializer — Deal round-trip ─────────────────────────────────────────────

class TestDealSerializer:
    def test_deal_round_trip(self):
        from serializer import serialize_deal, deserialize_deal

        deal = Deal(
            id="d1",
            faction_id="f1",
            mayor_terms=[DealTerm(type="tax_exemption", duration=3)],
            faction_terms=[DealTerm(type="committed_action", action="BuildProject", duration=3)],
            cycles_remaining=3,
            total_duration=3,
            rep_cost_if_broken=25,
            cycle_created=5,
        )
        restored = deserialize_deal(serialize_deal(deal))
        assert restored.id == "d1"
        assert restored.faction_id == "f1"
        assert len(restored.mayor_terms) == 1
        assert restored.mayor_terms[0].type == "tax_exemption"
        assert restored.faction_terms[0].action == "BuildProject"
        assert restored.rep_cost_if_broken == 25

    def test_mayor_deals_round_trip(self):
        from serializer import serialize_mayor, deserialize_mayor

        mayor = _mayor()
        mayor.deals["d1"] = Deal(
            id="d1", faction_id="f1",
            mayor_terms=[], faction_terms=[],
            cycles_remaining=2, total_duration=5,
        )
        restored = deserialize_mayor(serialize_mayor(mayor))
        assert "d1" in restored.deals
        assert restored.deals["d1"].faction_id == "f1"

    def test_faction_committed_fields_round_trip(self):
        from serializer import serialize_faction, deserialize_faction

        f = _faction()
        f.committed_action = "BuildProject"
        f.committed_target = "proj1"
        f.committed_deal_id = "d1"

        restored = deserialize_faction(serialize_faction(f))
        assert restored.committed_action == "BuildProject"
        assert restored.committed_target == "proj1"
        assert restored.committed_deal_id == "d1"


# ── Behavior engine — committed_action override ───────────────────────────────

class TestCommittedActionOverride:
    def _factions(self):
        f1 = _faction(fid="f1")
        f2 = _faction(fid="f2", name="Rival", domain="trade")
        return {"f1": f1, "f2": f2}

    def test_committed_action_overrides_weights(self):
        from engine.npc.behavior import select_faction_action

        factions = self._factions()
        faction = factions["f1"]
        faction.committed_action = "Protect"

        # Run many times — should always return Protect
        for _ in range(30):
            plan = select_faction_action(faction, factions, {}, WorldState())
            assert plan.action == "Protect"

    def test_committed_abstain_excludes_target(self):
        from engine.npc.behavior import select_faction_action

        factions = self._factions()
        faction = factions["f1"]
        faction.committed_abstain_action = "Harm"
        faction.committed_abstain_target = "f2"
        # Give faction a very aggressive profile
        faction.traits = [FactionTrait("aggressive", "very"), FactionTrait("angry at", "very", target_id="f2")]

        # f2 is the only rival; with abstain, Harm cannot target f2 → should fall back to Grow
        hits_f2 = 0
        for _ in range(50):
            plan = select_faction_action(faction, factions, {}, WorldState())
            if plan.action == "Harm" and plan.target_id == "f2":
                hits_f2 += 1
        assert hits_f2 == 0
