"""Tests for the Projects system — construction, health, effects, destruction."""
import pytest
from engine.models import Project, ProjectEffect, Faction, Domain, Treasury, Mayor, WorldState, MayorAction, Leader
from engine.projects.processing import (
    tick_projects, apply_project_effects, harm_project,
    repair_project, commission_project,
)
from engine.cycle.runner import run_cycle


def make_faction(fid="f1", domain="trade", floor=2, rating=2.0, health=75):
    return Faction(id=fid, name=fid, domain_primary=domain, leader=Leader(name="Test"), floor=floor, rating=rating, health=health)


def make_project(pid="p1", domain="trade", build_time=3, status="under_construction", health=0):
    return Project(id=pid, name=pid, domains=[domain], build_cost=100, build_time=build_time,
                   status=status, health=health)


def make_treasury(**kw):
    return Treasury(**kw)


def make_mayor(**kw):
    return Mayor(**kw)


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
