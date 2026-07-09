"""Scheduled scripted-event triggers (at_cycle / every_n_cycles), the runner wiring, and the
no-op placeholder deck (events_spec — Scheduled triggers + Placeholder events, 2026-07-09)."""
import os
import pytest
from engine.models import (
    WorldState, Faction, Domain, Leader, Mayor, Treasury,
)
from engine.events.event_system import check_scripted_events
from engine.cycle.runner import run_cycle
from loaders import load_event_deck


def make_faction(fid="f1", domain="trade", health=75, rating=2.0):
    return Faction(id=fid, name=fid, domain_primary=domain,
                   leader=Leader(name="Test"), health=health, rating=rating)


def make_world(cycle=0):
    w = WorldState()
    w.chaos = {"trade": 0.0}
    w.cycle = cycle
    return w


def _scripted(eid, conds):
    return {
        "id": eid, "name": eid, "type": "scripted",
        "trigger_conditions": conds,
        "template": {"target_type": "world", "target_id": "world",
                     "duration": 1, "effects": []},
    }


# ── at_cycle ──────────────────────────────────────────────────────────────────

class TestAtCycle:
    def test_fires_only_on_target_cycle(self):
        deck = [_scripted("honeymoon", {"at_cycle": 4})]
        factions = {"f1": make_faction()}
        for c in range(0, 8):
            world = make_world(cycle=c)
            events = check_scripted_events(world, factions, {}, Treasury(), deck)
            if c == 4:
                assert [e.id for e in events] == ["honeymoon"]
            else:
                assert events == []


# ── every_n_cycles ────────────────────────────────────────────────────────────

class TestEveryNCycles:
    def test_fires_on_multiples_not_zero_not_between(self):
        deck = [_scripted("admirer", {"every_n_cycles": 10})]
        factions = {"f1": make_faction()}
        fired_on = [c for c in range(0, 31)
                    if check_scripted_events(make_world(cycle=c), factions, {}, Treasury(), deck)]
        assert fired_on == [10, 20, 30]  # never 0, never a non-multiple

    def test_guards_nonpositive_n(self):
        deck = [_scripted("bad", {"every_n_cycles": 0})]
        assert check_scripted_events(make_world(cycle=10), {}, {}, Treasury(), deck) == []


# ── Runner wiring + dedup ─────────────────────────────────────────────────────

class TestRunnerWiring:
    def test_scripted_event_appears_via_run_cycle(self):
        # at_cycle:1 → the event is created during the cycle whose number is 1.
        deck = [{
            "id": "sched", "name": "Scheduled", "type": "scripted",
            "trigger_conditions": {"at_cycle": 1},
            "template": {"target_type": "world", "target_id": "world",
                         "duration": 3, "effects": []},
        }]
        world = make_world(cycle=1)
        factions = {"f1": make_faction()}
        domains = {"trade": Domain(id="trade", name="trade", cap=100)}
        active_events = []
        run_cycle(world, factions, domains, mayor=Mayor(action_points=6),
                  treasury=Treasury(gold=500), event_deck=deck, active_events=active_events)
        assert any(e.id == "sched" for e in active_events)

    def test_no_duplicate_stacking(self):
        # A multi-cycle scripted event that stays eligible must not be re-added while active.
        deck = [{
            "id": "stay", "name": "Stay", "type": "scripted",
            "trigger_conditions": {"min_cycle": 0},  # level-triggered: eligible every cycle
            "template": {"target_type": "world", "target_id": "world",
                         "duration": 5, "effects": []},
        }]
        world = make_world(cycle=0)
        factions = {"f1": make_faction()}
        domains = {"trade": Domain(id="trade", name="trade", cap=100)}
        active_events = []
        for _ in range(3):
            run_cycle(world, factions, domains, mayor=Mayor(action_points=6),
                      treasury=Treasury(gold=500), event_deck=deck, active_events=active_events)
        assert sum(1 for e in active_events if e.id == "stay") == 1


# ── Placeholder deck is a real, loadable, no-op deck ──────────────────────────

class TestPlaceholderDeck:
    def test_placeholders_present_and_effectless(self):
        deck = load_event_deck()
        placeholders = [e for e in deck if e.get("id", "").startswith("placeholder_")]
        assert placeholders, "expected placeholder_* events in the shipped deck"
        for e in placeholders:
            assert e["type"] == "scripted"
            assert e["template"].get("effects", []) == []  # no mechanical effect by design
            conds = e["trigger_conditions"]
            assert "at_cycle" in conds or "every_n_cycles" in conds
