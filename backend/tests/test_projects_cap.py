"""
test_projects_cap.py — domain cap derivation + maintenance on the base-project stack
model (projects_spec v6). cap = base_cap + stack_cap_contribution; base_cap frozen at
game start. Maintenance = 2 × active completed instances (building tops excluded).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.models import Faction, Domain, Leader, BaseProjectStack, WorldState, Mayor, Treasury
from engine.cycle import run_cycle
from engine import formulas
from engine.formulas import base_cap_from_fill
from engine.mayor.treasury import process_treasury_step0
from loaders import _freeze_base_caps


def mk_faction(fid, dom, rating):
    return Faction(id=fid, name=fid, domain_primary=dom, rating=rating, health=75,
                   leader=Leader(name="L"))


def mk_domain(did="harbor", cap=999, base_cap=0):
    return Domain(id=did, name=did, cap=cap, base_cap=base_cap)


def mk_stack(dom="harbor", count=0, completed=False, progress=0.0, build_step=25):
    return BaseProjectStack(name="Docks", domains=[dom], count=count,
                            completed=completed, progress=progress, build_step=build_step)


# ── (a) base_cap formula + authored cap ignored ───────────────────────────────

class TestBaseCap:
    def test_formula(self):
        assert base_cap_from_fill(10) == 12   # round(10 × 1.20)
        assert base_cap_from_fill(14) == 17   # round(16.8)

    def test_freeze_ignores_authored_cap(self):
        domains = {"harbor": mk_domain("harbor", cap=999)}
        domains["harbor"].utilization = 7     # Σ level at cycle 0
        _freeze_base_caps(domains)
        assert domains["harbor"].base_cap == round(7 * 1.20)   # 8
        assert domains["harbor"].cap == 8                       # authored 999 ignored


# ── (b) empty stack → cap == base_cap ─────────────────────────────────────────

def test_empty_stack_cap_equals_base_cap():
    world = WorldState(cycle=0)
    domains = {"harbor": mk_domain("harbor", base_cap=10)}
    factions = {"a": mk_faction("a", "harbor", 2.0)}
    run_cycle(world, factions, domains, base_stacks={"harbor": mk_stack(count=0)})
    assert domains["harbor"].cap == 10


# ── (c) all-pristine → +count × 2 ─────────────────────────────────────────────

def test_pristine_stack_adds_count_times_two():
    world = WorldState(cycle=0)
    domains = {"harbor": mk_domain("harbor", base_cap=10)}
    factions = {"a": mk_faction("a", "harbor", 2.0)}
    run_cycle(world, factions, domains,
              base_stacks={"harbor": mk_stack(count=3, completed=True, progress=100)})
    assert domains["harbor"].cap == 10 + 6


# ── (d) damaged top drops cap; building top adds 0 ────────────────────────────

def test_damaged_top_drops_cap():
    world = WorldState(cycle=0)
    domains = {"harbor": mk_domain("harbor", base_cap=10)}
    factions = {"a": mk_faction("a", "harbor", 2.0)}
    # count=2 pristine baseline would be +4. Damaged top into 21–50 → +3 (drop 1).
    run_cycle(world, factions, domains,
              base_stacks={"harbor": mk_stack(count=2, completed=True, progress=40)})
    assert domains["harbor"].cap == 10 + 3
    # Into 1–20 → +2 (drop 2 from the +4 pristine baseline).
    run_cycle(world, factions, domains,
              base_stacks={"harbor": mk_stack(count=2, completed=True, progress=10)})
    assert domains["harbor"].cap == 10 + 2


def test_building_top_adds_zero():
    world = WorldState(cycle=0)
    domains = {"harbor": mk_domain("harbor", base_cap=10)}
    factions = {"a": mk_faction("a", "harbor", 2.0)}
    for prog in (10, 50, 90):
        run_cycle(world, factions, domains,
                  base_stacks={"harbor": mk_stack(count=1, completed=False, progress=prog)})
        assert domains["harbor"].cap == 10   # lone building top contributes 0


# ── (e) CAP_HEADROOM_MULT is the single lever ─────────────────────────────────

def test_cap_headroom_constant(monkeypatch):
    monkeypatch.setattr(formulas, "CAP_HEADROOM_MULT", 2.0)
    assert formulas.base_cap_from_fill(10) == 20


# ── (f) maintenance = 2 × active completed count ──────────────────────────────

def test_maintenance_formula_per_active_count():
    t = Treasury(gold=500)
    results = process_treasury_step0(t, Mayor(), {}, {}, active_project_count=3)
    maint = next(r for r in results if r.action == "ProjectMaintenance")
    assert maint.delta == -6.0          # 2 × 3
    assert maint.outcome == "no_op"


def test_runner_counts_active_from_stacks_excluding_building():
    world = WorldState(cycle=0)
    domains = {"harbor": mk_domain("harbor", base_cap=10),
               "trade": mk_domain("trade", base_cap=10)}
    factions = {"a": mk_faction("a", "harbor", 2.0)}
    mayor, treasury = Mayor(), Treasury(gold=500)
    stacks = {
        "harbor": mk_stack("harbor", count=3, completed=True, progress=100),  # 3 active
        "trade": mk_stack("trade", count=2, completed=False, progress=50),    # 1 active (top building)
    }
    result = run_cycle(world, factions, domains, mayor=mayor, treasury=treasury, base_stacks=stacks)
    maint = next(e for e in result.events if e.action == "ProjectMaintenance")
    assert "4 projects" in maint.narrative      # 3 + 1, building top excluded


def test_maintenance_skipped_when_broke():
    t = Treasury(gold=25)   # 20 guard leaves 5; maintenance 6 unaffordable
    results = process_treasury_step0(t, Mayor(), {}, {}, active_project_count=3)
    maint = next(r for r in results if r.action == "ProjectMaintenance")
    assert maint.outcome == "fail"
    assert t.gold == 5      # nothing deducted for maintenance
