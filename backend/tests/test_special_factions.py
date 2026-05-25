"""Tests for special factions — The Public, Moneylender, External Threats."""
import pytest
from engine.models import (
    ThePublic, Faction, FactionTrait, Leader,
    Treasury, Mayor, ExternalThreat, ThreatEffect, WorldState, Domain,
)
from engine.special.public import process_the_public
from engine.special.moneylender import process_moneylender
from engine.special.external_threats import process_external_threats, make_bandit_threat
from engine.cycle.runner import run_cycle


def make_faction(fid="f1", domain="trade", floor=2, rating=2.0, health=75):
    return Faction(id=fid, name=fid, domain_primary=domain, leader=Leader(name="Test"), floor=floor, rating=rating, health=health)


def make_mayor(**kw):
    return Mayor(**kw)


def make_treasury(**kw):
    return Treasury(**kw)


# ── The Public ────────────────────────────────────────────────────────────────

class TestThePublic:
    def test_disposition_content(self):
        public = ThePublic(support=25)
        public.update_disposition()
        assert public.disposition == "content"

    def test_disposition_neutral(self):
        public = ThePublic(support=0)
        public.update_disposition()
        assert public.disposition == "neutral"

    def test_disposition_restless(self):
        public = ThePublic(support=-25)
        public.update_disposition()
        assert public.disposition == "restless"

    def test_disposition_angry(self):
        public = ThePublic(support=-40)
        public.update_disposition()
        assert public.disposition == "angry"

    def test_support_syncs_from_mayor_reputation(self):
        public = ThePublic(support=0)
        mayor = make_mayor()
        mayor.set_reputation("the_public", 30)
        process_the_public(public, mayor, {}, [])
        assert public.support == 30

    def test_restless_disposition_adds_distrusts_trait(self):
        public = ThePublic(support=-25)
        mayor = make_mayor(reputation={"the_public": -25})
        process_the_public(public, mayor, {}, [])
        distrusts = [t for t in public.traits if t.trait == "distrusts" and t.target_id == "mayor"]
        assert len(distrusts) == 1

    def test_angry_disposition_adds_angry_at_trait(self):
        public = ThePublic(support=-40)
        mayor = make_mayor(reputation={"the_public": -40})
        process_the_public(public, mayor, {}, [])
        angry = [t for t in public.traits if t.trait == "angry at" and t.target_id == "mayor"]
        assert len(angry) == 1

    def test_content_removes_negative_traits(self):
        public = ThePublic(support=30)
        public.traits = [
            FactionTrait(trait="distrusts", intensity="moderate", target_id="mayor"),
            FactionTrait(trait="angry at", intensity="slight", target_id="mayor"),
        ]
        mayor = make_mayor(reputation={"the_public": 30})
        process_the_public(public, mayor, {}, [])
        negative = [t for t in public.traits if t.trait in ("distrusts", "angry at")]
        assert len(negative) == 0

    def test_angry_disposition_triggers_removal_risk(self):
        public = ThePublic(support=-40)
        mayor = make_mayor(reputation={"the_public": -40})
        results = process_the_public(public, mayor, {}, [])
        removal = [r for r in results if r.action == "RemovalRisk"]
        assert len(removal) == 1


# ── Moneylender ───────────────────────────────────────────────────────────────

