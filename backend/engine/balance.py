"""
engine/balance.py — the single source of truth for tunable game dials (balance_spec).

Every "would I ever change this to retune difficulty or feel?" constant lives here, once,
as a field on `BalanceProfile`. Engine modules re-export their historical constant names
from the `NORMAL` profile (e.g. `DRIFT_STEP = NORMAL.drift_step`), so existing imports and
tests keep working unchanged while the *values* live in one place.

Difficulty is named profiles over a base set: `NORMAL` is the base (today's exact numbers);
`EASY` and `HARD` are `NORMAL` plus overrides. `SimRun.difficulty` records the chosen profile.

SCOPE (slice 1 — behavior-preserving):
  - `NORMAL` reproduces the pre-extraction constants exactly; the engine consumes NORMAL only.
  - `EASY` / `HARD` are DEFINED but NOT YET CONSUMED by the engine — wiring the active profile
    through the cycle is the next slice (see balance_spec.md "Slice 2"). Their override values
    are provisional and untuned.

DISCRIMINATOR for what belongs here: a difficulty/feel/stakes dial → yes. A structural
invariant (`RATING_MAX`, the d20, term-type maps, action-point costs) → no, leave it in place.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace


def _health_deltas() -> dict:
    return {"Starving": -4, "Hungry": -2, "Well fed": 2}


def _support_deltas() -> dict:
    return {"Starving": -5, "Hungry": -2, "Well fed": 2, "Miserable": -2, "Festive": 2}


def _piety_blame() -> dict:
    return {"Godless": 1.5, "Lax": 1.25, "Observant": 1.0, "Devout": 0.75, "Zealous": 0.75}


@dataclass(frozen=True)
class BalanceProfile:
    """One complete set of tunable dials. `NORMAL` is the base; difficulties override it."""

    name: str = "normal"

    # ── Treasury income (formulas.py) ──────────────────────────────────────────
    base_income: int = 20          # flat gold/cycle before any Tax Offices
    tax_office_income: int = 20    # gold/cycle per completed civic Tax Office

    # ── Domain cap (formulas.py) ───────────────────────────────────────────────
    cap_headroom_mult: float = 1.20

    # ── Public-needs drift (needs/drift.py) ────────────────────────────────────
    drift_step: int = 10           # max trait movement toward target per cycle
    pop_growth: float = 0.02       # ±fraction/cycle
    pop_min: int = 1000            # population floor (endgame slice decides floor-vs-death)
    health_deltas: dict = field(default_factory=_health_deltas)
    support_deltas: dict = field(default_factory=_support_deltas)

    # ── Piety (needs/scales.py) ────────────────────────────────────────────────
    piety_per_level: int = 4
    piety_parity: float = 1.0
    piety_blame: dict = field(default_factory=_piety_blame)
    zealot_support_tax: int = -1

    # ── Unrest (needs/scales.py) ───────────────────────────────────────────────
    unrest_hunger: int = 30
    unrest_impiety: int = 20
    unrest_confidence: int = 20
    unrest_drunk: int = 10
    unrest_ease: int = 4           # eases toward a lower target this slowly; rises at drift_step

    # ── City Guard (needs/scales.py) ───────────────────────────────────────────
    guard_suppress: int = 3
    guard_heavy_threshold: int = 15
    guard_heavy_support: int = -2

    # ── Consumption (needs/scales.py) ──────────────────────────────────────────
    consumption_parity: float = 0.27
    consumption_dry_health: int = -2

    # ── Public→production efficiency (needs/scales.py) ─────────────────────────
    health_output: float = 0.05
    consumption_output: float = 0.10
    eff_min: float = 0.5
    eff_max: float = 1.25

    # ── Mayor actions (mayor/actions.py) — DEFINED but NOT yet consumed ─────────
    # These are read on the player-action / audience path (a fixed-signature dispatch map
    # plus the separate audience route), not the per-cycle path. Threading them is a noted
    # follow-up; for now they resolve from NORMAL regardless of difficulty.
    meet_cooldown: int = 10        # cycles between audiences with the same faction
    sabotage_gold: int = 50        # gold cost of a Sabotage

    # ── Moneylender / removal coalition (special/moneylender.py) ───────────────
    leverage_threshold: int = 500
    removal_threshold: int = 800
    removal_grace_cycles: int = 5

    # ── Mayor removal spiral / terminal fail state (special/removal.py) ─────────
    removal_rep_threshold: int = -30   # Public reputation at/below this starts the countdown

    # ── Population collapse + latched warning (special/removal.py) ──────────────
    pop_collapse: int = 1000           # population at/below this ends the run (if death enabled)
    pop_floor_is_death: bool = True    # True: hitting the floor is terminal; False (easy): just a floor
    pop_warn_on: int = 1500            # warning latches ON at/below this population
    pop_warn_off: int = 1750           # warning clears once population recovers above this (hysteresis)
    pop_warn_support_drain: int = -1   # support lost per cycle while the warning is active

    # ── Elections (special/election.py) ────────────────────────────────────────
    election_interval: int = 12        # an election is held every N cycles
    election_warn_window: int = 4      # campaign warning starts this many cycles before the vote
    election_pass_score: float = 0.0   # approval (−50..+50) must reach this to be re-elected
    election_public_weight: float = 0.5  # popular vote share; faction vote share = 1 − this


# ── Profiles ────────────────────────────────────────────────────────────────────

#: Base profile — reproduces the pre-extraction constants exactly. The engine consumes this.
NORMAL = BalanceProfile(name="normal")

#: Forgiving "self-balancing" mode. Overrides bite on the per-cycle path (income, drift,
#: unrest, population, removal). Provisional, untuned values.
EASY = replace(
    NORMAL,
    name="easy",
    base_income=30,
    pop_growth=0.03,
    unrest_ease=6,            # calms faster
    removal_threshold=1200,   # more debt tolerance
    removal_grace_cycles=8,
    pop_floor_is_death=False,  # the city bottoms out at the floor but never dies
)

#: Harsher mode with real stakes. Provisional, untuned values.
HARD = replace(
    NORMAL,
    name="hard",
    base_income=12,
    pop_growth=0.015,
    unrest_ease=2,          # grudges linger
    removal_threshold=500,
    removal_grace_cycles=3,
)

#: Registry, keyed by the value stored on `SimRun.difficulty`.
PROFILES: dict[str, BalanceProfile] = {
    "easy": EASY,
    "normal": NORMAL,
    "hard": HARD,
}

DEFAULT_DIFFICULTY = "normal"


def get_profile(name: str | None) -> BalanceProfile:
    """Resolve a difficulty name to its profile. Unknown/None → NORMAL."""
    if not name:
        return NORMAL
    return PROFILES.get(name.lower(), NORMAL)


def is_valid_difficulty(name: str | None) -> bool:
    """True if `name` names a known profile (case-insensitive)."""
    return bool(name) and name.lower() in PROFILES
