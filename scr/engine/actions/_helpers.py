"""
actions/_helpers.py — Internal helpers shared across action resolvers.
"""
from __future__ import annotations
from typing import Dict, Optional

from ..models import Faction


def _find_rival_faction(
    actor: Faction,
    factions: Dict[str, Faction],
    prefer_id: Optional[str] = None,
) -> Optional[Faction]:
    """Return a rival faction, preferring prefer_id if valid."""
    rivals = [f for fid, f in factions.items() if fid != actor.id]
    if not rivals:
        return None
    if prefer_id and prefer_id in factions and prefer_id != actor.id:
        return factions[prefer_id]
    return rivals[0]


def _record(stat_changes: list, entity_id: str, field: str,
            old_val, new_val) -> None:
    stat_changes.append({
        "entity_id": entity_id, "field": field,
        "old_val": old_val, "new_val": new_val,
    })
