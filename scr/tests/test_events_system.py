"""Tests for the full event system — random, scripted, active processing, cascades."""
import pytest
from engine.models import (
    GameEvent, EventEffect, CascadeSpec, WorldState,
    Faction, Domain, FactionTrait, Leader,
)
from engine.events.event_system import (
    roll_for_random_events, check_scripted_events,
    process_active_events, create_mayor_triggered_event,
    _chaos_event_chance,
)
from engine.cycle.runner import run_cycle
from engine.models import Mayor, Treasury


def make_faction(fid="f1", domain="trade", health=75, floor=2, rating=2.0):
    return Faction(id=fid, name=fid, domain_primary=domain, leader=Leader(name="Test"), health=health, floor=floor, rating=rating)


def make_domain(did="trade", cap=100):
    return Domain(id=did, name=did, cap=cap)


def make_world(chaos=None):
    w = WorldState()
    w.chaos = chaos or {"trade": 5.0}
    return w


def make_event(eid="evt1", duration=2, status="active", effects=None, cascade=None):
    return GameEvent(
        id=eid, name=eid, type="random", trigger="test",
        target_type="faction", target_id="f1",
        duration=duration, cycles_remaining=duration,
        effects=effects or [], cascade=cascade, status=status,
    )


# ── Chaos probability table ───────────────────────────────────────────────────

class TestChaosChance:
    def test_low_chaos_low_chance(self):
        assert _chaos_event_chance(1.0) == 0.05

    def test_medium_chaos(self):
        assert _chaos_event_chance(4.0) == 0.15

    def test_high_chaos(self):
        assert _chaos_event_chance(7.0) == 0.30

    def test_max_chaos(self):
        assert _chaos_event_chance(10.0) == 0.50


# ── Random event rolling ──────────────────────────────────────────────────────

class TestRollForRandomEvents:
    def test_no_deck_no_events(self):
        world = make_world({"trade": 5.0})
        factions = {"f1": make_faction()}
        domains = {"trade": make_domain()}
        events = roll_for_random_events(world, factions, domains, [])
        assert events == []

    def test_deck_with_guaranteed_roll(self):
        import random
        random.seed(42)
        world = make_world({"trade": 10.0})  # 50% chance
        factions = {"f1": make_faction("f1", "trade")}
        domains = {"trade": make_domain("trade")}
        deck = [{
            "id": "test_event", "name": "Test Event",
            "type": "random", "weight": 10,
            "trigger_conditions": {"domain": "trade", "min_chaos": 0},
            "template": {
                "target_type": "faction",
                "target_id": "f1",
                "duration": 2,
                "effects": [{"field": "health", "target_id": "f1", "value": -5.0, "label": "test"}],
            },
        }]
        # With max chaos and seed, should fire at least once across multiple attempts
        fired = False
        for seed in range(50):
            random.seed(seed)
            events = roll_for_random_events(world, factions, domains, deck)
            if events:
                fired = True
                assert events[0].id == "test_event"
                break
        assert fired

    def test_trigger_condition_domain_filter(self):
        import random
        world = make_world({"trade": 10.0, "docks": 10.0})
        factions = {"f1": make_faction("f1", "trade")}
        domains = {"trade": make_domain("trade"), "docks": make_domain("docks")}
        deck = [{
            "id": "dock_event", "name": "Dock Event",
            "type": "random", "weight": 100,
            "trigger_conditions": {"domain": "docks", "min_chaos": 0},
            "template": {
                "target_type": "faction", "target_id": "f1",
                "duration": 1, "effects": [],
            },
        }]
        # Events from this deck can only fire for docks domain — never trade
        fired_events = []
        for seed in range(50):
            random.seed(seed)
            events = roll_for_random_events(world, factions, domains, deck)
            fired_events.extend(events)
        # Any fired events must have come from docks
        for e in fired_events:
            assert "docks" in e.trigger


# ── Active event processing ───────────────────────────────────────────────────

