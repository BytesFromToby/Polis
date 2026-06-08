"""
tests/test_civic_domain.py — the faction-less civic ("Public Treasury") domain and
its buildable Tax Office (treasury_spec v3).

Covers: the base-project name, the authored cap surviving the freeze, building a Tax
Office at standard cost, and Tax Offices not moving any domain's cap.
"""
from __future__ import annotations

from loaders import load_state_from_json
from engine.models import Mayor, Treasury, WorldState
from engine.projects.processing import base_project_name, new_base_stacks, mayor_build_base
from engine.cycle.runner import run_cycle


def test_civic_base_project_name():
    assert base_project_name("civic") == "Tax Office"


def test_civic_loads_with_authored_cap():
    _, _, domains = load_state_from_json("data")
    assert "civic" in domains
    assert domains["civic"].cap == 12      # authored, not frozen to 0
    assert domains["civic"].utilization == 0


def _build_one_tax_office(base_stacks, treasury, mayor):
    """Drive mayor_build_base on civic until the top Tax Office completes."""
    for _ in range(12):  # safety bound
        if base_stacks["civic"].completed and base_stacks["civic"].progress >= 100:
            break
        mayor_build_base("civic", base_stacks, treasury, mayor)


def test_tax_office_builds_at_standard_cost():
    _, _, domains = load_state_from_json("data")
    base_stacks = new_base_stacks(domains)
    assert "civic" in base_stacks                       # auto-created from BASE_PROJECT_NAMES
    mayor = Mayor(action_points=10)
    treasury = Treasury(gold=1000)
    gold_before, ap_before = treasury.gold, mayor.action_points

    # Break ground: standard base-project cost is 50 gold + 1 AP.
    mayor_build_base("civic", base_stacks, treasury, mayor)
    assert treasury.gold == gold_before - 50
    assert mayor.action_points == ap_before - 1
    assert base_stacks["civic"].count >= 1

    _build_one_tax_office(base_stacks, treasury, mayor)
    assert base_stacks["civic"].active_count() == 1     # one completed Tax Office


def test_tax_office_does_not_move_caps():
    world = WorldState()
    _, factions, domains = load_state_from_json("data")
    base_stacks = new_base_stacks(domains)
    mayor = Mayor(action_points=10)
    treasury = Treasury(gold=1000)
    _build_one_tax_office(base_stacks, treasury, mayor)

    guilds_cap_before = domains["guilds"].cap
    run_cycle(world, factions, domains, mayor=mayor, treasury=treasury, base_stacks=base_stacks)

    assert domains["civic"].cap == 12                   # civic cap unchanged by Tax Offices
    assert domains["guilds"].cap == guilds_cap_before   # influence domain unaffected
