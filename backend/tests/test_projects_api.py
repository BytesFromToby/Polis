"""
tests/test_projects_api.py — Projects API shape (game-ui_spec.md, Projects Panel).

Guards the regression behind the "percent not updating" bug: the projects response
contract must expose build_progress, which the UI uses to compute under-construction
percent-complete (health stays 0 during construction, so the UI cannot use it).
"""
from __future__ import annotations

from api.schemas import ProjectResponse
from engine.models import Project


def test_project_response_contract_includes_build_progress():
    assert "build_progress" in ProjectResponse.model_fields


def test_project_maps_into_response_with_build_progress():
    """A mid-construction base project serializes with its build_progress intact —
    mirrors the field mapping used by GET /projects and /projects/catalog."""
    p = Project(
        id="trade_base_1", name="Docks", domains=["trade"],
        build_cost=0, build_time=4, category="base",
        status="under_construction", build_progress=2, health=0,
    )
    resp = ProjectResponse(
        id=p.id, name=p.name, domain=p.domain, category=p.category,
        status=p.status, health=p.health, build_progress=p.build_progress,
        build_cost=p.build_cost, build_time=p.build_time,
        faction_build_actions=p.faction_build_actions, cycles_built=p.cycles_built,
        maintenance_cost=p.maintenance_cost, tax_level=p.tax_level,
        initiated_by=p.initiated_by,
    )
    assert resp.build_progress == 2
    assert resp.status == "under_construction"
