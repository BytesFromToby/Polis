"""
events/world.py — World-level event functions (v2, unit-free).

SM attention removed. Unit functions removed.
"""
from __future__ import annotations
import random
from typing import Dict, List

from ..models import Faction, Domain, WorldState, ActionResult
from ..formulas import faction_weight


def process_world_chaos(
    world: WorldState,
    factions: Dict[str, Faction],
    domains: Dict[str, Domain],
) -> List[ActionResult]:
    """
    For each domain with chaos > 0: probability check, fire extraordinary action.
    1–3: low — random faction gets +5 bonus to next action (not yet implemented)
    4–6: moderate — random event fires
    7–9: high — major event likely
    10:  guaranteed; chaos −2 next cycle
    """
    results: List[ActionResult] = []

    for domain_id, chaos_level in list(world.chaos.items()):
        if chaos_level <= 0:
            continue

        fire_chance = {
            1: 0.20, 2: 0.30, 3: 0.40,
            4: 0.55, 5: 0.65, 6: 0.70,
            7: 0.80, 8: 0.88, 9: 0.92,
        }.get(int(chaos_level), 1.0)

        if random.random() > fire_chance:
            world.chaos[domain_id] = max(0, chaos_level - 2)
            continue

        # Pick a faction in this domain to be affected
        domain_factions = [f for f in factions.values() if f.domain_primary == domain_id]
        if not domain_factions:
            world.chaos[domain_id] = max(0, chaos_level - 2)
            continue

        target = random.choice(domain_factions)
        intensity = "minor" if chaos_level <= 3 else ("moderate" if chaos_level <= 6 else "major")
        narrative = (
            f"Chaos grips {domain_id.replace('_', ' ').title()}. "
            f"A {intensity} upheaval rattles {target.name}."
        )
        results.append(ActionResult(
            "ChaosEvent", target.id, None, "success",
            dramatic=(chaos_level >= 7),
            narrative=narrative,
            domain=domain_id,
        ))

        if chaos_level >= 10:
            world.chaos[domain_id] = max(0, chaos_level - 2)

    return results
