"""
tests/test_base_project_description.py — per-base-project one-line description
(audience_spec.md — BuildProject buildable info). Single source of truth for the effect text.
"""
from __future__ import annotations

from engine.projects import base_project_description
from engine.projects.processing import BASE_PROJECT_NAMES


def test_description_for_every_base_project():
    for domain_id in BASE_PROJECT_NAMES:
        desc = base_project_description(domain_id)
        assert isinstance(desc, str) and desc.strip()
        assert "\n" not in desc          # one line


def test_unknown_domain_returns_default():
    desc = base_project_description("not_a_domain")
    assert isinstance(desc, str) and desc.strip()
    assert "\n" not in desc
