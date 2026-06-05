"""
test_events.py — Tests for v3 events (cascades, world chaos).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from engine.models import Faction, Domain, WorldState, ActionResult, Leader
from engine.events import check_for_cascades, process_world_chaos


def make_faction(fid="a", domain="political", rating=4.0) -> Faction:
    return Faction(id=fid, name=f"The {fid}", domain_primary=domain,
                   rating=rating, health=50,
                   leader=Leader(name="Test"))


def make_domain(did="political") -> Domain:
    return Domain(id=did, name=did, cap=100)


class TestCheckForCascades:
    """Collapse cascades are retired — factions are permanent (they Break, never die),
    so check_for_cascades is a no-op kept only for back-compat."""

    def test_no_results_no_cascade(self):
        factions = {"a": make_faction()}
        domains = {"political": make_domain()}
        world = WorldState()
        results = [ActionResult("Grow", "a", None, "success")]
        assert check_for_cascades(results, factions, domains, world) == []

    def test_collapse_no_longer_cascades(self):
        # A legacy "FactionCollapse" result must produce nothing now.
        factions = {"a": make_faction()}
        domains = {"political": make_domain()}
        world = WorldState()
        results = [ActionResult("FactionCollapse", "a", None, "decisive", domain="political")]
        assert check_for_cascades(results, factions, domains, world) == []

    def test_no_chaos_side_effects(self):
        domains = {"political": make_domain()}
        world = WorldState(chaos={"political": 0})
        results = [ActionResult("FactionCollapse", "a", None, "decisive", domain="political")]
        check_for_cascades(results, {}, domains, world)
        assert world.chaos.get("political", 0) == 0


class TestProcessWorldChaos:
    def test_no_chaos_no_results(self):
        factions = {"a": make_faction()}
        domains = {"political": make_domain()}
        world = WorldState(chaos={})
        results = process_world_chaos(world, factions, domains)
        assert results == []

    def test_high_chaos_fires_event(self):
        import random
        factions = {"a": make_faction()}
        domains = {"political": make_domain()}
        found = False
        for seed in range(50):
            random.seed(seed)
            world = WorldState(chaos={"political": 10})
            results = process_world_chaos(world, factions, domains)
            if results:
                found = True
                break
        assert found
