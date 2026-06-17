"""Confidence event integration — band gates + the three flagships (events_spec).

Removal Coalition (Hostile), Effigy in the Agora (Hostile/Suspicious), Acclamation (Beloved).
"""
import json
import os

from engine.events.event_system import _matches_trigger, process_active_events
from engine.models import EventEffect, Faction, GameEvent, Leader, ThePublic, WorldState

DATA = os.path.join(os.path.dirname(__file__), "..", "data")


def deck():
    with open(os.path.join(DATA, "events.json"), encoding="utf-8") as f:
        return {e["id"]: e for e in json.load(f)}


def mk_event(eid, effects, target_type="public", target_id="the_public"):
    return GameEvent(id=eid, name=eid, type="random", trigger="t", target_type=target_type,
                     target_id=target_id, duration=1, cycles_remaining=1, status="active",
                     effects=effects)


def eligible(conds, support):
    return _matches_trigger({"trigger_conditions": conds}, "guilds", 0.0, {}, WorldState(),
                            ThePublic(support=support))


def mh():
    return Faction(id="merchant-houses", name="Merchant Houses", domain_primary="port",
                   leader=Leader(name="x"), rating=4.0)


class TestGates:
    def test_max_confidence_hostile(self):
        assert eligible({"max_confidence_band": "Hostile"}, -40)       # Hostile
        assert not eligible({"max_confidence_band": "Hostile"}, -20)   # Suspicious

    def test_min_confidence_beloved(self):
        assert eligible({"min_confidence_band": "Beloved"}, 40)        # Beloved
        assert not eligible({"min_confidence_band": "Beloved"}, 20)    # Favorable


class TestRemovalCoalition:
    def test_fires_and_gated(self):
        tmpl = deck()["removal_coalition"]
        effects = [EventEffect(**e) for e in tmpl["template"]["effects"]]
        factions = {"merchant-houses": mh()}
        world = WorldState(chaos={"port": 0.0})
        process_active_events([mk_event("rc", effects, "faction", "merchant-houses")],
                              factions, {}, world, public=ThePublic(support=-40))
        assert factions["merchant-houses"].rating == 4.3   # +0.3
        assert world.chaos["port"] == 1.0                  # +1
        conds = tmpl["trigger_conditions"]
        assert eligible(conds, -40)        # Hostile
        assert not eligible(conds, -15)    # Suspicious — not eligible


class TestEffigy:
    def test_fires_at_hostile_or_suspicious(self):
        conds = deck()["effigy_in_the_agora"]["trigger_conditions"]
        assert eligible(conds, -40)   # Hostile
        assert eligible(conds, -15)   # Suspicious
        assert not eligible(conds, 0)  # Neutral

    def test_effects(self):
        tmpl = deck()["effigy_in_the_agora"]["template"]
        effects = [EventEffect(**e) for e in tmpl["effects"]]
        factions = {"merchant-houses": mh()}
        p = ThePublic(support=-20)
        process_active_events([mk_event("ef", effects, "faction", "merchant-houses")],
                              factions, {}, WorldState(), public=p)
        assert factions["merchant-houses"].rating == 4.2  # +0.2
        assert p.support == -22                            # −2


class TestAcclamation:
    def test_fires_and_gated(self):
        tmpl = deck()["acclamation"]
        effects = [EventEffect(**e) for e in tmpl["template"]["effects"]]
        p = ThePublic(support=40)
        process_active_events([mk_event("ac", effects)], {}, {}, WorldState(), public=p)
        assert p.support == 45  # +5
        conds = tmpl["trigger_conditions"]
        assert eligible(conds, 40)        # Beloved
        assert not eligible(conds, 20)    # Favorable
