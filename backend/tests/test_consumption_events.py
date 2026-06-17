"""Consumption event integration — band gates + the two flagships (events_spec).

The Wells Sicken (Dry → bad water) and The Drunken Riot (Sodden AND Restless+ → violence).
"""
import json
import os

from engine.events.event_system import _matches_trigger, process_active_events
from engine.models import EventEffect, GameEvent, ThePublic, WorldState

DATA = os.path.join(os.path.dirname(__file__), "..", "data")


def deck():
    with open(os.path.join(DATA, "events.json"), encoding="utf-8") as f:
        return {e["id"]: e for e in json.load(f)}


def mk_event(eid, effects):
    return GameEvent(id=eid, name=eid, type="random", trigger="t", target_type="public",
                     target_id="the_public", duration=1, cycles_remaining=1, status="active",
                     effects=effects)


def eligible(conds, public):
    return _matches_trigger({"trigger_conditions": conds}, "guilds", 0.0, {}, WorldState(), public)


class TestGates:
    def test_max_consumption_band_dry(self):
        assert eligible({"max_consumption_band": "Dry"}, ThePublic(consumption=10))
        assert not eligible({"max_consumption_band": "Dry"}, ThePublic(consumption=50))

    def test_min_consumption_band_sodden(self):
        assert eligible({"min_consumption_band": "Sodden"}, ThePublic(consumption=90))
        assert not eligible({"min_consumption_band": "Sodden"}, ThePublic(consumption=70))


class TestWellsSicken:
    def test_fires_and_gated(self):
        tmpl = deck()["wells_sicken"]
        effects = [EventEffect(**e) for e in tmpl["template"]["effects"]]
        p = ThePublic(consumption=10, health=80)
        process_active_events([mk_event("wells_sicken", effects)], {}, {}, WorldState(), public=p)
        assert p.health == 76  # −4
        conds = tmpl["trigger_conditions"]
        assert eligible(conds, ThePublic(consumption=10))       # Dry
        assert not eligible(conds, ThePublic(consumption=50))   # Tempered


class TestDrunkenRiot:
    def test_compound_gate_needs_both(self):
        conds = deck()["drunken_riot"]["trigger_conditions"]
        # both conditions → eligible
        assert eligible(conds, ThePublic(consumption=90, unrest=50))   # Sodden + Restless
        # either alone → not
        assert not eligible(conds, ThePublic(consumption=90, unrest=10))  # Sodden, but Placid
        assert not eligible(conds, ThePublic(consumption=50, unrest=50))  # Restless, but Tempered

    def test_fires(self):
        tmpl = deck()["drunken_riot"]["template"]
        effects = [EventEffect(**e) for e in tmpl["effects"]]
        p = ThePublic(health=80)
        world = WorldState(chaos={"guilds": 1.0})
        process_active_events([mk_event("drunken_riot", effects)], {}, {}, world, public=p)
        assert world.chaos["guilds"] == 3.0  # +2
        assert p.health == 77                # −3
