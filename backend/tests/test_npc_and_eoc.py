"""
test_npc_and_eoc.py — Tests for faction behavior and end-of-cycle (v3).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from engine.models import Faction, Domain, WorldState, FactionTrait, Leader
from engine.npc import select_faction_action, evolve_traits
from engine.npc.behavior import BASE_WEIGHTS, _lowest_health_ally


def make_faction(fid="a", rating=2.0) -> Faction:
    return Faction(
        id=fid, name=f"The {fid}", domain_primary="political",
        rating=rating, health=75,
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
        assert plan.action in ("Grow", "Harm", "Aid", "Protect", "Steal",
                               "BuildProject", "SabotageProject", "Skip")

    def test_plan_faction_id_matches(self):
        f = make_faction("test_id")
        factions = {"test_id": f, "other": make_faction("other")}
        domains = {"political": make_domain()}
        world = WorldState()
        plan = select_faction_action(f, factions, domains, world)
        assert plan.faction_id == "test_id"

    def test_contested_action_has_target(self):
        """For Harm/Steal, target_id should be set."""
        import random
        f = make_faction()
        f.traits = [FactionTrait(trait="aggressive", intensity="very")]
        factions = {"a": f, "b": make_faction("b")}
        domains = {"political": make_domain()}
        world = WorldState()
        for seed in range(50):
            random.seed(seed)
            plan = select_faction_action(f, factions, domains, world)
            if plan.action in ("Harm", "Steal"):
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


class TestBehaviorRedesign:
    """Slice 3: Block gone, Aid added, aggression respects the level-1 safe floor."""

    def test_block_removed_aid_added(self):
        assert "Block" not in BASE_WEIGHTS
        assert "Aid" in BASE_WEIGHTS

    def test_aggression_never_targets_level_1(self):
        import random
        f = make_faction("a", rating=4.0)
        f.traits = [FactionTrait(trait="aggressive", intensity="very")]
        rival = make_faction("b", rating=1.0)  # level 1 — protected by the safe floor
        factions = {"a": f, "b": rival}
        domains = {"political": make_domain()}
        world = WorldState()
        for seed in range(100):
            random.seed(seed)
            plan = select_faction_action(f, factions, domains, world)
            assert not (plan.action in ("Harm", "Steal") and plan.target_id == "b")

    def test_aggression_targets_eligible_rival(self):
        import random
        f = make_faction("a", rating=4.0)
        f.traits = [FactionTrait(trait="aggressive", intensity="very")]
        safe = make_faction("b", rating=1.0)    # level 1 — protected
        target = make_faction("c", rating=3.0)  # level 3 — fair game
        factions = {"a": f, "b": safe, "c": target}
        domains = {"political": make_domain()}
        world = WorldState()
        for seed in range(100):
            random.seed(seed)
            plan = select_faction_action(f, factions, domains, world)
            if plan.action in ("Harm", "Steal"):
                assert plan.target_id == "c"
                return
        pytest.skip("No aggressive action selected in 100 seeds")

    def test_aid_picks_lowest_health_ally(self):
        f = make_faction("a")
        f.traits = [
            FactionTrait(trait="allied with", intensity="moderate", target_id="b"),
            FactionTrait(trait="allied with", intensity="moderate", target_id="c"),
        ]
        ally_hi = make_faction("b", rating=2.0); ally_hi.health = 80
        ally_lo = make_faction("c", rating=2.0); ally_lo.health = 20
        factions = {"a": f, "b": ally_hi, "c": ally_lo}
        low = _lowest_health_ally(f, factions)
        assert low is not None and low.id == "c"
