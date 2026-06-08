"""
tests/test_deal_ticking.py — active deals decrement and expire each cycle (audience_spec
Deal Lifecycle). Regression for tick_deals never being wired into run_cycle.
"""
from __future__ import annotations

from engine.models import WorldState, Mayor, Faction, Leader, Deal, DealTerm
from engine.cycle import run_cycle


def _faction():
    return Faction(id="f1", name="The Companions", domain_primary="military",
                   rating=3.0, leader=Leader(name="Captain"))


def _deal(cycles_remaining=3):
    # A mayor-side-only deal (no committed_action faction term) so no compliance
    # suspension interferes — pure cycle decrement.
    return Deal(
        id="d1", faction_id="f1",
        mayor_terms=[DealTerm(type="tax_exemption", duration=cycles_remaining)],
        faction_terms=[],
        cycles_remaining=cycles_remaining, total_duration=cycles_remaining,
    )


def _run(mayor):
    world = WorldState()
    factions = {"f1": _faction()}
    run_cycle(world, factions, {}, mayor=mayor, treasury=None)


def test_active_deal_decrements_each_cycle():
    mayor = Mayor()
    mayor.deals["d1"] = _deal(cycles_remaining=3)
    _run(mayor)
    assert mayor.deals["d1"].cycles_remaining == 2
    _run(mayor)
    assert mayor.deals["d1"].cycles_remaining == 1


def test_deal_expires_to_fulfilled_at_zero():
    mayor = Mayor()
    mayor.deals["d1"] = _deal(cycles_remaining=1)
    _run(mayor)
    d = mayor.deals["d1"]
    assert d.cycles_remaining <= 0
    assert d.status == "fulfilled"
