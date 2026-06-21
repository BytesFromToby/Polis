"""
tests/test_difficulty_bite.py — difficulty actually changes per-cycle behavior (balance_spec
Slice 2). Where Slice 1 only proved NORMAL reproduces history, here we prove EASY/HARD diverge
on the threaded per-cycle path: treasury income, unrest easing, population growth, removal trigger.
"""
from __future__ import annotations

from engine.balance import EASY, NORMAL, HARD
from engine.models import ThePublic, Treasury, Mayor
from engine.needs.chain import ChainOutput
from engine.needs.drift import apply_needs
from engine.mayor.treasury import _calc_income
from engine.special.moneylender import process_moneylender


def out_with(**kw):
    base = dict(fed_target=60.0, happy_target=50.0, wine_happy=0.0, raw=0.0, units={})
    base.update(kw)
    return ChainOutput(**base)


# ── Treasury income ──────────────────────────────────────────────────────────────

def test_income_scales_with_difficulty():
    assert _calc_income(None, EASY) == EASY.base_income == 30
    assert _calc_income(None, NORMAL) == NORMAL.base_income == 20
    assert _calc_income(None, HARD) == HARD.base_income == 12
    assert _calc_income(None, EASY) > _calc_income(None, HARD)


# ── Unrest easing (asymmetric memory) ────────────────────────────────────────────

def _ease(profile):
    """Calm city with elevated unrest → eases toward the lower target by profile.unrest_ease."""
    p = ThePublic(unrest=50, fed=60, happy=60, piety=50, support=0)
    apply_needs(p, out_with(fed_target=60.0, happy_target=60.0), factions=None, balance=profile)
    return p.unrest


def test_unrest_eases_per_difficulty():
    assert _ease(EASY) == 50 - EASY.unrest_ease    # 44 — calms fastest
    assert _ease(NORMAL) == 50 - NORMAL.unrest_ease  # 46
    assert _ease(HARD) == 50 - HARD.unrest_ease     # 48 — grudges linger
    assert _ease(EASY) < _ease(NORMAL) < _ease(HARD)


# ── Population growth ────────────────────────────────────────────────────────────

def _grow(profile):
    p = ThePublic(population=10_000, fed=100, health=100, happy=60, piety=50, support=0)
    apply_needs(p, out_with(fed_target=100.0, happy_target=60.0), factions=None, balance=profile)
    return p.population


def test_population_grows_per_difficulty():
    assert _grow(EASY) == round(10_000 * (1 + EASY.pop_growth))    # 10_300
    assert _grow(HARD) == round(10_000 * (1 + HARD.pop_growth))    # 10_150
    assert _grow(EASY) > _grow(NORMAL) > _grow(HARD) > 10_000


# ── Removal coalition trigger threshold ──────────────────────────────────────────

def _angry(profile, debt=600):
    t = Treasury()
    t.debt = debt
    results = process_moneylender(t, Mayor(), {}, balance=profile)
    return any(r.action == "MoneylenderAngry" for r in results)


def test_removal_threshold_per_difficulty():
    # Debt of 600 is past HARD's removal_threshold (500) but under NORMAL (800) and EASY (1200).
    assert _angry(HARD) is True
    assert _angry(NORMAL) is False
    assert _angry(EASY) is False
