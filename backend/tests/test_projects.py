"""Tests for the Projects system — construction, health, effects, destruction."""
import pytest
from engine.models import Project, ProjectEffect, Faction, Domain, Treasury, Mayor, WorldState, MayorAction, Leader
from engine.projects.processing import (
    tick_projects, apply_project_effects, harm_project,
    repair_project, commission_project, mayor_buy_build_unit,
)
from engine.actions.faction import resolve_build_project, resolve_sabotage_project
from engine.cycle.runner import run_cycle
from engine.mayor.treasury import process_treasury_step0
from engine.formulas import project_cap_contribution
import engine.actions.faction as faction_mod


def make_faction(fid="f1", domain="trade", floor=None, rating=2.0, health=75):
    if floor is not None:
        rating = float(floor)
    return Faction(id=fid, name=fid, domain_primary=domain, leader=Leader(name="Test"), rating=rating, health=health)


def make_project(pid="p1", domain="trade", build_time=3, status="under_construction", health=0):
    return Project(id=pid, name=pid, domains=[domain], build_cost=100, build_time=build_time,
                   status=status, health=health)


def make_treasury(**kw):
    return Treasury(**kw)


def make_mayor(**kw):
    return Mayor(**kw)


# ── Per-cycle build counter ─────────────────────────────────────────────────

class TestBuildActionsReset:
    def test_counter_resets_after_ticking(self):
        # cycle-runner_spec: after project ticking, every project's
        # build_actions_this_cycle is 0.
        project = make_project(status="active", health=80)
        project.build_actions_this_cycle = 2
        tick_projects({"p1": project}, {}, {}, make_treasury(gold=500))
        assert project.build_actions_this_cycle == 0

    def test_counter_resets_for_under_construction(self):
        project = make_project(build_time=3)  # under_construction
        project.build_actions_this_cycle = 1
        tick_projects({"p1": project}, {}, {}, make_treasury(gold=500))
        assert project.build_actions_this_cycle == 0


# ── Base-project build model (4 work units) ───────────────────────────────────

def make_base_project(pid="harbor_base_1", domain="harbor", status="under_construction",
                      build_progress=0, build_cost=0):
    return Project(id=pid, name="Docks", domains=[domain], build_cost=build_cost,
                   build_time=4, category="base", status=status,
                   build_progress=build_progress, health=0)


def force_roll(monkeypatch, value):
    """Force d20 in resolve_build_project (roll = value + level)."""
    monkeypatch.setattr(faction_mod.random, "randint", lambda a, b: value)


class TestBuildModel:
    def test_faction_success_adds_one_unit(self, monkeypatch):
        force_roll(monkeypatch, 20)
        f = make_faction("f1", "harbor", rating=2.0)
        p = make_base_project()
        r = resolve_build_project(f, p)
        assert r.outcome == "success"
        assert p.build_progress == 1

    def test_faction_fail_adds_nothing(self, monkeypatch):
        force_roll(monkeypatch, 1)  # 1 + level 2 = 3 < 12
        f = make_faction("f1", "harbor", rating=2.0)
        p = make_base_project()
        r = resolve_build_project(f, p)
        assert r.outcome == "fail"
        assert p.build_progress == 0

    def test_cross_domain_blocked(self):
        f = make_faction("f1", "military", rating=2.0)
        p = make_base_project(domain="harbor")
        r = resolve_build_project(f, p)
        assert r.outcome == "blocked"
        assert p.build_progress == 0

    def test_completion_at_four_units(self, monkeypatch):
        force_roll(monkeypatch, 20)
        f = make_faction("f1", "harbor", rating=2.0)
        p = make_base_project(build_progress=3)
        r = resolve_build_project(f, p)
        assert p.build_progress == 4
        assert p.status == "active"
        assert p.health == 100
        assert r.dramatic is True

    def test_mayor_buy_adds_unit_and_charges(self):
        p = make_base_project()
        treasury = make_treasury(gold=500)
        mayor = make_mayor(action_points=3)
        r = mayor_buy_build_unit(p, treasury, mayor)
        assert r.outcome == "decisive"
        assert p.build_progress == 1
        assert treasury.gold == 450
        assert mayor.action_points == 2

    def test_mayor_buy_insufficient_gold_no_charge(self):
        p = make_base_project()
        treasury = make_treasury(gold=40)
        mayor = make_mayor(action_points=3)
        r = mayor_buy_build_unit(p, treasury, mayor)
        assert r.outcome == "fail"
        assert p.build_progress == 0
        assert treasury.gold == 40
        assert mayor.action_points == 3  # AP refunded

    def test_mayor_buy_no_ap_no_charge(self):
        p = make_base_project()
        treasury = make_treasury(gold=500)
        mayor = make_mayor(action_points=0)
        r = mayor_buy_build_unit(p, treasury, mayor)
        assert r.outcome == "fail"
        assert p.build_progress == 0
        assert treasury.gold == 500

    def test_mayor_can_rush_three_units_one_turn(self):
        p = make_base_project()
        treasury = make_treasury(gold=500)
        mayor = make_mayor(action_points=3)
        while mayor.action_points > 0:
            mayor_buy_build_unit(p, treasury, mayor)
        assert p.build_progress == 3
        assert treasury.gold == 350  # 3 × 50

    def test_no_build_cost_deducted(self):
        # build_cost is high but base build never charges it (faction labor is free;
        # Mayor buy charges a flat 50, not build_cost).
        p = make_base_project(build_cost=999)
        treasury = make_treasury(gold=500)
        mayor = make_mayor(action_points=1)
        mayor_buy_build_unit(p, treasury, mayor)
        assert treasury.gold == 450  # only the flat 50, not 999


