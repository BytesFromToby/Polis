"""
tests/test_treasury_insolvency.py — Insolvency model (treasury_spec v3).

When expenditure can't be covered: gold clamps at 0 and the shortfall is paid as damage
to random NON-civic base-project instances (Tax Offices excluded). Destroyed instances
drop active_count, lowering maintenance — self-balancing. No v2 bankruptcy-ladder effect.
"""
from __future__ import annotations
import random

from engine.mayor.treasury import process_treasury_step0
from engine.models import Treasury, Mayor, BaseProjectStack


def _stack(name, domain, count, progress=100.0, completed=True):
    return BaseProjectStack(name=name, domains=[domain], count=count,
                            completed=completed, progress=progress)


def test_gold_clamps_at_zero():
    # gold 0 + base income 20 = 20; required = 20 guard + 2*30 maint = 80 → shortfall.
    t = Treasury(gold=0)
    process_treasury_step0(t, Mayor(), {}, {}, active_project_count=30, base_stacks={})
    assert t.gold == 0   # never negative


def test_shortfall_damages_noncivic_not_civic():
    t = Treasury(gold=0)
    base_stacks = {
        "harbor": _stack("Docks", "harbor", count=2, progress=100.0),
        "civic": _stack("Tax Office", "civic", count=1, progress=100.0),
    }
    # income = 20 + 20 (1 office) = 40; required = 20 + 2*30 = 80 → shortfall 40.
    process_treasury_step0(t, Mayor(), {}, {}, active_project_count=30,
                           base_stacks=base_stacks, rng=random.Random(1))
    assert t.gold == 0
    assert base_stacks["harbor"].progress < 100          # non-civic damaged
    # civic Tax Office untouched
    assert base_stacks["civic"].count == 1
    assert base_stacks["civic"].progress == 100.0


def test_large_shortfall_destroys_instance_lowering_maintenance():
    t = Treasury(gold=0)
    base_stacks = {"harbor": _stack("Docks", "harbor", count=2, progress=100.0)}
    before = base_stacks["harbor"].active_count()         # 2
    # income 20 (no offices); required = 20 + 2*61 = 142 → shortfall 122 (> 100+1 → destroys).
    process_treasury_step0(t, Mayor(), {}, {}, active_project_count=61,
                           base_stacks=base_stacks, rng=random.Random(1))
    after = base_stacks["harbor"].active_count()
    assert after < before                                 # an instance destroyed
    # maintenance scales with active_count, so it is lower next cycle
    assert 2 * after < 2 * before


def test_no_bankruptcy_ladder_effects():
    t = Treasury(gold=0)
    mayor = Mayor()
    rep_before = mayor.get_reputation("the_public")
    results = process_treasury_step0(t, mayor, {}, {}, active_project_count=30, base_stacks={})
    # No v2 ladder: no guard/maintenance "fail" outcomes, and no -20 public-rep removal hit.
    assert not any(r.outcome == "fail" for r in results)
    assert any(r.action == "Insolvency" for r in results)
    assert mayor.get_reputation("the_public") == rep_before
