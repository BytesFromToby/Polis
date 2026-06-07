"""
tests/test_projects_api.py — Projects API shape (game-ui_spec.md, Projects Panel).

The /projects list returns one base-project stack per domain (projects_spec v6). The
contract must expose count, completed, and progress — the UI derives the pooled count
and the in-flux front row from these.
"""
from __future__ import annotations

from api.schemas import BaseStackResponse
from engine.models import BaseProjectStack


def test_stack_response_contract_fields():
    fields = BaseStackResponse.model_fields
    for f in ("name", "domain", "domains", "count", "completed", "progress", "build_step"):
        assert f in fields


def test_stack_maps_into_response():
    """A stack with a damaged top serializes with count/completed/progress intact —
    mirrors the field mapping used by GET /projects."""
    s = BaseProjectStack(name="Docks", domains=["harbor"], count=3,
                         completed=True, progress=40, build_step=25)
    resp = BaseStackResponse(
        name=s.name, domain=s.domain, domains=list(s.domains),
        count=s.count, completed=s.completed, progress=s.progress,
        build_step=s.build_step, initiated_by=s.initiated_by,
    )
    assert resp.count == 3
    assert resp.completed is True
    assert resp.progress == 40
    assert resp.domain == "harbor"
