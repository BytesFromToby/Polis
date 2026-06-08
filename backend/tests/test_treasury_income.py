"""
tests/test_treasury_income.py — Treasury income model (treasury_spec v3).

Income = BASE_INCOME (20) + TAX_OFFICE_INCOME (20) × completed civic Tax Offices.
The per-domain auto-tax is removed: factions/domains no longer generate income.
Also a regression for expenditure (guard payroll + maintenance) staying intact.
"""
from __future__ import annotations

from engine.mayor.treasury import process_treasury_step0
from engine.models import Treasury, Mayor, Faction, Leader, BaseProjectStack


def _office_stack(count: int, completed: bool = True, progress: float = 100.0) -> BaseProjectStack:
    return BaseProjectStack(name="Tax Office", domains=["civic"],
                            count=count, completed=completed, progress=progress)


def test_no_tax_offices_income_is_base():
    t = Treasury(gold=100)
    process_treasury_step0(t, Mayor(), {}, {}, base_stacks={})
    assert t.income_this_cycle == 20


def test_income_scales_with_completed_offices():
    t = Treasury(gold=100)
    base_stacks = {"civic": _office_stack(count=3)}   # 3 completed Tax Offices
    process_treasury_step0(t, Mayor(), {}, {}, base_stacks=base_stacks)
    assert t.income_this_cycle == 20 + 20 * 3   # 80


def test_building_top_not_counted():
    t = Treasury(gold=100)
    # count=3 with a building (incomplete) top over a pristine pool of 2 → active_count == 2
    base_stacks = {"civic": _office_stack(count=3, completed=False, progress=50.0)}
    process_treasury_step0(t, Mayor(), {}, {}, base_stacks=base_stacks)
    assert t.income_this_cycle == 20 + 20 * 2   # 60, building top excluded


def test_factions_generate_no_income():
    """Per-domain auto-tax removed: factions present, no Tax Offices → income is base only."""
    t = Treasury(gold=100)
    factions = {
        "a": Faction(id="a", name="A", domain_primary="trade", rating=4.0, leader=Leader(name="A")),
        "b": Faction(id="b", name="B", domain_primary="guilds", rating=5.0, leader=Leader(name="B")),
    }
    process_treasury_step0(t, Mayor(), factions, {}, base_stacks={})
    assert t.income_this_cycle == 20


def test_expenditure_guard_and_maintenance():
    """With gold covering costs: guard payroll 20 + maintenance 2 × active_count."""
    t = Treasury(gold=500)
    process_treasury_step0(t, Mayor(), {}, {}, active_project_count=3, base_stacks={})
    # guard 20 + maintenance 2*3=6 → 26 expenditure
    assert t.expenditure_this_cycle == 20 + 2 * 3
