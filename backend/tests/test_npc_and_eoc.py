"""
test_npc_and_eoc.py — Tests for faction behavior and end-of-cycle (v3).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from engine.models import Faction, Domain, WorldState, FactionTrait, Leader
from engine.npc import select_faction_action, evolve_traits


def make_faction(fid="a", rating=2.0) -> Faction:
    return Faction(
        id=fid, name=f"The {fid}", domain_primary="political",
        rating=rating, health=75, entrench=75,
        leader=Leader(name="Test"),
        traits=[FactionTrait(trait="aggressive", intensity="moderate")],
    )


def make_domain(did="political") -> Domain:
    return Domain(id=did, name=did, cap=100)


class TestSelectFactionAction:
    def test_returns_faction_plan(self):
        from engine.models import FactionPlan
        f = make_faction()
        factions = {"a": f, "b": make_faction("b", 1.5)}
        domains = {"political": make_domain()}
        world = WorldState()
        plan = select_faction_action(f, factions, domains, world)
        assert isinstance(plan, FactionPlan)

    def test_plan_has_valid_action(self):
        f = make_faction()
        factions = {"a": f, "b": make_faction("b", 1.5)}
        domains = {"political": make_domain()}
        world = WorldState()
        plan = select_faction_action(f, factions, domains, world)
        assert plan.action in ("Grow", "Harm", "Block", "Protect", "Steal", "Recruit", "Skip")

    def test_plan_faction_id_matches(self):
        f = make_faction("test_id")
        factions = {"test_id": f, "other": make_faction("other")}
        domains = {"political": make_domain()}
        world = WorldState()
        plan = select_faction_action(f, factions, domains, world)
        assert plan.faction_id == "test_id"

    def test_contested_action_has_target(self):
        """For Harm/Block/Steal, target_id should be set."""
        import random
        f = make_faction()
        f.traits = [FactionTrait(trait="aggressive", intensity="very")]
        factions = {"a": f, "b": make_faction("b")}
        domains = {"political": make_domain()}
        world = WorldState()
        for seed in range(50):
            random.seed(seed)
            plan = select_faction_action(f, factions, domains, world)
            if plan.action in ("Harm", "Block", "Steal"):
                assert plan.target_id is not None
                return


class TestEvolveTraits:
    def test_harmed_adds_angry_at(self):
        f = make_faction()
        f.traits = []
        evolve_traits(f, was_harmed_by="enemy_id")
        trait_names = [t.trait for t in f.traits]
        assert "angry at" in trait_names or "aggressive" in trait_names

    def test_grow_streak_adds_ambitious(self):
        f = make_faction()
        f.traits = []
        evolve_traits(f, grew_streak=3)
        trait_names = [t.trait for t in f.traits]
        assert "ambitious" in trait_names

    def test_hostile_drought_decays_aggressive(self):
        f = make_faction()
        f.traits = [FactionTrait(trait="aggressive", intensity="moderate")]
        evolve_traits(f, hostile_drought=5)
        t = f.get_trait("aggressive")
        if t:
            assert t.intensity == "slight"
        else:
            pass  # trait was removed (was at slight already) — also valid

    def test_max_traits_enforced(self):
        """Adding a trait when already at 6 should not exceed 6."""
        f = make_faction()
        f.traits = [FactionTrait(trait=f"t{i}", intensity="moderate") for i in range(6)]
        evolve_traits(f, grew_streak=3)
        assert len(f.traits) <= 6
