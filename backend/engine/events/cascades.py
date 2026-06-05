"""
events/cascades.py — Retired.

Collapse cascades are gone: factions are now permanent. At health 0 a faction
Breaks (level −1 or leader death + regen) rather than collapsing, so there is no
collapse event to cascade from and no power vacuum to open. The public entry
point is kept as a no-op so existing imports/exports remain valid.
"""
from __future__ import annotations
from typing import Dict, List

from ..models import Faction, Domain, WorldState, ActionResult


def check_for_cascades(
    action_results: List[ActionResult],
    factions: Dict[str, Faction],
    domains: Dict[str, Domain],
    world: WorldState,
) -> List[ActionResult]:
    """No-op: collapse cascades are retired (factions are permanent)."""
    return []