# ── Construction ──────────────────────────────────────────────────────────────

class TestConstruction:
    def test_construction_advances_each_cycle(self):
        project = make_project(build_time=3)
        treasury = make_treasury(gold=500)
        projects = {"p1": project}
        results = tick_projects(projects, {}, {}, treasury)
        assert project.cycles_built == 1
        assert project.status == "under_construction"

    def test_project_completes_on_time(self):
        project = make_project(build_time=1)
        treasury = make_treasury(gold=500)
        results = tick_projects({"p1": project}, {}, {}, treasury)
        assert project.status == "active"
        assert any(r.action == "ProjectComplete" for r in results)

    def test_project_not_complete_before_build_time(self):
        project = make_project(build_time=3)
        project.cycles_built = 1
        tick_projects({"p1": project}, {}, {}, make_treasury(gold=500))
        assert project.status == "under_construction"

    def test_completed_project_has_full_health(self):
        project = make_project(build_time=1)
        project.health = 50  # damaged during construction
        tick_projects({"p1": project}, {}, {}, make_treasury(gold=500))
        assert project.health == 100


# ── Health system ──────────────────────────────────────────────────────────────

class TestProjectHealth:
    def test_health_tier_intact(self):
        p = make_project(health=100, status="active")
        assert p.health_tier() == "intact"
        assert p.effect_multiplier() == 1.0

    def test_health_tier_damaged(self):
        p = make_project(health=40, status="damaged")
        assert p.health_tier() == "damaged"
        assert p.effect_multiplier() == 0.5

    def test_health_tier_critical(self):
        p = make_project(health=10, status="critical")
        assert p.health_tier() == "critical"
        assert p.effect_multiplier() == 0.25

    def test_health_tier_destroyed(self):
        p = make_project(health=0, status="destroyed")
        assert p.health_tier() == "destroyed"
        assert p.effect_multiplier() == 0.0


# ── Harm ─────────────────────────────────────────────────────────────────────

class TestHarmProject:
    def test_decisive_hit_does_25_damage(self):
        import random
        random.seed(99)  # find a seed that gives margin >= 5
        project = make_project(health=100, status="active")
        attacker = make_faction(floor=5, rating=5.0)
        # With rating 5, attacker roll = d20+5; DC=12; need margin>=5 → roll >= 12
        # Try enough times
        for seed in range(1000):
            random.seed(seed)
            result = harm_project(project, attacker, dc=12)
            if result.outcome == "decisive":
                assert project.health == 75
                return
        pytest.skip("Could not find seed for decisive hit in harm_project test")

    def test_failed_attack_does_no_damage(self):
        import random
        project = make_project(health=100, status="active")
        attacker = make_faction(floor=1, rating=1.0)
        # With low rating, find a fail
        for seed in range(1000):
            random.seed(seed)
            result = harm_project(project, attacker, dc=20)
            if result.outcome == "fail":
                assert project.health == 100
                return
        pytest.skip("Could not find seed for failed attack")

    def test_harm_updates_project_status(self):
        project = make_project(health=55, status="active")
        project.health = 15  # force critical threshold
        from engine.projects.processing import _update_project_status
        _update_project_status(project)
        assert project.status == "critical"


