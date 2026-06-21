"""Tests for Rally / Agitate — factions sway the Public's opinion of the Mayor.

Spec: actions_spec §Rally/§Agitate, faction-behavior_spec (Step 3 stance row),
proposals/faction-influence.md. Constants/dials imported, never copied.
"""
import random

import engine.npc.behavior as behavior
from engine.actions.faction import _influence_delta, resolve_rally, resolve_agitate
from engine.balance import NORMAL, get_profile
from engine.cycle.runner import run_cycle
from engine.models import Faction, Leader, Mayor, ThePublic, WorldState


def mk_faction(fid, domain="trade", rating=2.0):
    return Faction(id=fid, name=fid.title(), domain_primary=domain, leader=Leader(name=f"L-{fid}"),
                   rating=rating)


def captured_weights(faction, factions, mayor=None, monkeypatch=None):
    captured = {}

    def capture(weights):
        captured.update(weights)
        return "Grow"

    monkeypatch.setattr(behavior, "weighted_choice", capture)
    monkeypatch.setattr(behavior.random, "random", lambda: 0.99)  # never Skip
    behavior.select_faction_action(faction, factions, {}, WorldState(), mayor=mayor)
    return captured


# ── Resolvers (deterministic) ────────────────────────────────────────────────────

class TestResolvers:
    def test_rally_raises_public_support_rank_scaled(self):
        f = mk_faction("a", rating=6.0)   # level 6 → round(0.5*6)=3
        f.health = 70
        mayor = Mayor(); mayor.set_reputation("the_public", 5)
        r = resolve_rally(f, mayor, NORMAL)
        assert mayor.get_reputation("the_public") == 5 + 3
        assert f.rating == 6.0 and f.health == 70        # pure opportunity cost
        assert r.action == "Rally" and r.outcome == "success"

    def test_agitate_lowers_public_support(self):
        f = mk_faction("a", rating=6.0)
        mayor = Mayor(); mayor.set_reputation("the_public", 5)
        resolve_agitate(f, mayor, NORMAL)
        assert mayor.get_reputation("the_public") == 5 - 3

    def test_influence_delta_scaling(self):
        assert _influence_delta(mk_faction("x", rating=1.0), NORMAL) == 1   # max(1, round(0.5))
        assert _influence_delta(mk_faction("x", rating=4.0), NORMAL) == 2
        assert _influence_delta(mk_faction("x", rating=10.0), NORMAL) == 5

    def test_magnitude_scales_with_difficulty(self):
        f = mk_faction("a", rating=6.0)
        hard = get_profile("hard")
        # influence_per_level is shared today, so this just guards the dial is read, not hardcoded.
        assert _influence_delta(f, hard) == max(1, round(hard.influence_per_level * f.level))


# ── Weight gating (Step 3 stance) ─────────────────────────────────────────────────

class TestWeights:
    def test_no_mayor_means_no_influence_weight(self, monkeypatch):
        f = mk_faction("a")
        w = captured_weights(f, {"a": f}, mayor=None, monkeypatch=monkeypatch)
        assert w.get("Rally", 0.0) == 0.0 and w.get("Agitate", 0.0) == 0.0

    def test_indifferent_middle_reaches_for_neither(self, monkeypatch):
        f = mk_faction("a")
        mayor = Mayor(); mayor.set_reputation("a", 0)   # between the thresholds
        w = captured_weights(f, {"a": f}, mayor=mayor, monkeypatch=monkeypatch)
        assert w["Rally"] == 0.0 and w["Agitate"] == 0.0

    def test_high_standing_lifts_rally(self, monkeypatch):
        f = mk_faction("a")
        mayor = Mayor(); mayor.set_reputation("a", behavior.RALLY_THRESHOLD)   # exactly at threshold
        w = captured_weights(f, {"a": f}, mayor=mayor, monkeypatch=monkeypatch)
        assert w["Rally"] == behavior.RALLY_WEIGHT and w["Agitate"] == 0.0

    def test_low_standing_lifts_agitate(self, monkeypatch):
        f = mk_faction("a")
        mayor = Mayor(); mayor.set_reputation("a", behavior.AGITATE_THRESHOLD)
        w = captured_weights(f, {"a": f}, mayor=mayor, monkeypatch=monkeypatch)
        assert w["Agitate"] == behavior.AGITATE_WEIGHT and w["Rally"] == 0.0

    def test_stronger_standing_scales_weight(self, monkeypatch):
        f = mk_faction("a")
        near = Mayor(); near.set_reputation("a", behavior.RALLY_THRESHOLD)
        far = Mayor(); far.set_reputation("a", behavior.RALLY_THRESHOLD + 30)
        w_near = captured_weights(f, {"a": f}, mayor=near, monkeypatch=monkeypatch)
        w_far = captured_weights(f, {"a": f}, mayor=far, monkeypatch=monkeypatch)
        assert w_far["Rally"] > w_near["Rally"]


# ── Integration through run_cycle ─────────────────────────────────────────────────

def _final_public_rep(forced_action, monkeypatch, seed=11):
    random.seed(seed)
    monkeypatch.setattr(behavior, "weighted_choice", lambda w: forced_action)
    monkeypatch.setattr(behavior.random, "random", lambda: 0.99)  # never Skip
    factions = {"a": mk_faction("a", rating=6.0)}
    mayor = Mayor(); mayor.set_reputation("the_public", 0)
    public = ThePublic(support=0)
    for _ in range(3):
        run_cycle(WorldState(chaos={}), factions, {}, mayor=mayor, public=public, balance=NORMAL)
    return mayor.get_reputation("the_public")


def test_rally_run_beats_agitate_run(monkeypatch):
    rally = _final_public_rep("Rally", monkeypatch)
    agitate = _final_public_rep("Agitate", monkeypatch)
    assert rally > agitate
