"""
tests/test_balance.py — the balance dial registry (balance_spec.md).

Two jobs:
  1. Lock the refactor: NORMAL must reproduce the pre-extraction constants exactly, and every
     engine module that re-exports a dial must agree with NORMAL (no silent drift).
  2. Cover the profile machinery: registry contents, get_profile resolution, easy/hard overrides.
"""
from __future__ import annotations

import engine.balance as balance
from engine.balance import NORMAL, EASY, HARD, PROFILES, get_profile, is_valid_difficulty


# ── 1. NORMAL reproduces the historical constants exactly ────────────────────────

def test_normal_values_match_historical_constants():
    assert NORMAL.base_income == 20
    assert NORMAL.tax_office_income == 20
    assert NORMAL.cap_headroom_mult == 1.20
    assert NORMAL.drift_step == 10
    assert NORMAL.pop_growth == 0.02
    assert NORMAL.pop_min == 1000
    assert NORMAL.health_deltas == {"Starving": -4, "Hungry": -2, "Well fed": 2}
    assert NORMAL.support_deltas == {
        "Starving": -5, "Hungry": -2, "Well fed": 2, "Miserable": -2, "Festive": 2,
    }
    assert NORMAL.piety_per_level == 4
    assert NORMAL.piety_parity == 1.0
    assert NORMAL.piety_blame == {
        "Godless": 1.5, "Lax": 1.25, "Observant": 1.0, "Devout": 0.75, "Zealous": 0.75,
    }
    assert NORMAL.zealot_support_tax == -1
    assert NORMAL.unrest_hunger == 30
    assert NORMAL.unrest_impiety == 20
    assert NORMAL.unrest_confidence == 20
    assert NORMAL.unrest_drunk == 10
    assert NORMAL.unrest_ease == 4
    assert NORMAL.guard_suppress == 3
    assert NORMAL.guard_heavy_threshold == 15
    assert NORMAL.guard_heavy_support == -2
    assert NORMAL.consumption_parity == 0.27
    assert NORMAL.consumption_dry_health == -2
    assert NORMAL.health_output == 0.05
    assert NORMAL.consumption_output == 0.10
    assert (NORMAL.eff_min, NORMAL.eff_max) == (0.5, 1.25)
    assert NORMAL.meet_cooldown == 10
    assert NORMAL.sabotage_gold == 50
    assert NORMAL.leverage_threshold == 500
    assert NORMAL.removal_threshold == 800
    assert NORMAL.removal_grace_cycles == 5
    assert NORMAL.removal_rep_threshold == -30
    assert NORMAL.pop_collapse == 1000
    assert NORMAL.pop_floor_is_death is True
    assert (NORMAL.pop_warn_on, NORMAL.pop_warn_off) == (1500, 1750)
    assert NORMAL.pop_warn_support_drain == -1


# ── The engine modules re-export NORMAL — they must not drift from it ─────────────

def test_modules_reexport_normal():
    from engine import formulas
    from engine.needs import drift, scales
    from engine.mayor import actions
    from engine.special import moneylender

    assert formulas.BASE_INCOME == NORMAL.base_income
    assert formulas.TAX_OFFICE_INCOME == NORMAL.tax_office_income
    assert formulas.CAP_HEADROOM_MULT == NORMAL.cap_headroom_mult

    assert drift.DRIFT_STEP == NORMAL.drift_step
    assert drift.POP_GROWTH == NORMAL.pop_growth
    assert drift.POP_MIN == NORMAL.pop_min
    assert drift.HEALTH_DELTAS == NORMAL.health_deltas
    assert drift.SUPPORT_DELTAS == NORMAL.support_deltas

    assert scales.UNREST_EASE == NORMAL.unrest_ease
    assert scales.GUARD_SUPPRESS == NORMAL.guard_suppress
    assert scales.ZEALOT_SUPPORT_TAX == NORMAL.zealot_support_tax
    assert scales.CONSUMPTION_PARITY == NORMAL.consumption_parity
    assert (scales.EFF_MIN, scales.EFF_MAX) == (NORMAL.eff_min, NORMAL.eff_max)

    assert actions.MEET_COOLDOWN == NORMAL.meet_cooldown
    assert actions.SABOTAGE_GOLD == NORMAL.sabotage_gold

    assert moneylender.LEVERAGE_THRESHOLD == NORMAL.leverage_threshold
    assert moneylender.REMOVAL_THRESHOLD == NORMAL.removal_threshold
    assert moneylender.REMOVAL_GRACE_CYCLES == NORMAL.removal_grace_cycles


# ── 2. Profile machinery ─────────────────────────────────────────────────────────

def test_registry_contents():
    assert set(PROFILES) == {"easy", "normal", "hard"}
    assert PROFILES["normal"] is NORMAL
    assert PROFILES["easy"] is EASY
    assert PROFILES["hard"] is HARD
    assert balance.DEFAULT_DIFFICULTY == "normal"


def test_get_profile_resolution():
    assert get_profile("normal") is NORMAL
    assert get_profile("EASY") is EASY          # case-insensitive
    assert get_profile("hard") is HARD
    assert get_profile(None) is NORMAL          # None → normal
    assert get_profile("nonsense") is NORMAL    # unknown → normal


def test_is_valid_difficulty():
    assert is_valid_difficulty("easy")
    assert is_valid_difficulty("Normal")
    assert not is_valid_difficulty("brutal")
    assert not is_valid_difficulty(None)
    assert not is_valid_difficulty("")


def test_easy_and_hard_override_normal():
    # Each carries its own name and differs from NORMAL on the dials we chose to vary.
    assert EASY.name == "easy" and HARD.name == "hard"
    assert EASY.base_income > NORMAL.base_income > HARD.base_income
    assert EASY.unrest_ease > NORMAL.unrest_ease > HARD.unrest_ease
    assert EASY.removal_threshold > NORMAL.removal_threshold > HARD.removal_threshold
    # Unvaried dials are inherited unchanged.
    assert EASY.drift_step == NORMAL.drift_step == HARD.drift_step