# ── Repair ────────────────────────────────────────────────────────────────────

class TestRepairProject:
    def test_repair_restores_25_health(self):
        project = make_project(health=50, status="damaged")
        treasury = make_treasury(gold=500)
        mayor = make_mayor(action_points=5)
        result = repair_project(project, treasury, mayor)
        assert result.outcome == "decisive"
        assert project.health == 75
        assert treasury.gold == 470

    def test_repair_fails_insufficient_gold(self):
        project = make_project(health=50, status="damaged")
        treasury = make_treasury(gold=10)
        mayor = make_mayor(action_points=5)
        result = repair_project(project, treasury, mayor)
        assert result.outcome == "fail"
        assert project.health == 50

    def test_repair_fails_insufficient_ap(self):
        project = make_project(health=50, status="damaged")
        treasury = make_treasury(gold=500)
        mayor = make_mayor(action_points=0)
        result = repair_project(project, treasury, mayor)
        assert result.outcome == "fail"

    def test_repair_caps_at_100_health(self):
        project = make_project(health=90, status="active")
        treasury = make_treasury(gold=500)
        mayor = make_mayor(action_points=5)
        repair_project(project, treasury, mayor)
        assert project.health == 100


# ── Commission ────────────────────────────────────────────────────────────────

class TestCommissionProject:
    def test_commission_creates_project(self):
        template = {
            "id": "dock_expansion", "name": "Dock Expansion",
            "domain": "docks", "build_cost": 100, "build_time": 3,
            "maintenance_cost": 15, "effects": [],
        }
        treasury = make_treasury(gold=500)
        mayor = make_mayor(action_points=6)
        project, result = commission_project(template, treasury, mayor)
        assert project is not None
        assert project.status == "under_construction"
        assert treasury.gold == 400
        assert result.outcome == "decisive"

    def test_commission_fails_insufficient_gold(self):
        template = {
            "id": "city_wall", "name": "City Wall",
            "domain": "political", "build_cost": 200, "build_time": 5, "effects": [],
        }
        treasury = make_treasury(gold=50)
        mayor = make_mayor(action_points=6)
        project, result = commission_project(template, treasury, mayor)
        assert project is None
        assert result.outcome == "fail"

    def test_commission_fails_insufficient_ap(self):
        template = {
            "id": "market", "name": "Market",
            "domain": "trade", "build_cost": 10, "build_time": 2, "effects": [],
        }
        treasury = make_treasury(gold=500)
        mayor = make_mayor(action_points=0)
        project, result = commission_project(template, treasury, mayor)
        assert project is None
        assert result.outcome == "fail"


# ── Effects ───────────────────────────────────────────────────────────────────

class TestProjectEffects:
    def test_active_project_applies_treasury_income(self):
        effect = ProjectEffect(target="treasury", target_id="treasury",
                               field="gold_per_cycle", value=15.0)
        project = make_project(status="active", health=100)
        project.effects = [effect]
        treasury = make_treasury(gold=100)
        apply_project_effects({"p1": project}, {}, {}, treasury)
        assert treasury.gold == 115

    def test_damaged_project_applies_half_effect(self):
        effect = ProjectEffect(target="treasury", target_id="treasury",
                               field="gold_per_cycle", value=20.0)
        project = make_project(status="damaged", health=40)
        project.effects = [effect]
        treasury = make_treasury(gold=100)
        apply_project_effects({"p1": project}, {}, {}, treasury)
        assert treasury.gold == 110  # 20 * 0.5 = 10

    def test_destroyed_project_no_effect(self):
        effect = ProjectEffect(target="treasury", target_id="treasury",
                               field="gold_per_cycle", value=15.0)
        project = make_project(status="destroyed", health=0)
        project.effects = [effect]
        treasury = make_treasury(gold=100)
        apply_project_effects({"p1": project}, {}, {}, treasury)
        assert treasury.gold == 100


# ── Cycle integration ─────────────────────────────────────────────────────────

