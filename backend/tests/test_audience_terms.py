"""
tests/test_audience_terms.py — Audience deal-term clarity + budget_allocation removal
(audience_spec.md v4, "Valid Deal Terms").

Pins: budget_allocation is no longer a live term; the prompt explains each term with correct
per-action targeting; the parser drops removed/unknown terms (keeping the rest) and strips
targets from untargeted committed_actions.
"""
from __future__ import annotations
from unittest.mock import MagicMock

from engine.models import Faction, Leader, Mayor
from engine.llm.prompt_builder import PromptBuilder
from engine.llm.response_parser import ResponseParser, VALID_TERM_TYPES, _STRING_TERM_MAP


def _faction(fid="f1"):
    return Faction(id=fid, name="The Guild", domain_primary="guilds", leader=Leader(name="Vane"))


def _mayor():
    m = Mayor()
    m.set_reputation("f1", 5)
    return m


def _build_prompt():
    f = _faction()
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
    return PromptBuilder().build(faction=f, run_id="r", mayor=_mayor(), db=db, factions={"f1": f}, domains={})


def _deal(mayor_terms_json: str, faction_terms_json: str) -> str:
    return (
        'Agreed.\n\n<deal>\n{"accepted": true, '
        f'"mayor_terms": [{mayor_terms_json}], '
        f'"faction_terms": [{faction_terms_json}], '
        '"rep_cost_if_broken_by_mayor": 20, "memory_note": "x", "reasoning": "y"}\n</deal>'
    )


# (a) budget_allocation is no longer a live term
def test_budget_allocation_not_a_live_term():
    assert "budget_allocation" not in VALID_TERM_TYPES
    assert "budget_allocation" not in _STRING_TERM_MAP
    assert "budget_allocation" not in _build_prompt()


# (b) the prompt explains each term
def test_prompt_explains_each_term():
    p = _build_prompt()
    assert "Grow" in p
    assert "Protect" in p and "ALL" in p          # "less Harm from ALL rivals"
    assert "BuildProject" in p and "Workshop" in p   # the guilds faction's own buildable, named
    assert "endorsement" in p.lower()
    assert "Refrain" in p                          # committed_abstain, plain language


# (b3) the prompt names the faction's OWN buildable + targets it by domain id
# (audience_spec.md — BuildProject buildable info)
def test_prompt_names_own_buildable_and_domain_target():
    from engine.projects import base_project_description
    p = _build_prompt()                            # faction: domain_primary="guilds" → "Workshop"
    assert "Workshop" in p
    assert base_project_description("guilds") in p
    # BuildProject <deal> target is the faction's domain id, not a free-text project id
    build_line = next(l for l in p.split("\n") if '"BuildProject"' in l)
    assert '"target_id": "guilds"' in build_line
    assert "<a project id>" not in p
    assert "dock_expansion" not in p
    # only the faction's own buildable appears — not other domains' base projects
    assert "Docks" not in p and "Barracks" not in p


# (b2) tax exemption is shelved — the prompt offers only endorsement (audience_spec.md; record in archive/)
def test_prompt_offers_only_endorsement():
    p = _build_prompt()
    assert "endorsement" in p.lower()
    assert "tax exemption" not in p.lower()
    assert "tax_exemption" not in p.lower()
    # the <deal> schema's mayor_terms explanation line offers endorsement, not tax_exemption
    mayor_terms_line = next(l for l in p.split("\n") if '("mayor_terms")' in l)
    assert "endorsement" in mayor_terms_line
    assert "tax_exemption" not in mayor_terms_line


# (c) target_id is shown only for BuildProject and committed_abstain
def test_target_id_only_where_real():
    lines = _build_prompt().split("\n")

    def line_with(sub):
        return next(l for l in lines if sub in l)

    assert "target_id" not in line_with('"action": "Grow"')
    assert "target_id" not in line_with('"action": "Protect"')
    assert "target_id" in line_with('"action": "BuildProject"')
    assert "target_id" in line_with("committed_abstain")


