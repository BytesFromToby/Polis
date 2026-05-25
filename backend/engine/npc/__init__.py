"""
engine/npc/__init__.py — Faction behavior engine (v2).
"""
from .behavior import (
    select_faction_action,
    evolve_traits,
    weighted_choice,
    BASE_WEIGHTS,
    TRAIT_MODIFIERS,
    INTENSITY_MULTIPLIERS,
    SKIP_CHANCE,
)

__all__ = [
    "select_faction_action",
    "evolve_traits",
    "weighted_choice",
    "BASE_WEIGHTS",
    "TRAIT_MODIFIERS",
    "INTENSITY_MULTIPLIERS",
    "SKIP_CHANCE",
]
