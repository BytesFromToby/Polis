"""
test_project_initiation.py — base-project initiation on the stack model (projects_spec v6).

Breaking ground adds a new top (count += 1, building, progress 0); refused while the top
is in-flux (building or damaged). Mayor may break ground anywhere; NPC factions break
ground under near-cap pressure (own domain utilization ≥ 0.85 × cap) with a pristine/empty top.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from engine.models import Faction, Domain, Leader, BaseProjectStack, WorldState, Treasury, Mayor
from engine.npc import select_faction_action
from engine.projects.processing import initiate_base_stack, mayor_build_base


def mk_faction(fid="a", dom="harbor", rating=2.0):
    return Faction(id=fid, name=fid, domain_primary=dom, rating=rating, health=75,
                   leader=Leader(name="L"))


def mk_domain(did="harbor", cap=10, base_cap=10, utilization=9.0):
    return Domain(id=did, name=did, cap=cap, base_cap=base_cap, utilization=utilization)


def mk_stack(dom="harbor", **kw):
    return BaseProjectStack(name="Docks", domains=[dom], **kw)


# ── initiate_base_stack ─────────────────────────────────────────────────────────

class TestInitiateHelper:
    def test_break_ground_on_empty(self):
        s = mk_stack(count=0)
        assert initiate_base_stack(s, "mayor") is True
        assert s.count == 1 and s.completed is False and s.progress == 0

    def test_break_ground_on_pristine_pool(self):
        s = mk_stack(count=2, completed=True, progress=100)
        assert initiate_base_stack(s, "mayor") is True
        assert s.count == 3 and s.completed is False and s.progress == 0

    def test_refused_while_building(self):
        s = mk_stack(count=1, completed=False, progress=50)
        assert initiate_base_stack(s, "mayor") is False
        assert s.count == 1   # unchanged — resolve the front first

    def test_refused_while_damaged(self):
        s = mk_stack(count=2, completed=True, progress=40)
        assert initiate_base_stack(s, "mayor") is False
        assert s.count == 2


# ── NPC near-cap initiation ─────────────────────────────────────────────────────

class TestFactionInitiation:
    def test_faction_builds_own_domain_when_near_cap_with_empty_stack(self):
        f = mk_faction()
        factions = {"a": f}
        domains = {"harbor": mk_domain(utilization=9)}   # 9 ≥ 0.85×10
        stacks = {"harbor": mk_stack(count=0)}
        world = WorldState()
        found = False
        for seed in range(200):
            random.seed(seed)
            plan = select_faction_action(f, factions, domains, world, {}, stacks)
            if plan.action == "BuildProject" and plan.target_id == "harbor":
                found = True
                break
        assert found

    def test_faction_never_initiates_below_threshold_with_empty_stack(self):
        f = mk_faction()
        factions = {"a": f}
        domains = {"harbor": mk_domain(utilization=5)}   # 5 < 0.85×10 — cannot initiate
        stacks = {"harbor": mk_stack(count=0)}
        world = WorldState()
        for seed in range(200):
            random.seed(seed)
            plan = select_faction_action(f, factions, domains, world, {}, stacks)
            assert plan.action != "BuildProject"   # no build site, no near-cap initiation


# ── Mayor initiation ─────────────────────────────────────────────────────────────

class TestMayorInitiation:
    def test_mayor_initiates_in_factionless_domain(self):
        treasury = Treasury(gold=500)
        mayor = Mayor(action_points=1)
        stacks = {"harbor": mk_stack(count=0)}
        r = mayor_build_base("harbor", stacks, treasury, mayor)
        assert r.outcome == "decisive"
        s = stacks["harbor"]
        assert s.count == 1 and s.progress == 25   # initiated + one funded step (build_step 25)
