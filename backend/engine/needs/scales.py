"""
engine/needs/scales.py — the non-food Public scales: piety and unrest (public-needs_spec).

Piety is a need with a temple-produced supply (mirrors the food chain shape but lives here, since
it feeds a Public scale, not food). Unrest is the pressure aggregate (added in the unrest slice).
All constants provisional — tune by feel; tests import them, never copy.
"""
from __future__ import annotations
from typing import Dict, TYPE_CHECKING

from .chain import TOIL_MULT
from .bands import piety_band, fed_band

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