class TestMoneylender:
    def test_no_debt_no_effects(self):
        treasury = make_treasury(debt=0)
        mayor = make_mayor()
        results = process_moneylender(treasury, mayor, {})
        assert results == []

    def test_leverage_active_above_500_debt(self):
        treasury = make_treasury(debt=600)
        mayor = make_mayor()
        factions = {"moneylender": make_faction("moneylender")}
        results = process_moneylender(treasury, mayor, factions)
        leverage = [r for r in results if r.action == "MoneylenderLeverage"]
        assert len(leverage) == 1

    def test_leverage_adds_steal_bonus_to_moneylender_faction(self):
        treasury = make_treasury(debt=600)
        mayor = make_mayor()
        ml_faction = make_faction("moneylender")
        process_moneylender(treasury, mayor, {"moneylender": ml_faction})
        assert getattr(ml_faction, "_leverage_steal_bonus", 0) == 10

    def test_above_800_debt_adds_angry_at_mayor_trait(self):
        treasury = make_treasury(debt=900)
        mayor = make_mayor()
        ml_faction = make_faction("moneylender")
        results = process_moneylender(treasury, mayor, {"moneylender": ml_faction})
        angry = [t for t in ml_faction.traits if t.trait == "angry at" and t.target_id == "mayor"]
        assert len(angry) == 1

    def test_removal_countdown_triggers_after_grace_period(self):
        treasury = make_treasury(debt=900)
        mayor = make_mayor()
        factions = {"moneylender": make_faction("moneylender")}
        countdown = [5]  # start with 5 cycles remaining

        # Tick down to 0
        for _ in range(5):
            countdown[0] -= 1

        countdown = [0]
        results = process_moneylender(treasury, mayor, factions, removal_countdown=countdown)
        removal = [r for r in results if r.action == "MayorRemovalAttempt"]
        assert len(removal) == 1


# ── External Threats ──────────────────────────────────────────────────────────

class TestExternalThreats:
    def test_bandit_threat_adds_chaos(self):
        threat = make_bandit_threat(threat_level=2)
        world = WorldState()
        world.chaos = {"street": 0.0}
        treasury = make_treasury(gold=500)
        mayor = make_mayor()
        process_external_threats([threat], {}, {"street": Domain(id="street", name="street", cap=100)},
                                  world, treasury, mayor)
        assert world.chaos["street"] > 0

    def test_threat_reduces_treasury(self):
        threat = make_bandit_threat(threat_level=2)
        world = WorldState()
        world.chaos = {"street": 0.0}
        treasury = make_treasury(gold=500)
        mayor = make_mayor()
        process_external_threats([threat], {}, {}, world, treasury, mayor)
        # -5 gold per cycle * threat_level 2 = -10
        assert treasury.gold == 490

    def test_timed_threat_expires(self):
        threat = make_bandit_threat(threat_level=1, duration=1)
        world = WorldState()
        world.chaos = {}
        treasury = make_treasury(gold=500)
        mayor = make_mayor()
        results = process_external_threats([threat], {}, {}, world, treasury, mayor)
        expired = [r for r in results if r.action == "ThreatExpired"]
        assert len(expired) == 1
        assert not threat.active

    def test_indefinite_threat_stays_active(self):
        threat = make_bandit_threat(threat_level=1, duration=0)  # 0 = indefinite
        world = WorldState()
        world.chaos = {}
        treasury = make_treasury(gold=500)
        mayor = make_mayor()
        process_external_threats([threat], {}, {}, world, treasury, mayor)
        assert threat.active  # indefinite threats don't expire

    def test_inactive_threat_skipped(self):
        threat = make_bandit_threat(threat_level=3)
        threat.active = False
        world = WorldState()
        treasury = make_treasury(gold=500)
        mayor = make_mayor()
        results = process_external_threats([threat], {}, {}, world, treasury, mayor)
        assert results == []


# ── Cycle integration ─────────────────────────────────────────────────────────

class TestSpecialCycleIntegration:
    def test_public_processed_each_cycle(self):
        world = WorldState()
        world.chaos = {}
        factions = {}
        domains = {}
        mayor = Mayor(action_points=6, reputation={"the_public": 30})
        treasury = Treasury(gold=500)
        public = ThePublic(support=0)

        run_cycle(world, factions, domains, mayor=mayor, treasury=treasury, public=public)
        # Reputation decays -1 per cycle (30→29) before public syncs; still content
        assert public.support == 29
        assert public.disposition == "content"

    def test_threats_applied_in_cycle(self):
        world = WorldState()
        world.chaos = {"street": 0.0}
        factions = {}
        domains = {"street": Domain(id="street", name="street", cap=100)}
        mayor = Mayor(action_points=6)
        treasury = Treasury(gold=500)
        threats = [make_bandit_threat(threat_level=1)]

        run_cycle(world, factions, domains, mayor=mayor, treasury=treasury,
                  external_threats=threats)
        assert world.chaos.get("street", 0) > 0 or treasury.gold < 500