# (d) parser clears target on untargeted committed_actions, keeps it for BuildProject
def test_parser_target_guard():
    parser, f, m = ResponseParser(), _faction(), _mayor()

    r_protect = parser.parse(
        _deal('{"type": "endorsement"}',
              '{"type": "committed_action", "action": "Protect", "target_id": "f2", "duration": 4}'),
        f, m,
    )
    assert r_protect.accepted
    assert r_protect.faction_terms[0].target_id == ""

    r_grow = parser.parse(
        _deal('{"type": "endorsement"}',
              '{"type": "committed_action", "action": "Grow", "target_id": "f2", "duration": 4}'),
        f, m,
    )
    assert r_grow.faction_terms[0].target_id == ""

    r_build = parser.parse(
        _deal('{"type": "endorsement"}',
              '{"type": "committed_action", "action": "BuildProject", "target_id": "dock", "duration": 4}'),
        f, m,
    )
    assert r_build.accepted
    assert r_build.faction_terms[0].target_id == "dock"


# (g) Toil — chain-role gating, needs line, parser target guard (audience_spec v5.1)
def _build_prompt_for(fid, domain, public=None):
    from engine.models import ThePublic
    from loaders import load_chains
    f = Faction(id=fid, name=fid.title(), domain_primary=domain, leader=Leader(name="X"), rating=2.0)
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
    m = Mayor()
    m.set_reputation(fid, 5)
    return PromptBuilder().build(
        faction=f, run_id="r", mayor=m, db=db, factions={fid: f}, domains={},
        public=public or ThePublic(), chains=load_chains(),
    )


def test_toil_offered_only_to_chain_role_factions():
    p_oven = _build_prompt_for("ovenmen", "guilds")
    assert "Toil" in p_oven
    assert '"action": "Toil"' in p_oven

    p_temple = _build_prompt_for("tidesworn", "temples")
    assert "Toil" not in p_temple


def test_prompt_contains_needs_line():
    from engine.models import ThePublic
    p = _build_prompt_for("ovenmen", "guilds", public=ThePublic(fed=80, happy=10, health=100))
    assert "The people are Well fed" in p
    assert "Miserable" in p


def test_prompt_without_public_has_no_needs_line():
    assert "The people are" not in _build_prompt()


def test_toil_schema_line_untargeted():
    p = _build_prompt_for("ovenmen", "guilds")
    toil_line = next(l for l in p.split("\n") if '"action": "Toil"' in l)
    assert "target_id" not in toil_line


def test_parser_clears_toil_target():
    parser, f, m = ResponseParser(), _faction(), _mayor()
    r = parser.parse(
        _deal('{"type": "endorsement"}',
              '{"type": "committed_action", "action": "Toil", "target_id": "f2", "duration": 4}'),
        f, m,
    )
    assert r.accepted
    assert r.faction_terms[0].action == "Toil"
    assert r.faction_terms[0].target_id == ""


# (e) a removed term bundled with a valid one is dropped; the deal still seals
def test_budget_term_dropped_deal_seals():
    parser, f, m = ResponseParser(), _faction(), _mayor()
    r = parser.parse(
        _deal('{"type": "tax_exemption", "duration": 4}, {"type": "budget_allocation", "duration": 3}',
              '{"type": "committed_action", "action": "Grow", "duration": 4}'),
        f, m,
    )
    assert r.accepted
    assert len(r.mayor_terms) == 1
    assert r.mayor_terms[0].type == "tax_exemption"


# (f) a deal whose only Mayor term is budget_allocation collapses to no-deal (one-sided)
def test_only_budget_term_no_deal():
    parser, f, m = ResponseParser(), _faction(), _mayor()
    r = parser.parse(
        _deal('{"type": "budget_allocation", "duration": 3}',
              '{"type": "committed_action", "action": "Grow", "duration": 4}'),
        f, m,
    )
    assert not r.accepted
    assert "one side committed nothing" in r.parse_error
