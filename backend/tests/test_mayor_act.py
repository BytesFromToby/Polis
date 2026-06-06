"""
tests/test_mayor_act.py — Tests for the /mayor/act endpoint and underlying action logic.
"""
from __future__ import annotations

import pytest
from engine.models import Mayor, Treasury, Faction, Domain, FactionTrait, Leader, MayorAction, Project
from engine.mayor.actions import execute_mayor_actions, ACTION_COSTS, _ACTION_MAP
from engine.projects import mayor_build_or_repair
from api.schemas import VALID_MAYOR_ACTIONS


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _mayor(ap=4):
    m = Mayor()
    m.action_points = ap
    return m


def _treasury(gold=500):
    return Treasury(gold=gold)


def _faction(fid="f1", name="The Guild", domain="trade", health=75, leader=True):
    return Faction(
        id=fid, name=name, domain_primary=domain, health=health,
        leader=Leader(name="Elder") if leader else Leader(name="Elder", status="absent"),
    )


def _domain(did="trade"):
    return Domain(id=did, name=did, cap=100)


def _act(action, target="f1", mayor=None, factions=None, domains=None, treasury=None):
    m = mayor or _mayor()
    f = factions or {"f1": _faction()}
    d = domains or {"trade": _domain()}
    t = treasury or _treasury()
    ma = MayorAction(action=action, target_id=target, cost=ACTION_COSTS.get(action, 1))
    results = execute_mayor_actions([ma], m, t, f, d)
    return results[0], m, f, d, t


# ── AP spending ───────────────────────────────────────────────────────────────

class TestAPSpending:
    def test_action_spends_ap(self):
        m = _mayor(ap=4)
        result, m, *_ = _act("PubliclyEndorse", mayor=m)
        assert m.action_points == 3

    def test_insufficient_ap_returns_fail(self):
        m = _mayor(ap=0)
        result, *_ = _act("PubliclyEndorse", mayor=m)
        assert result.outcome == "fail"
        assert "Insufficient" in result.narrative


# ── Political actions ─────────────────────────────────────────────────────────

class TestPoliticalActions:
    def test_endorse_raises_rep(self):
        m = _mayor()
        _act("PubliclyEndorse", "f1", mayor=m)
        assert m.get_reputation("f1") == 10

    def test_endorse_lowers_domain_peers(self):
        m = _mayor(ap=6)
        f = {"f1": _faction("f1", domain="trade"), "f2": _faction("f2", domain="trade")}
        _act("PubliclyEndorse", "f1", mayor=m, factions=f)
        assert m.get_reputation("f2") == -3

    def test_condemn_lowers_rep(self):
        m = _mayor()
        _act("PubliclyCondemn", "f1", mayor=m)
        assert m.get_reputation("f1") == -15

    def test_meet_sets_cooldown(self):
        m = _mayor()
        _act("MeetWithFaction", "f1", mayor=m)
        assert "f1" in m.cooldowns

    def test_meet_fails_on_cooldown(self):
        m = _mayor(ap=6)
        m.cooldowns["f1"] = 5
        result, *_ = _act("MeetWithFaction", "f1", mayor=m)
        assert result.outcome == "fail"


# ── Roster integrity ───────────────────────────────────────────────────────────

DEMO_ROSTER = {
    "MeetWithFaction", "PubliclyEndorse", "PubliclyCondemn",
    "GrantTaxExemption", "Sabotage", "BuildProject", "BreakADeal",
}
REMOVED_ACTIONS = {
    "BrokerADeal", "AllocateBudget", "WithholdResources", "IssueADecree",
    "AppointAnOfficial", "TurnABlindEye", "RequestAReport", "PlantARumor",
}


class TestRosterIntegrity:
    def test_valid_actions_is_exact_demo_set(self):
        assert VALID_MAYOR_ACTIONS == DEMO_ROSTER

    def test_removed_actions_absent(self):
        for name in REMOVED_ACTIONS:
            assert name not in VALID_MAYOR_ACTIONS
            assert name not in _ACTION_MAP


# ── Sabotage ────────────────────────────────────────────────────────────────

def _rated(fid="f1", rating=3.5, health=100, domain="trade"):
    return Faction(id=fid, name=fid, domain_primary=domain, rating=rating,
                   health=health, leader=Leader(name="Elder"))