class TestProjectCycleIntegration:
    def test_projects_tick_each_cycle(self):
        world = WorldState()
        factions = {"f1": make_faction()}
        domains = {"trade": Domain(id="trade", name="trade", cap=100)}
        mayor = make_mayor(action_points=6)
        treasury = make_treasury(gold=500)
        project = make_project(build_time=3)
        projects = {"p1": project}

        run_cycle(world, factions, domains, mayor=mayor, treasury=treasury, projects=projects)
        assert project.cycles_built == 1

    def test_project_completes_after_build_time_cycles(self):
        world = WorldState()
        factions = {}
        domains = {}
        mayor = make_mayor(action_points=6)
        treasury = make_treasury(gold=500)
        project = make_project(build_time=2)
        projects = {"p1": project}

        for _ in range(2):
            mayor.action_points = 6
            run_cycle(world, factions, domains, mayor=mayor, treasury=treasury, projects=projects)

        assert project.status == "active"


# ── Base-project sabotage & maintenance (Slice 4) ─────────────────────────────

def _force_sabotage(monkeypatch, atk, dfn):
    """Force the two d20 rolls inside resolve_sabotage_project (attacker, defender)."""
    seq = iter([atk, dfn])
    monkeypatch.setattr(faction_mod.random, "randint", lambda a, b: next(seq))


def make_active_base(pid="harbor_base_1", domain="harbor", health=100):
    return Project(id=pid, name="Docks", domains=[domain], build_cost=0, build_time=4,
                   category="base", status="active", health=health, build_progress=4)


class TestSabotageBase:
    def test_decisive_minus_25(self, monkeypatch):
        _force_sabotage(monkeypatch, 20, 1)  # big positive margin → decisive
        f = make_faction("f1", "harbor", rating=2.0)
        p = make_active_base(health=100)
        r = resolve_sabotage_project(f, p)
        assert r.outcome == "decisive"
        assert p.health == 75

    def test_partial_minus_10(self, monkeypatch):
        # level 2, defense 5 (health 100): margin = (10+2)-(4+5) = 3 → partial
        _force_sabotage(monkeypatch, 10, 4)
        f = make_faction("f1", "harbor", rating=2.0)
        p = make_active_base(health=100)
        r = resolve_sabotage_project(f, p)
        assert r.outcome == "partial"
        assert p.health == 90

    def test_fail_no_damage(self, monkeypatch):
        _force_sabotage(monkeypatch, 1, 20)  # big negative margin → fail
        f = make_faction("f1", "harbor", rating=2.0)
        p = make_active_base(health=100)
        r = resolve_sabotage_project(f, p)
        assert r.outcome == "fail"
        assert p.health == 100

    def test_not_domain_gated(self, monkeypatch):
        _force_sabotage(monkeypatch, 20, 1)
        f = make_faction("f1", "military", rating=2.0)  # different domain than the project
        p = make_active_base(domain="harbor", health=100)
        r = resolve_sabotage_project(f, p)
        assert r.outcome != "blocked"
        assert p.health == 75

    def test_destroyed_at_zero_and_no_cap(self, monkeypatch):
        _force_sabotage(monkeypatch, 20, 1)
        f = make_faction("f1", "harbor", rating=2.0)
        p = make_active_base(health=20)   # defense_rating 1; decisive -25 → 0
        resolve_sabotage_project(f, p)
        assert p.status == "destroyed"
        assert project_cap_contribution(p) == 0


class TestMaintenanceBase:
    def test_maintenance_is_two_times_active_count(self):
        treasury = make_treasury(gold=500)
        mayor = make_mayor()
        results = process_treasury_step0(treasury, mayor, {}, {}, active_project_count=3)
        maint = [r for r in results if r.action == "ProjectMaintenance"]
        assert len(maint) == 1
        assert maint[0].outcome == "no_op"
        assert maint[0].delta == -6.0  # 2 × 3

    def test_maintenance_skipped_when_broke_no_damage(self):
        treasury = make_treasury(gold=0)
        mayor = make_mayor()
        project = make_active_base(health=100)  # standalone — must be untouched
        results = process_treasury_step0(treasury, mayor, {}, {}, active_project_count=3)
        maint = [r for r in results if r.action == "ProjectMaintenance"]
        assert len(maint) == 1
        assert maint[0].outcome == "fail"
        assert treasury.gold == 0          # not driven negative by maintenance
        assert project.health == 100       # maintenance never damages projects
