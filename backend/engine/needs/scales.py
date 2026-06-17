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

if TYPE_CHECKING:
    from engine.models import Faction, ThePublic

# ── Piety ──────────────────────────────────────────────────────────────────────
PIETY_PER_LEVEL = 4          # piety supply per temple-faction level
PIETY_PARITY = 1.0           # supply meeting parity-demand sits at the top of Observant
# Crisis-blame: piety scales the needs step's NEGATIVE support penalties.
PIETY_BLAME = {
    "Godless": 1.5, "Lax": 1.25, "Observant": 1.0, "Devout": 0.75, "Zealous": 0.75,
}
ZEALOT_SUPPORT_TAX = -1      # support/cycle while piety is Zealous (temples defy the Mayor)


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
UNREST_HUNGER = 30       # pressure when Starving (half when Hungry)
UNREST_IMPIETY = 20      # pressure when Godless (half when Lax)
UNREST_CONFIDENCE = 20   # max pressure from negative support, scaled by -support/50
UNREST_DRUNK = 10        # pressure when the city is drunk
UNREST_EASE = 4          # unrest eases toward a lower target this slowly (memory); rises at DRIFT_STEP
GUARD_SUPPRESS = 3       # unrest removed per City Guard level (paid), after drift — symptom only
GUARD_HEAVY_THRESHOLD = 15   # suppression removing ≥ this is "heavy-handed"
GUARD_HEAVY_SUPPORT = -2     # support cost of heavy-handed guarding


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
CONSUMPTION_PARITY = 0.27
CONSUMPTION_DRY_HEALTH = -2   # health/cycle while Dry (too little wine → raw water → illness)


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
HEALTH_OUTPUT = 0.05       # Robust +1×, Thriving +2× — a hale workforce produces more
CONSUMPTION_OUTPUT = 0.10  # Tipsy −1×, Sodden −2× — a drunk city does less work
EFF_MIN, EFF_MAX = 0.5, 1.25

_HEALTH_BONUS = {"Robust": 1, "Thriving": 2}
_CONSUMPTION_PENALTY = {"Tipsy": 1, "Sodden": 2}


def production_efficiency(public: "ThePublic") -> float:
    """1.0 at Healthy+Tempered; health Robust/Thriving lift it, consumption Tipsy/Sodden cut it."""
    bonus = HEALTH_OUTPUT * _HEALTH_BONUS.get(health_band(public.health), 0)
    penalty = CONSUMPTION_OUTPUT * _CONSUMPTION_PENALTY.get(consumption_band(public.consumption), 0)
    return max(EFF_MIN, min(EFF_MAX, 1.0 + bonus - penalty))
