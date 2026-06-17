"""Piety/unrest event integration — public-targeted effects, band gates, the two flagships.

Spec: events_spec (piety/unrest gates + flagships, public-targeted effects).
"""
import json
import os

from engine.events.event_system import _matches_trigger, process_active_events
from engine.models import EventEffect, GameEvent, ThePublic, WorldState

DATA = os.path.join(os.path.dirname(__file__), "..", "data")


def mk_event(eid, effects, **tmpl):
    return GameEvent(id=eid, name=eid, type="random", trigger="test",
                     target_type=tmpl.get("target_type", "public"),
                     target_id=tmpl.get("target_id", "the_public"),
                     duration=1, cycles_remaining=1, status="active", effects=effects)


def deck():
    with open(os.path.join(DATA, "events.json"), encoding="utf-8") as f:
        return {e["id"]: e for e in json.load(f)}


class TestPublicTargetedEffect:
    def test_clamps_and_applies(self):
        p = ThePublic(piety=10)
        ev = mk_event("omen", [EventEffect(field="piety", target_id="the_public", value=-5, label="x")])
        process_active_events([ev], {}, {}, WorldState(), public=p)
        assert p.piety == 5

    def test_support_floor_minus_50(self):
        p = ThePublic(support=-49)
        ev = mk_event("x", [EventEffect(field="support", target_id="the_public", value=-10, label="x")])
        process_active_events([ev], {}, {}, WorldState(), public=p)
        assert p.support == -50  # clamps at the support floor, not 0

    def test_support_ceiling_plus_50(self):
        p = ThePublic(support=45)
        ev = mk_event("x", [EventEffect(field="support", target_id="the_public", value=20, label="x")])
        process_active_events([ev], {}, {}, WorldState(), public=p)
        assert p.support == 50  # support tops out at +50, not 100

    def test_no_public_is_safe(self):
        ev = mk_event("x", [EventEffect(field="piety", target_id="the_public", value=-5, label="x")])
        # public=None → the effect is simply skipped, no crash
        process_active_events([ev], {}, {}, WorldState(), public=None)


class TestBandGates:
    def _eligible(self, conds, public):
        return _matches_trigger({"trigger_conditions": conds}, "guilds", 0.0, {}, WorldState(), public)

    def test_min_unrest_band_boiling(self):
        assert self._eligible({"min_unrest_band": "Boiling"}, ThePublic(unrest=90))
        assert not self._eligible({"min_unrest_band": "Boiling"}, ThePublic(unrest=70))  # Agitated

    def test_max_piety_band_lax(self):
        assert self._eligible({"max_piety_band": "Lax"}, ThePublic(piety=30))      # Lax
        assert self._eligible({"max_piety_band": "Lax"}, ThePublic(piety=10))      # Godless
        assert not self._eligible({"max_piety_band": "Lax"}, ThePublic(piety=50))  # Observant

    def test_need_gate_without_public_ineligible(self):
        assert not self._eligible({"min_unrest_band": "Boiling"}, None)


class TestFlagships:
    def test_mob_marches_fires(self):
        tmpl = deck()["mob_marches"]["template"]
        effects = [EventEffect(**e) for e in tmpl["effects"]]
        ev = mk_event("mob_marches", effects)
        p = ThePublic(health=80)
        world = WorldState(chaos={"guilds": 1.0})
        process_active_events([ev], {}, {}, world, public=p)
        assert world.chaos["guilds"] == 3.0   # +2 disorder
        assert p.health == 75                  # −5 injuries

    def test_mob_marches_gated_to_boiling(self):
        conds = deck()["mob_marches"]["trigger_conditions"]
        assert _matches_trigger({"trigger_conditions": conds}, "guilds", 0.0, {}, WorldState(),
                                ThePublic(unrest=90))
        assert not _matches_trigger({"trigger_conditions": conds}, "guilds", 0.0, {}, WorldState(),
                                    ThePublic(unrest=50))

    def test_ignored_omen_fires_and_gating(self):
        entry = deck()["ignored_omen"]
        effects = [EventEffect(**e) for e in entry["template"]["effects"]]
        p = ThePublic(piety=15, support=0)
        process_active_events([mk_event("ignored_omen", effects)], {}, {}, WorldState(), public=p)
        assert p.piety == 10 and p.support == -3
        # gated to Godless/Lax — not eligible at Observant
        conds = entry["trigger_conditions"]
        assert _matches_trigger({"trigger_conditions": conds}, "guilds", 0.0, {}, WorldState(),
                                ThePublic(piety=15))
        assert not _matches_trigger({"trigger_conditions": conds}, "guilds", 0.0, {}, WorldState(),
                                    ThePublic(piety=70))
