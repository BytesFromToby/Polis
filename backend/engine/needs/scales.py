"""
engine/needs/scales.py — the non-food Public scales: piety and unrest (public-needs_spec).

Piety is a need with a temple-produced supply (mirrors the food chain shape but lives here, since
it feeds a Public scale, not food). Unrest is the pressure aggregate (added in the unrest slice).
All constants provisional — tune by feel; tests import them, never copy.
"""
from __future__ import annotations
from typing import Dict, TYPE_CHECKING

from .chain import TOIL_MULT
from .bands import piety_band

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
