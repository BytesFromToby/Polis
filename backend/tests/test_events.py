"""
test_events.py — Tests for v3 events (cascades, world chaos).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from engine.models import Faction, Domain, WorldState, ActionResult, Leader
from engine.events import check_for_cascades, process_world_chaos


def make_faction(fid="a", domain="political", rating=4.0, floor=4) -> Faction:
    f = Faction(id=fid, name=f"The {fid}", domain_primary=domain,
                rating=rating, health=50, entrench=50,
                leader=Leader(name="Test"))
    f.floor = floor
    return f


def make_domain(did="political") -> Domain:
    return Domain(id=did, name=did, cap=100)


class TestCheckForCascades:
    def test_no_collapse_no_cascade(self):
        factions = {"a": make_faction()}
        domains = {"political": make_domain()}
        world = WorldState()
        results = [ActionResult("Grow", "a", None, "success")]
        cascades = check_for_cascades(results, factions, domains, world)
        assert cascades == []

    def test_collapse_triggers_cascade(self):
        factions = {"a": make_faction()}
        domains = {"political": make_domain()}
        world = WorldState()
        results = [ActionResult("FactionCollapse", "a", None, "decisive", domain="political")]
        cascades = check_for_cascades(results, factions, domains, world)
        assert len(cascades) > 0

    def test_collapse_opens_power_vacuum(self):
        factions = {}
        domains = {"political": make_domain()}
        world = WorldState()
        results = [ActionResult("FactionCollapse", "a", None, "decisive", domain="political")]
        check_for_cascades(results, factions, domains, world)
        assert any(pv.get("domain_id") == "political" for pv in world.power_vacuums)

    def test_collapse_increases_chaos(self):
        factions = {}
        domains = {"political": make_domain()}
        world = WorldState(chaos={"political": 0})
        results = [ActionResult("FactionCollapse", "a", None, "decisive", domain="political")]
        check_for_cascades(results, factions, domains, world)
        assert world.chaos.get("political", 0) > 0


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
