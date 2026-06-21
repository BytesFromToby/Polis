"""
formulas.py — Pure calculation functions for Polis v3.

v3 changes (2026-05-17):
  - Removed all unit-specific formulas (inertia, edge/grit, support, weight tables)
  - Removed SM attention formulas
  - Removed focus/obscure/spy formulas
  - Simplified to faction-only contest resolution
"""
from __future__ import annotations
import random
from typing import TYPE_CHECKING

from engine.balance import NORMAL as _BAL

if TYPE_CHECKING:
    from .models import Faction, Domain


# ── Rating ceiling ────────────────────────────────────────────────────────────

RATING_MAX: float = 10.0    # faction rank ceiling (1.0–10.0); level = int(rating)


# ── Treasury income (treasury_spec v3) — tunables in engine/balance.py ──────────

BASE_INCOME: int = _BAL.base_income         # flat gold/cycle before any Tax Offices
TAX_OFFICE_INCOME: int = _BAL.tax_office_income   # gold/cycle per completed civic Tax Office


# ── Domain cap (projects rework) — tunable in engine/balance.py ────────────────

CAP_HEADROOM_MULT: float = _BAL.cap_headroom_mult   # starting cap = round(initial Σ level × this)


def base_cap_from_fill(fill: float) -> int:
    """A domain's frozen base cap: round(starting Σ level × CAP_HEADROOM_MULT).
    Set once at game start; thereafter only base projects move the live cap."""
    return round(fill * CAP_HEADROOM_MULT)


def project_cap_contribution(project) -> int:
    """How much an individual base project adds to its domain's cap, by health tier.
    Only `category == "base"` projects that are active/damaged contribute:
    intact (health 51–100) → +2, damaged (21–50) → +1, else (critical,
    under_construction, destroyed, or non-base) → 0."""
    if getattr(project, "category", "standard") != "base":
        return 0
    if project.status not in ("active", "damaged"):
        return 0
    if project.health >= 51:
        return 2
    if project.health >= 21:
        return 1
    return 0


def stack_cap_contribution(stack) -> int:
    """A domain's base-project stack contribution to its cap (projects_spec v6):
    (count − 1)×2 for the pristine pool + the top's tier when completed (a building
    top adds 0). Delegates to the stack's own derived helper so the math lives once."""
    return stack.cap_contribution() if stack is not None else 0


# ── Grow ──────────────────────────────────────────────────────────────────────

def grow_increment(level: int) -> float:
    """
    Grow increment per cycle toward the next level: 1 / (level + 1).
    Decelerating (low levels rise fast); retired 1/(2^n+1), unusable across
    10 levels. Provisional — tuned by feel.

    | Level | Grows to next | Increment |
    |-------|---------------|-----------|
    |   1   |       2       |   0.500   |
    |   2   |       3       |   0.333   |
    |   3   |       4       |   0.250   |
    |   5   |       6       |   0.167   |
    |   9   |      10       |   0.100   |
    """
    n = max(1, level)
    return round(1.0 / (n + 1), 6)


# ── Contest Resolution ────────────────────────────────────────────────────────

def faction_roll(faction: "Faction", modifier: int = 0) -> int:
    """
    d20 + floor(rating) + modifier
    Leaderless penalty (-2) applied by caller if needed.
    """
    return random.randint(1, 20) + int(faction.rating) + modifier


def resolve_contest(
    attacker: "Faction",
    defender: "Faction",
    attacker_mod: int = 0,
    defender_mod: int = 0,
) -> tuple:
    """
    Returns (outcome, margin, atk_roll, dfn_roll).
    outcome: "decisive" | "partial" | "fail"
    margin >= 5: decisive | 1-4: partial | <= 0: fail (defender wins ties)
    """
    atk_mod = attacker_mod
    dfn_mod = defender_mod

    atk = faction_roll(attacker, atk_mod)
    dfn = faction_roll(defender, dfn_mod)
    margin = atk - dfn

    if margin >= 5:
        return "decisive", margin, atk, dfn
    elif margin >= 1:
        return "partial", margin, atk, dfn
    else:
        return "fail", margin, atk, dfn


# ── Domain ────────────────────────────────────────────────────────────────────

def faction_weight(level: int) -> int:
    """A faction contributes its level to its domain's utilization (Σ level).
    Replaces the retired exponential weight table."""
    return max(0, level)


def domain_cap_resistance(utilization: float, cap: int) -> str:
    """
    Returns: 'open' | 'passive' | 'contested' | 'blocked'
    < 60%: open  |  60-85%: passive  |  85-95%: contested  |  >= 95%: blocked
    """
    if cap == 0:
        return "blocked"
    pct = utilization / cap
    if pct >= 0.95:  return "blocked"
    if pct >= 0.85:  return "contested"
    if pct >= 0.60:  return "passive"
    return "open"
