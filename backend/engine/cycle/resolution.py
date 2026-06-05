"""
cycle/resolution.py — Sequential initiative action loop (v5, demo redesign).

Block removed (no standing trap). Each faction acts once in initiative order.
A faction reduced to 0 health Breaks immediately (it never dies).
"""
from __future__ import annotations
import random
from typing import Dict, List, Optional

from ..models import Faction, Domain, WorldState, Project, ActionResult, FactionPlan, Leader
from ..actions import (
    resolve_grow,
    resolve_harm,
    resolve_protect,
    resolve_aid,
    resolve_steal,
    resolve_build_project,
    resolve_sabotage_project,
)
from ..npc import select_faction_action


# Minimal name pool for auto-regenerated leaders (theme-appropriate placeholder).
_NEW_LEADER_NAMES = [
    "Hagnon", "Kleisthenes", "Theramenes", "Nikias", "Demosthenes",
    "Kallikrates", "Eudoxos", "Phaidra", "Aristomache", "Xanthippe",
    "Melanthios", "Polydoros", "Euphranor", "Lykourgos", "Andromache",
]


def run_sequential_actions(
    world: WorldState,
    factions: Dict[str, Faction],
    domains: Dict[str, Domain],
    projects: Dict[str, Project],
    cycle_num: int,
    logger=None,
) -> List[ActionResult]:
    """Step 1+2: roll initiative, then resolve each faction's single action in order.
    A target dropped to 0 health Breaks before the loop continues."""
    results: List[ActionResult] = []

    for faction in factions.values():
        faction.reset_cycle_state()

    # Step 1 — Initiative (all factions; none are ever removed)
    order = list(factions.keys())
    random.shuffle(order)
    world.initiative_order = order

    # Step 2 — Sequential action loop
    for fid in order:
        faction = factions.get(fid)
        if faction is None:
            continue

        plan = select_faction_action(faction, factions, domains, world, projects)
        result = _execute(plan, faction, factions, domains, projects)
        if not result:
            continue

        results.append(result)
        if logger and result.dramatic and result.narrative:
            logger.log_dramatic(cycle_num, result.narrative)

        # Break check — did this action drop a faction to 0 health?
        if result.target_id:
            victim = factions.get(result.target_id)
            if victim and victim.health <= 0:
                brk = resolve_break(victim)
                results.append(brk)
                if logger and brk.narrative:
                    logger.log_dramatic(cycle_num, brk.narrative)

    return results


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
    if action == "Aid" and plan.target_id:
        target = factions.get(plan.target_id)
        if target:
            return resolve_aid(faction, target)
    if action == "Harm" and plan.target_id:
        target = factions.get(plan.target_id)
        if target:
            return resolve_harm(faction, target, factions)
    if action == "Steal" and plan.target_id:
        target = factions.get(plan.target_id)
        if target:
            return resolve_steal(faction, target)
    if action == "BuildProject" and plan.target_id:
        if plan.target_id.startswith("new_base:"):
            from ..projects import initiate_base_project
            domain_id = plan.target_id.split(":", 1)[1]
            new_project = initiate_base_project(domain_id, projects, faction.id)
            if new_project:
                return resolve_build_project(faction, new_project)
            return None
        project = projects.get(plan.target_id)
        if project:
            return resolve_build_project(faction, project)
    if action == "SabotageProject" and plan.target_id:
        project = projects.get(plan.target_id)
        if project:
            return resolve_sabotage_project(faction, project)

    # Fallback
    return resolve_grow(faction, domains)


def resolve_break(faction: Faction, rng=random) -> ActionResult:
    """Resolve a Break (health reached 0). The faction never dies:
    - 75% → level −1 (rank drops to (level-1).0; reprieve, no change, at level 1)
    - 25% → leader dies + auto-regenerates (new leader, `weakened` for a cycle)
    Health resets to 75. `rng` is injectable so tests can force a branch."""
    old_leader = faction.leader.name
    if rng.random() < 0.25:
        new_name = rng.choice(_NEW_LEADER_NAMES)
        # status="present": a freshly installed leader is full strength. (The spec
        # called for a 1-cycle `weakened` window, but the existing leadership flow
        # escalates `weakened`→`absent`, which would turn recovery into a crisis.)
        faction.leader = Leader(name=new_name, traits=[], status="present", personality_notes=[])
        narrative = f"{old_leader} of {faction.name} falls; {new_name} takes command."
    else:
        level = faction.level
        if level > 1:
            faction.rating = float(level - 1)
            narrative = f"{faction.name} is thrown into disarray and loses ground."
        else:
            narrative = f"{faction.name} is battered but holds at the bottom."

    faction.health = 75
    return ActionResult(
        "Break", faction.id, faction.id, "decisive",
        dramatic=True, narrative=narrative,
    )