class TestProcessActiveEvents:
    def test_event_applies_health_effect(self):
        faction = make_faction("f1", health=75)
        event = make_event(duration=2, effects=[
            EventEffect(field="health", target_id="f1", value=-5.0, label="test"),
        ])
        world = make_world()
        results = process_active_events([event], {"f1": faction}, {}, world)
        assert faction.health == 70
        assert event.cycles_remaining == 1

    def test_event_resolves_after_duration(self):
        event = make_event(duration=1, effects=[])
        world = make_world()
        process_active_events([event], {}, {}, world)
        assert event.status == "resolved"

    def test_event_enters_cascading_state(self):
        cascade = CascadeSpec(
            delay=1, target_id="f1",
            effects=[EventEffect(field="health", target_id="f1", value=-10.0, label="cascade")],
        )
        event = make_event(duration=1, cascade=cascade)
        world = make_world()
        process_active_events([event], {}, {}, world)
        assert event.status == "cascading"
        assert event.cascade_delay_remaining == 1

    def test_cascade_fires_after_delay(self):
        faction = make_faction("f1", health=75)
        cascade = CascadeSpec(
            delay=0, target_id="f1",
            effects=[EventEffect(field="health", target_id="f1", value=-10.0, label="cascade")],
        )
        event = make_event(duration=1, cascade=cascade, status="active")
        world = make_world()
        # First process: resolves primary, enters cascading with delay=0
        process_active_events([event], {"f1": faction}, {}, world)
        # event is now cascading with delay=0
        assert event.status == "cascading"
        # Second process: fires cascade immediately
        results = process_active_events([event], {"f1": faction}, {}, world)
        assert event.status == "resolved"
        assert faction.health == 65  # -10 from cascade

    def test_resolved_events_filtered_out(self):
        active = [make_event(duration=1, status="active")]
        world = make_world()
        process_active_events(active, {}, {}, world)
        # Simulate runner filtering
        active[:] = [e for e in active if e.status != "resolved"]
        assert len(active) == 0


# ── Scripted events ───────────────────────────────────────────────────────────

class TestScriptedEvents:
    def test_scripted_fires_on_cycle_condition(self):
        world = make_world()
        world.cycle = 15
        deck = [{
            "id": "plague", "name": "Plague",
            "type": "scripted", "weight": 1,
            "trigger_conditions": {"min_cycle": 10},
            "template": {
                "target_type": "faction", "target_id": "f1",
                "duration": 3, "effects": [],
            },
        }]
        from engine.models import Treasury
        events = check_scripted_events(world, {"f1": make_faction()}, {}, Treasury(), deck)
        assert len(events) == 1
        assert events[0].id == "plague"

    def test_scripted_does_not_fire_early(self):
        world = make_world()
        world.cycle = 5
        deck = [{
            "id": "plague", "name": "Plague",
            "type": "scripted", "weight": 1,
            "trigger_conditions": {"min_cycle": 10},
            "template": {
                "target_type": "faction", "target_id": "f1",
                "duration": 3, "effects": [],
            },
        }]
        from engine.models import Treasury
        events = check_scripted_events(world, {}, {}, Treasury(), deck)
        assert len(events) == 0


# ── Mayor-triggered events ────────────────────────────────────────────────────

class TestMayorTriggeredEvents:
    def test_condemn_creates_rivals_emboldened(self):
        factions = {
            "f1": make_faction("f1", "trade"),
            "f2": make_faction("f2", "trade"),
        }
        event = create_mayor_triggered_event("PubliclyCondemn", "f1", factions, cycle=1)
        assert event is not None
        assert event.type == "mayor_triggered"
        assert event.target_id in ("f2",)

    def test_withhold_creates_outside_pressure(self):
        factions = {"f1": make_faction("f1", "trade")}
        event = create_mayor_triggered_event("WithholdResources", "f1", factions, cycle=1)
        assert event is not None
        assert event.duration == 2
        assert any(e.field == "entrench" for e in event.effects)

    def test_unknown_action_returns_none(self):
        event = create_mayor_triggered_event("PubliclyEndorse", "f1", {}, cycle=1)
        assert event is None


# ── Cycle integration ─────────────────────────────────────────────────────────

class TestEventCycleIntegration:
    def test_active_events_processed_each_cycle(self):
        world = WorldState()
        world.chaos = {"trade": 0.0}
        faction = make_faction("f1", health=75)
        factions = {"f1": faction}
        domains = {"trade": make_domain()}
        mayor = Mayor(action_points=6)
        treasury = Treasury(gold=500)

        event = make_event("dmg_evt", duration=2, effects=[
            EventEffect(field="health", target_id="f1", value=-5.0, label="test"),
        ])
        active_events = [event]

        run_cycle(world, factions, domains, mayor=mayor, treasury=treasury,
                  active_events=active_events)

        # -5 from event; faction also gets end-of-cycle health decay (leaderless = -2)
        assert faction.health < 75
        assert event.cycles_remaining == 1
