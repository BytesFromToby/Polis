"""
engine/needs/scales.py — the non-food Public scales: piety and unrest (public-needs_spec).

Piety is a need with a temple-produced supply (mirrors the food chain shape but lives here, since
it feeds a Public scale, not food). Unrest is the pressure aggregate (added in the unrest slice).
All constants provisional — tune by feel; tests import them, never copy.
"""
from __future__ import annotations
from typing import Dict, TYPE_CHECKING

from .chain import TOIL_MULT
from .bands import piety_band, fed_band, consumption_band, health_band
from engine.balance import NORMAL as _BAL

if TYPE_CHECKING:
    from engine.models import Faction, ThePublic

# Tunables live in engine/balance.py; names preserved here for the modules/tests that import them.
# ── Piety ──────────────────────────────────────────────────────────────────────
PIETY_PER_LEVEL = _BAL.piety_per_level   # piety supply per temple-faction level
PIETY_PARITY = _BAL.piety_parity         # supply meeting parity-demand sits at the top of Observant
# Crisis-blame: piety scales the needs step's NEGATIVE support penalties.
PIETY_BLAME = _BAL.piety_blame
ZEALOT_SUPPORT_TAX = _BAL.zealot_support_tax   # support/cycle while piety is Zealous


def piety_supply(factions: Dict[str, "Faction"]) -> float:
    """Σ PIETY_PER_LEVEL × level over temple-domain factions, honoring Withhold (×0) then
    Toil (×TOIL_MULT) exactly as the food chain treats its producers."""
    total = 0.0
    for f in factions.values():
        if f.domain_primary != "temples":
            continue
        contribution = PIETY_PER_LEVEL * f.level
        if f.withholding:
            contribution = 0.0
        elif f.toiling:
            contribution *= TOIL_MULT
        total += contribution
    return total


def piety_target(factions: Dict[str, "Faction"], population: int) -> float:
    demand = population / 1000.0
    if demand <= 0:
        return 0.0
    return max(0.0, min(100.0, 100.0 * piety_supply(factions) / (demand * PIETY_PARITY)))


def blame_factor(piety: int) -> float:
    return PIETY_BLAME[piety_band(piety)]


# ── Unrest ─────────────────────────────────────────────────────────────────────
UNREST_HUNGER = _BAL.unrest_hunger       # pressure when Starving (half when Hungry)
UNREST_IMPIETY = _BAL.unrest_impiety     # pressure when Godless (half when Lax)
UNREST_CONFIDENCE = _BAL.unrest_confidence   # max pressure from negative support, scaled by -support/50
UNREST_DRUNK = _BAL.unrest_drunk         # pressure when the city is drunk
UNREST_EASE = _BAL.unrest_ease           # unrest eases toward a lower target this slowly; rises at DRIFT_STEP
GUARD_SUPPRESS = _BAL.guard_suppress     # unrest removed per City Guard level (paid), after drift — symptom only
GUARD_HEAVY_THRESHOLD = _BAL.guard_heavy_threshold   # suppression removing ≥ this is "heavy-handed"
GUARD_HEAVY_SUPPORT = _BAL.guard_heavy_support     # support cost of heavy-handed guarding


def unrest_target(public: "ThePublic") -> float:
    """Aggregate civic pressure (0–100) — hunger + impiety + low confidence + drunkenness."""
    pressure = 0.0

    fed_word = fed_band(public.fed)
    if fed_word == "Starving":
        pressure += UNREST_HUNGER
    elif fed_word == "Hungry":
        pressure += UNREST_HUNGER / 2

    piety_word = piety_band(public.piety)
    if piety_word == "Godless":
        pressure += UNREST_IMPIETY
    elif piety_word == "Lax":
        pressure += UNREST_IMPIETY / 2

    if public.support < 0:
        pressure += min(UNREST_CONFIDENCE, UNREST_CONFIDENCE * (-public.support) / 50)

    if public.drunk:
        pressure += UNREST_DRUNK

    return max(0.0, min(100.0, pressure))


# ── Consumption ────────────────────────────────────────────────────────────────
# wine_happy/demand at CONSUMPTION_PARITY maps to the Tempered midpoint (50). Tuned so the
# FRESH standard city sits Tempered: its wine_happy/demand == 0.27 (Winepressers level 2), so
# PARITY == 0.27 → target 50. (An earlier 0.097 was mis-measured from an evolved roster.)
CONSUMPTION_PARITY = _BAL.consumption_parity
CONSUMPTION_DRY_HEALTH = _BAL.consumption_dry_health   # health/cycle while Dry (raw water → illness)


def consumption_target(wine_happy: float, population: int) -> float:
    """Driven by wine supply only (no misery→drink feedback — the doom-loop governor).
    wine/demand at CONSUMPTION_PARITY → 50 (Tempered); twice that → 100 (Sodden)."""
    demand = population / 1000.0
    if demand <= 0:
        return 0.0
    return max(0.0, min(100.0, 50.0 * (wine_happy / demand) / CONSUMPTION_PARITY))


def is_drunk(consumption: int) -> bool:
    return consumption_band(consumption) in ("Tipsy", "Sodden")


# ── The Public→production wire ───────────────────────────────────────────────────
# One global efficiency multiplier on food output, read from the Public's current bands.
# Deliberately small: a nudge, not a regime change (the shipped redundancy/dynamics still hold).
HEALTH_OUTPUT = _BAL.health_output       # Robust +1×, Thriving +2× — a hale workforce produces more
CONSUMPTION_OUTPUT = _BAL.consumption_output  # Tipsy −1×, Sodden −2× — a drunk city does less work
EFF_MIN, EFF_MAX = _BAL.eff_min, _BAL.eff_max

_HEALTH_BONUS = {"Robust": 1, "Thriving": 2}
_CONSUMPTION_PENALTY = {"Tipsy": 1, "Sodden": 2}


def production_efficiency(public: "ThePublic") -> float:
    """1.0 at Healthy+Tempered; health Robust/Thriving lift it, consumption Tipsy/Sodden cut it."""
    bonus = HEALTH_OUTPUT * _HEALTH_BONUS.get(health_band(public.health), 0)
    penalty = CONSUMPTION_OUTPUT * _CONSUMPTION_PENALTY.get(consumption_band(public.consumption), 0)
    return max(EFF_MIN, min(EFF_MAX, 1.0 + bonus - penalty))