class TestSabotage:
    def test_cost_deducts_ap_and_gold(self):
        m = _mayor(ap=4)
        t = _treasury(gold=500)
        result, m, *_rest, t = _act("Sabotage", "f1", mayor=m,
                                     factions={"f1": _rated()}, treasury=t)
        assert result.outcome == "decisive"
        assert m.action_points == 3
        assert t.gold == 450

    def test_insufficient_gold_refunds_ap_no_deduction(self):
        m = _mayor(ap=4)
        t = _treasury(gold=10)
        result, m, *_rest, t = _act("Sabotage", "f1", mayor=m,
                                    factions={"f1": _rated()}, treasury=t)
        assert result.outcome == "fail"
        assert m.action_points == 4   # AP refunded
        assert t.gold == 10           # nothing deducted

    def test_rank_erodes_fractional_margin(self):
        _, _, f, *_ = _act("Sabotage", "f1", factions={"f1": _rated(rating=3.50)})
        assert f["f1"].rating == pytest.approx(3.25)
        # integer-rating faction loses no rank
        _, _, f2, *_ = _act("Sabotage", "f1", factions={"f1": _rated(rating=3.00)})
        assert f2["f1"].rating == pytest.approx(3.00)

    def test_health_halved(self):
        _, _, f, *_ = _act("Sabotage", "f1", factions={"f1": _rated(health=100)})
        assert f["f1"].health == 50
        _, _, f2, *_ = _act("Sabotage", "f1", factions={"f1": _rated(health=50)})
        assert f2["f1"].health == 25

    def test_single_sabotage_cannot_break_or_delevel(self):
        _, _, f, *_ = _act("Sabotage", "f1", factions={"f1": _rated(rating=3.50, health=40)})
        assert f["f1"].level == 3      # still level 3 (3.25)
        assert f["f1"].health > 0      # 40 -> 20, never 0

    def test_reputation_minus_ten(self):
        m = _mayor(ap=4)
        result, m, *_ = _act("Sabotage", "f1", mayor=m, factions={"f1": _rated()})
        assert m.get_reputation("f1") == -10

    def test_level_one_target_allowed(self):
        result, _, f, *_ = _act("Sabotage", "f1", factions={"f1": _rated(rating=1.40, health=80)})
        assert result.outcome == "decisive"   # not refused on safe-floor grounds
        assert f["f1"].health == 40            # 80 -> 40


# ── Build Project (context-aware) ──────────────────────────────────────────────

def _base_project(progress=1, status="under_construction", health=0, domain="trade"):
    return Project(
        id=f"{domain}_base_1", name="Agora", domains=[domain], build_cost=0,
        build_time=4, category="base", status=status,
        build_progress=progress, health=health, initiated_by="mayor",
    )


class TestBuildProject:
    def test_initiates_when_none_under_construction(self):
        m = _mayor(ap=4); t = _treasury(gold=500); projects = {}
        r = mayor_build_or_repair("trade", projects, t, m)
        assert r.outcome != "fail"
        base = [p for p in projects.values() if p.category == "base" and "trade" in p.domains]
        assert len(base) == 1
        assert base[0].status == "under_construction"
        assert base[0].build_progress == 1
        assert t.gold == 450 and m.action_points == 3

    def test_adds_unit_when_under_construction(self):
        m = _mayor(ap=4); t = _treasury(gold=500)
        projects = {"trade_base_1": _base_project(progress=1)}
        mayor_build_or_repair("trade", projects, t, m)
        assert projects["trade_base_1"].build_progress == 2
        assert t.gold == 450 and m.action_points == 3

    def test_fourth_unit_completes(self):
        m = _mayor(ap=4); t = _treasury(gold=500)
        projects = {"trade_base_1": _base_project(progress=3)}
        mayor_build_or_repair("trade", projects, t, m)
        assert projects["trade_base_1"].status == "active"
        assert projects["trade_base_1"].health == 100

    def test_repairs_active_damaged(self):
        m = _mayor(ap=4); t = _treasury(gold=500)
        projects = {"trade_base_1": _base_project(progress=4, status="active", health=60)}
        r = mayor_build_or_repair("trade", projects, t, m)
        assert r.outcome != "fail"
        assert projects["trade_base_1"].health == 85   # +25
        assert t.gold == 470 and m.action_points == 3   # repair costs 30

    def test_insufficient_funds_refunds(self):
        # No AP -> refused, nothing changes
        m = _mayor(ap=0); t = _treasury(gold=500); projects = {}
        r = mayor_build_or_repair("trade", projects, t, m)
        assert r.outcome == "fail"
        assert t.gold == 500 and m.action_points == 0 and projects == {}
        # Has AP but not enough gold -> refused, AP refunded, nothing deducted
        m2 = _mayor(ap=2); t2 = _treasury(gold=10); projects2 = {}
        r2 = mayor_build_or_repair("trade", projects2, t2, m2)
        assert r2.outcome == "fail"
        assert t2.gold == 10 and m2.action_points == 2
