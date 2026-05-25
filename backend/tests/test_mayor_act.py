"""
tests/test_mayor_act.py — Tests for the /mayor/act endpoint and underlying action logic.
"""
from __future__ import annotations

import pytest
from engine.models import Mayor, Treasury, Faction, Domain, FactionTrait, Leader, MayorAction
from engine.mayor.actions import execute_mayor_actions, ACTION_COSTS


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

    def test_two_ap_action_spends_two(self):
        m = _mayor(ap=4)
        result, m, *_ = _act("BrokerADeal", target="f1,f2", mayor=m,
                              factions={"f1": _faction("f1"), "f2": _faction("f2")})
        # BrokerADeal may fail (rep check) but AP always spent
        assert m.action_points == 2

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

    def test_broker_fails_without_rep(self):
        m = _mayor(ap=4)
        m.set_reputation("f1", 5)
        m.set_reputation("f2", 5)
        f = {"f1": _faction("f1"), "f2": _faction("f2")}
        result, *_ = _act("BrokerADeal", "f1,f2", mayor=m, factions=f)
        assert result.outcome == "fail"

    def test_broker_can_succeed_with_rep(self):
        import random
        random.seed(42)  # seed for deterministic roll
        m = _mayor(ap=4)
        m.set_reputation("f1", 20)
        m.set_reputation("f2", 20)
        f = {"f1": _faction("f1"), "f2": _faction("f2")}
        result, *_ = _act("BrokerADeal", "f1,f2", mayor=m, factions=f)
        # With rep=20, avg=20, d20+20 always exceeds DC 15
        assert result.outcome == "decisive"


# ── Resource actions ──────────────────────────────────────────────────────────

class TestResourceActions:
    def test_allocate_budget_adds_drift(self):
        m = _mayor()
        d = {"trade": _domain("trade")}
        d["trade"].drift = 0.5
        _act("AllocateBudget", "trade", mayor=m, domains=d)
        assert d["trade"].drift == pytest.approx(0.52)

    def test_allocate_budget_requires_gold(self):
        m = _mayor()
        t = _treasury(gold=5)
        result, *_ = _act("AllocateBudget", "trade", mayor=m, treasury=t)
        assert result.outcome == "fail"

    def test_withhold_blocks_growth(self):
        m = _mayor()
        f = {"f1": _faction()}
        _act("WithholdResources", "f1", mayor=m, factions=f)
        assert f["f1"]._growth_blocked is True

    def test_withhold_lowers_rep(self):
        m = _mayor()
        _act("WithholdResources", "f1", mayor=m)
        assert m.get_reputation("f1") == -10


# ── Authority actions ─────────────────────────────────────────────────────────

class TestAuthorityActions:
    def test_issue_decree_marks_domain(self):
        m = _mayor(ap=4)
        d = {"trade": _domain("trade")}
        _act("IssueADecree", "trade", mayor=m, domains=d)
        assert d["trade"]._decree_active is True

    def test_appoint_fails_if_has_leader(self):
        m = _mayor(ap=4)
        result, *_ = _act("AppointAnOfficial", "f1", mayor=m)
        assert result.outcome == "fail"

    def test_appoint_succeeds_if_leaderless(self):
        m = _mayor(ap=4)
        f = {"f1": _faction(leader=False)}
        result, _, factions, *_ = _act("AppointAnOfficial", "f1", mayor=m, factions=f)
        assert result.outcome == "decisive"
        assert factions["f1"].leader.status == "present"

    def test_blind_eye_marks_uncontested(self):
        m = _mayor()
        f = {"f1": _faction()}
        _act("TurnABlindEye", "f1", mayor=m, factions=f)
        assert f["f1"]._uncontested is True


# ── Information actions ───────────────────────────────────────────────────────

class TestInformationActions:
    def test_report_returns_no_op(self):
        result, *_ = _act("RequestAReport", "f1")
        assert result.outcome == "no_op"
        assert "traits" in result.narrative

    def test_plant_rumor_adds_trait(self):
        m = _mayor()
        f = {"f1": _faction("f1"), "f2": _faction("f2")}
        _act("PlantARumor", "f1,f2", mayor=m, factions=f)
        trait_ids = [t.trait for t in f["f1"].traits]
        assert "distrusts" in trait_ids

    def test_plant_rumor_escalates_existing_distrust(self):
        m = _mayor(ap=6)
        f = {"f1": _faction("f1"), "f2": _faction("f2")}
        f["f1"].traits.append(FactionTrait(trait="distrusts", intensity="slight", target_id="f2"))
        _act("PlantARumor", "f1,f2", mayor=m, factions=f)
        distrust = next(t for t in f["f1"].traits if t.trait == "distrusts" and t.target_id == "f2")
        assert distrust.intensity == "moderate"
