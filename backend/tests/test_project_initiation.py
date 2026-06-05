"""
test_project_initiation.py — Slice 3 of the projects rework: base-project initiation.

Mayor may break ground anywhere; NPC factions break ground under near-cap pressure
(own domain utilization ≥ 85% of cap, none already under construction). At most one
base project per domain may be under construction at a time.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
import pytest
from engine.models import Faction, Domain, Leader, Project, WorldState, Treasury, Mayor
from engine.npc import select_faction_action
from engine.npc.behavior import _can_initiate_base
from engine.projects.processing import initiate_base_project, mayor_build_base


def mk_faction(fid="a", dom="harbor", rating=2.0):
    return Faction(id=fid, name=fid, domain_primary=dom, rating=rating, health=75,
                   leader=Leader(name="L"))


def mk_domain(did="harbor", cap=10, base_cap=10, utilization=9.0):
    return Domain(id=did, name=did, cap=cap, base_cap=base_cap, utilization=utilization)


def mk_under_construction(did="harbor"):
    return Project(id=f"{did}_base_1", name="Docks", domains=[did], build_cost=0,
                   build_time=4, category="base", status="under_construction")


# ── initiate_base_project ──────────────────────────────────────────────────────

class TestInitiateHelper:
    def test_creates_instance(self):
        projects = {}
        p = initiate_base_project("harbor", projects, "mayor")
        assert p is not None
        assert p.status == "under_construction"
        assert p.build_progress == 0
        assert p.name == "Docks"
        assert p.category == "base"
        assert p.id in projects

    def test_second_initiation_in_same_domain_refused(self):
        projects = {}
        initiate_base_project("harbor", projects, "mayor")
        assert initiate_base_project("harbor", projects, "mayor") is None

    def test_other_domain_still_allowed(self):
        projects = {}
        initiate_base_project("harbor", projects, "mayor")
        assert initiate_base_project("trade", projects, "mayor") is not None


# ── Near-cap eligibility ───────────────────────────────────────────────────────

class TestEligibility:
    def test_eligible_when_near_cap_none_in_progress(self):
        f = mk_faction()
        domains = {"harbor": mk_domain(utilization=9)}
        assert _can_initiate_base(f, domains, {}) is True

    def test_not_eligible_below_threshold(self):
        f = mk_faction()
        domains = {"harbor": mk_domain(utilization=5)}  # 5 < 0.85×10
        assert _can_initiate_base(f, domains, {}) is False

    def test_not_eligible_when_one_under_construction(self):
        f = mk_faction()
        domains = {"harbor": mk_domain(utilization=9)}
        projects = {"harbor_base_1": mk_under_construction()}
        assert _can_initiate_base(f, domains, projects) is False


# ── Faction selection ──────────────────────────────────────────────────────────

class TestFactionInitiation:
    def test_faction_can_select_initiation_when_near_cap(self):
        f = mk_faction()
        factions = {"a": f}
        domains = {"harbor": mk_domain(utilization=9)}
        world = WorldState()
        found = False
        for seed in range(200):
            random.seed(seed)
            plan = select_faction_action(f, factions, domains, world, {})
            if plan.action == "BuildProject" and (plan.target_id or "").startswith("new_base:"):
                found = True
                break
        assert found

    def test_faction_never_initiates_when_one_under_construction(self):
        f = mk_faction()
        factions = {"a": f}
        domains = {"harbor": mk_domain(utilization=9)}
        projects = {"harbor_base_1": mk_under_construction()}
        world = WorldState()
        for seed in range(200):
            random.seed(seed)
            plan = select_faction_action(f, factions, domains, world, projects)
            assert not (plan.action == "BuildProject"
                        and (plan.target_id or "").startswith("new_base:"))


# ── Mayor initiation ───────────────────────────────────────────────────────────

class TestMayorInitiation:
    def test_mayor_initiates_in_factionless_domain(self):
        projects = {}
        treasury = Treasury(gold=500)
        mayor = Mayor(action_points=1)
        r = mayor_build_base("harbor", projects, treasury, mayor)
        assert r.outcome == "decisive"
        base = [p for p in projects.values() if p.category == "base"]
        assert len(base) == 1
        assert base[0].build_progress == 1  # initiated + one funded unit
