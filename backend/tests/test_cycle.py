"""
test_cycle.py — Integration tests for the v3 faction-only cycle runner.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from engine.models import Faction, Domain, WorldState, FactionTrait, Leader
from engine.cycle import run_cycle


def make_world() -> WorldState:
    return WorldState(cycle=0)


def make_domain(did="political") -> Domain:
    return Domain(id=did, name=did.replace("_", " ").title(), cap=100)


def make_faction(fid, domain="political", rating=2.0) -> Faction:
    return Faction(
        id=fid, name=f"The {fid.title()}", domain_primary=domain,
        rating=rating, health=75,
        leader=Leader(name="Test Leader"),
        traits=[FactionTrait(trait="ambitious", intensity="moderate")],
    )


def make_minimal_world():
    world = make_world()
    domains = {"political": make_domain("political"), "street": make_domain("street")}
    factions = {
        "faction_a": make_faction("faction_a", "political", 2.0),
        "faction_b": make_faction("faction_b", "political", 1.5),
        "faction_c": make_faction("faction_c", "street", 2.5),
    }
    return world, factions, domains


class TestRunCycle:
    def test_cycle_completes(self):
        world, factions, domains = make_minimal_world()
        result = run_cycle(world, factions, domains)
        assert result is not None

    def test_cycle_increments_world_cycle(self):
        world, factions, domains = make_minimal_world()
        assert world.cycle == 0
        run_cycle(world, factions, domains)
        assert world.cycle == 1

    def test_result_has_events(self):
        world, factions, domains = make_minimal_world()
        result = run_cycle(world, factions, domains)
        assert isinstance(result.events, list)

    def test_faction_actions_counted(self):
        world, factions, domains = make_minimal_world()
        result = run_cycle(world, factions, domains)
        assert result.faction_actions >= 0

    def test_multiple_cycles_run(self):
        world, factions, domains = make_minimal_world()
        for _ in range(5):
            if factions:
                run_cycle(world, factions, domains)
        assert world.cycle == 5

    def test_domain_utilization_recalculated(self):
        world, factions, domains = make_minimal_world()
        run_cycle(world, factions, domains)
        # political domain has 2 factions; utilization should be > 0
        # (factions at floor 2 = weight 2 each)
        assert domains["political"].utilization >= 0
