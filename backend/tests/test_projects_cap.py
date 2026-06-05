"""
test_projects_cap.py — Slice 1 of the projects rework: domain cap derivation.

cap = base_cap + Σ contribution(active base projects). base_cap is frozen at game
start from starting fill (Σ level × CAP_HEADROOM_MULT); the live cap is re-derived
each cycle by the runner.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from engine.models import Faction, Domain, Leader, Project, WorldState
from engine.cycle import run_cycle
from engine import formulas
from engine.formulas import base_cap_from_fill
from loaders import _freeze_base_caps
from serializer import (
    serialize_project, deserialize_project,
    serialize_domain, deserialize_domain,
)


def mk_faction(fid, dom, rating):
    return Faction(id=fid, name=fid, domain_primary=dom, rating=rating, health=75,
                   leader=Leader(name="L"))


def mk_domain(did="harbor", cap=999, base_cap=0):
    return Domain(id=did, name=did, cap=cap, base_cap=base_cap)


def mk_base_project(pid="harbor_base_1", dom="harbor", status="active", health=80):
    return Project(id=pid, name="Docks", domains=[dom], build_cost=0, build_time=4,
                   category="base", status=status, health=health)


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


# ── (b) no base projects → cap == base_cap ────────────────────────────────────

def test_no_base_projects_cap_equals_base_cap():
    world = WorldState(cycle=0)
    domains = {"harbor": mk_domain("harbor", base_cap=10)}
    factions = {"a": mk_faction("a", "harbor", 2.0)}
    run_cycle(world, factions, domains, projects={})
    assert domains["harbor"].cap == 10


# ── (c) contribution by health tier ───────────────────────────────────────────

@pytest.mark.parametrize("status,health,contrib", [
    ("active", 80, 2),          # intact
    ("damaged", 40, 1),         # damaged
    ("critical", 10, 0),        # critical
    ("under_construction", 0, 0),
    ("destroyed", 0, 0),
])
def test_cap_contribution_by_tier(status, health, contrib):
    world = WorldState(cycle=0)
    domains = {"harbor": mk_domain("harbor", base_cap=10)}
    factions = {"a": mk_faction("a", "harbor", 2.0)}
    projects = {"p": mk_base_project(status=status, health=health)}
    # No treasury → projects don't tick; cap still derives at cycle start.
    run_cycle(world, factions, domains, projects=projects)
    assert domains["harbor"].cap == 10 + contrib


# ── (d) re-derived each cycle ─────────────────────────────────────────────────

def test_cap_rederived_each_cycle():
    world = WorldState(cycle=0)
    domains = {"harbor": mk_domain("harbor", base_cap=10)}
    factions = {"a": mk_faction("a", "harbor", 2.0)}
    projects = {"p": mk_base_project(status="active", health=80)}
    run_cycle(world, factions, domains, projects=projects)
    assert domains["harbor"].cap == 12          # intact → +2
    projects["p"].status = "damaged"
    projects["p"].health = 40
    run_cycle(world, factions, domains, projects=projects)
    assert domains["harbor"].cap == 11          # damaged → +1, re-derived


# ── (e) CAP_HEADROOM_MULT is the single lever ─────────────────────────────────

def test_cap_headroom_constant(monkeypatch):
    monkeypatch.setattr(formulas, "CAP_HEADROOM_MULT", 2.0)
    assert formulas.base_cap_from_fill(10) == 20


# ── serializer round-trip ─────────────────────────────────────────────────────

def test_serializer_roundtrip_build_progress_and_base_cap():
    p = mk_base_project()
    p.build_progress = 3
    assert deserialize_project(serialize_project(p)).build_progress == 3

    d = mk_domain("harbor", base_cap=12)
    assert deserialize_domain(serialize_domain(d)).base_cap == 12
