"""
events/cascades.py — Cascade events triggered by faction collapse.

Triggered when a faction with floor(rating) >= 4 collapses.
"""
from __future__ import annotations
import random
from typing import Dict, List

from ..models import Faction, Domain, WorldState, ActionResult
from ..formulas import faction_weight


def check_for_cascades(
    action_results: List[ActionResult],
    factions: Dict[str, Faction],
    domains: Dict[str, Domain],
    world: WorldState,
) -> List[ActionResult]:
    """
    Scan action_results for faction collapses that warrant cascade effects.
    Only triggers for factions at floor >= 4.
    """
    cascade_results: List[ActionResult] = []

    for result in action_results:
        if result.action not in ("FactionCollapse", "FactionDissolve"):
            continue
        if result.outcome not in ("decisive", "success"):
            continue

        collapsed_id = result.actor_id
        domain_id = result.domain

        if not domain_id:
            continue

        cascades = _fire_faction_collapse_cascade(
            collapsed_id, domain_id, factions, domains, world
        )
        cascade_results.extend(cascades)

    return cascade_results


def _fire_faction_collapse_cascade(
    collapsed_id: str,
    domain_id: str,
    factions: Dict[str, Faction],
    domains: Dict[str, Domain],
    world: WorldState,
) -> List[ActionResult]:
    """Fire cascade effects when a high-rated faction collapses."""

    # Recalculate domain utilization
    domain = domains.get(domain_id)
    if domain:
        domain.utilization = sum(
            faction_weight(f.floor)
            for f in factions.values()
            if f.domain_primary == domain_id
        )

    # Open power vacuum if not already open
    already_open = any(pv.get("domain_id") == domain_id for pv in world.power_vacuums)
    if not already_open:
        world.power_vacuums.append({
            "domain_id": domain_id,
            "cycles_remaining": 2,
            "origin_faction_id": collapsed_id,
        })

    # World chaos +2 in affected domain
    world.chaos[domain_id] = min(10, world.chaos.get(domain_id, 0) + 2)

    narrative = (
        f"The collapse of a powerful faction in {domain_id.replace('_', ' ').title()} "
        f"sends shockwaves through the domain. A power vacuum opens."
    )

    return [ActionResult(
        "Cascade", collapsed_id, None, "decisive",
        dramatic=True,
        narrative=narrative,
        domain=domain_id,
    )]
