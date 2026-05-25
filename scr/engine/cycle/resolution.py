"""
cycle/resolution.py — Sequential initiative action loop (v4).

Replaces the old batch declaration + block-first-then-all model.
Each faction acts one at a time in initiative order. Block fires as a
standing trap at the start of the target's turn.
"""
from __future__ import annotations
import random
from typing import Dict, List, Optional

from ..models import Faction, Domain, WorldState, Project, ActionResult, FactionPlan
from ..actions import (
    resolve_grow,
    resolve_harm,
    set_block,
    fire_block,
    resolve_protect,
    resolve_steal,
    resolve_build_project,
    resolve_sabotage_project,
)
from ..npc import select_faction_action


def run_sequential_actions(
    world: WorldState,
    factions: Dict[str, Faction],
    domains: Dict[str, Domain],
    projects: Dict[str, Project],
    cycle_num: int,
    logger=None,
) -> List[ActionResult]:
    """
    Step 1+2: Roll initiative, then iterate factions in order.
    Each turn: fire pending block → select action → resolve.
    Returns all ActionResults for the cycle.
    """
    results: List[ActionResult] = []

    # Reset cycle-only state on all factions
    for faction in factions.values():
        faction.reset_cycle_state()

    # Step 1 — Initiative roll
    order = list(factions.keys())
    random.shuffle(order)
    world.initiative_order = order

    # Step 2 — Sequential action loop
    for fid in order:
        faction = factions.get(fid)
        if faction is None:
            continue

        # 2a — Block check: scan for any armed block targeting this faction
        block_result = _check_and_fire_block(faction, factions, cycle_num, logger)
        if block_result:
            results.append(block_result)
            if faction.action_cancelled:
                continue  # decisive block: skip this faction's turn entirely

        # 2b — Behavior engine (live state)
        plan = select_faction_action(faction, factions, domains, world, projects)

        # Apply downgrade from partial block
        if faction.action_downgraded:
            if plan.action in ("Harm", "Steal"):
                plan.action = "Grow"
                plan.target_id = None
            faction.action_downgraded = False

        # 2c — Resolve action
        result = _execute(plan, faction, factions, domains, projects)
        if result:
            results.append(result)
            if logger and result.dramatic and result.narrative:
                logger.log_dramatic(cycle_num, result.narrative)

    return results


def _check_and_fire_block(
    faction: Faction,
    factions: Dict[str, Faction],
    cycle_num: int,
    logger=None,
) -> Optional[ActionResult]:
    """Find the first armed blocker targeting this faction and fire it."""
    for blocker in factions.values():
        if blocker.active_block_target == faction.id:
            result = fire_block(blocker, faction)
            if logger and result.narrative:
                logger.log_dramatic(cycle_num, result.narrative)
            return result
    return None


def _execute(
    plan: FactionPlan,
    faction: Faction,
    factions: Dict[str, Faction],
    domains: Dict[str, Domain],
    projects: Dict[str, Project],
) -> Optional[ActionResult]:
    action = plan.action

    if action == "Skip":
        return None

    if action == "Grow":
        return resolve_grow(faction, domains)

    if action == "Protect":
        return resolve_protect(faction)

    if action == "Harm" and plan.target_id:
        target = factions.get(plan.target_id)
        if target:
            return resolve_harm(faction, target, factions)

    if action == "Steal" and plan.target_id:
        target = factions.get(plan.target_id)
        if target:
            return resolve_steal(faction, target)

    if action == "Block" and plan.target_id:
        return set_block(faction, plan.target_id)

    if action == "BuildProject" and plan.target_id:
        project = projects.get(plan.target_id)
        if project:
            return resolve_build_project(faction, project)

    if action == "SabotageProject" and plan.target_id:
        project = projects.get(plan.target_id)
        if project:
            return resolve_sabotage_project(faction, project)

    # Fallback
    return resolve_grow(faction, domains)
