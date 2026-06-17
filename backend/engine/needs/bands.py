"""
engine/needs/bands.py — word bands for the Public's needs (public-needs_spec).

Bands are defined once here and used by the audience prompt, the UI payload,
and event gating. Tables are ordered (upper_bound, word); a value belongs to
the first band whose upper bound it does not exceed.
"""
from __future__ import annotations
from typing import List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from engine.models import ThePublic

FED_BANDS: List[Tuple[int, str]] = [
    (20, "Starving"),
    (45, "Hungry"),
    (75, "Fed"),
    (100, "Well fed"),
]

HAPPY_BANDS: List[Tuple[int, str]] = [
    (20, "Miserable"),
    (45, "Sullen"),
    (75, "Content"),
    (100, "Festive"),
]

# Piety/unrest use the 20% increments of public-model.md (five bands each).
PIETY_BANDS: List[Tuple[int, str]] = [
    (20, "Godless"),
    (40, "Lax"),
    (60, "Observant"),
    (80, "Devout"),
    (100, "Zealous"),
]

UNREST_BANDS: List[Tuple[int, str]] = [   # low is good
    (20, "Placid"),
    (40, "Quiet"),
    (60, "Restless"),
    (80, "Agitated"),
    (100, "Boiling"),
]

CONSUMPTION_BANDS: List[Tuple[int, str]] = [   # mid is good (U-shaped) — both ends bite
    (20, "Dry"),
    (40, "Sober"),
    (60, "Tempered"),
    (80, "Tipsy"),
    (100, "Sodden"),
]

# Health gains a band table for the production wire (Robust/Thriving → output↑). The sickly
# threshold (health < 40) still holds: Plague + Sickly are exactly the sub-40 bands.
HEALTH_BANDS: List[Tuple[int, str]] = [
    (20, "Plague"),
    (40, "Sickly"),
    (60, "Healthy"),
    (80, "Robust"),
    (100, "Thriving"),
]

# Confidence = the Mayor's `support` axis (−50..+50), not 0–100. High is good.
CONFIDENCE_BANDS: List[Tuple[int, str]] = [
    (-30, "Hostile"),
    (-10, "Suspicious"),
    (10, "Neutral"),
    (30, "Favorable"),
    (50, "Beloved"),
]

SICKLY_THRESHOLD = 40   # health below this → the people are sickly


def _band(value: int, table: List[Tuple[int, str]]) -> str:
    for upper, word in table:
        if value <= upper:
            return word
    return table[-1][1]


def fed_band(value: int) -> str:
    return _band(value, FED_BANDS)


def happy_band(value: int) -> str:
    return _band(value, HAPPY_BANDS)


def piety_band(value: int) -> str:
    return _band(value, PIETY_BANDS)


def unrest_band(value: int) -> str:
    return _band(value, UNREST_BANDS)


def consumption_band(value: int) -> str:
    return _band(value, CONSUMPTION_BANDS)


def health_band(value: int) -> str:
    return _band(value, HEALTH_BANDS)


def confidence_band(support: int) -> str:
    """Confidence is the −50..+50 `support` axis (special-factions_spec) viewed in 5 bands."""
    return _band(support, CONFIDENCE_BANDS)


def band_index(word: str, table: List[Tuple[int, str]]) -> int:
    """Position of a band word in its table (0 = lowest). For ≤/≥ gate comparisons."""
    for i, (_, w) in enumerate(table):
        if w == word:
            return i
    raise ValueError(f"unknown band word: {word!r}")


def is_sickly(health: int) -> bool:
    return health < SICKLY_THRESHOLD


def needs_line(public: "ThePublic", drunk: bool) -> str:
    """One prompt/UI line: 'The people are {fed}{, drunk}{, sickly}, and {happy}.'"""
    parts = [fed_band(public.fed)]
    if drunk:
        parts.append("drunk")
    if is_sickly(public.health):
        parts.append("sickly")
    return f"The people are {', '.join(parts)}, and {happy_band(public.happy)}."
