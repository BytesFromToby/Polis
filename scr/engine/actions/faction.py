"""
actions/faction.py — Faction action resolvers (v4).

Actions: Grow, Harm, Block (set_block/fire_block), Protect, Steal,
         BuildProject, SabotageProject.
Recruit removed. Block is now a persistent trap resolved when target acts.
"""
from __future__ import annotations
import random
from typing import Dict, Optional

from ..models import Faction, Domain, Project, ActionResult
from ..formulas import grow_increment, resolve_contest, RATING_MAX
from ._helpers import _find_rival_faction


# ── GROW ──────────────────────────────────────────────────────────────────────

def resolve_grow(
    faction: Faction,
    domains: Dict[str, Domain],
) -> ActionResult:
    domain = domains.get(faction.domain_primary)
    if domain and domain.cap > 0 and domain.utilization >= domain.cap:
        return ActionResult(
            "Grow", faction.id, None, "blocked",
            narrative=f"{faction.name} cannot grow — domain at capacity.",
        )
    if faction.rating >= RATING_MAX:
        return ActionResult(
            "Grow", faction.id, None, "blocked",
            narrative=f"{faction.name} is already at maximum influence.",
        )

    floor_before = faction.floor
    increment = grow_increment(floor_before)
    faction.rating = round(min(RATING_MAX, faction.rating + increment), 4)
    faction.health = min(100, faction.health + 3)

    floor_advance = int(faction.rating) > floor_before and faction.entrench >= 50
    if floor_advance:
        faction.floor = int(faction.rating)
        faction.entrench = max(25, int(faction.entrench * 0.25))

    return ActionResult(
        "Grow", faction.id, None, "success",
        delta=increment,
        dramatic=floor_advance,
        narrative=(
            f"{faction.name} expands its influence."
            + (" They reach a new level of power." if floor_advance else "")
        ),
    )


# ── HARM ──────────────────────────────────────────────────────────────────────

def resolve_harm(
    faction: Faction,
    target: Faction,
    factions: Dict[str, Faction],
) -> ActionResult:
    if target.domain_primary != faction.domain_primary:
        return ActionResult(
            "Harm", faction.id, target.id, "blocked",
            narrative=f"{faction.name} cannot reach {target.name} — different domain.",
        )

    outcome, margin, atk, dfn = resolve_contest(faction, target)

    if outcome == "decisive":
        target.rating = round(max(1.0, target.rating - 0.25), 4)
        target.entrench = max(0, target.entrench - 10)
        return ActionResult(
            "Harm", faction.id, target.id, "decisive",
            margin=margin, delta=0.25,
            roll_attacker=atk, roll_defender=dfn,
            dramatic=True,
            narrative=f"{faction.name} strikes hard against {target.name}, weakening their influence and shaking their organization.",
        )
    elif outcome == "partial":
        target.entrench = max(0, target.entrench - 10)
        return ActionResult(
            "Harm", faction.id, target.id, "partial",
            margin=margin, delta=0.0,
            roll_attacker=atk, roll_defender=dfn,
            narrative=f"{faction.name} pressures {target.name}, wearing down their defenses.",
        )
    else:
        return ActionResult(
            "Harm", faction.id, target.id, "fail",
            margin=margin, delta=0.0,
            roll_attacker=atk, roll_defender=dfn,
            narrative=f"{faction.name} moves against {target.name} but fails to land a blow.",
        )


# ── BLOCK ─────────────────────────────────────────────────────────────────────

def set_block(faction: Faction, target_id: str) -> ActionResult:
    """Place a standing block trap. Target is hidden from public log."""
    faction.active_block_target = target_id
    return ActionResult(
        "Block", faction.id, None, "no_op",
        narrative=f"{faction.name} takes a guarded stance.",
    )


def fire_block(blocker: Faction, target: Faction) -> ActionResult:
    """Contest fires when target acts. Consumes the block regardless of outcome."""
    blocker.active_block_target = ""
    outcome, margin, atk, dfn = resolve_contest(blocker, target)

    if outcome == "decisive":
        target.action_cancelled = True
        return ActionResult(
            "Block", blocker.id, target.id, "decisive",
            margin=margin, roll_attacker=atk, roll_defender=dfn,
            dramatic=True,
            narrative=f"{blocker.name} intercepts {target.name} — their action is neutralized.",
        )
    elif outcome == "partial":
        target.action_downgraded = True
        return ActionResult(
            "Block", blocker.id, target.id, "partial",
            margin=margin, roll_attacker=atk, roll_defender=dfn,
            narrative=f"{blocker.name} disrupts {target.name} — they are forced to fall back.",
        )
    else:
        return ActionResult(
            "Block", blocker.id, target.id, "fail",
            margin=margin, roll_attacker=atk, roll_defender=dfn,
            narrative=f"{blocker.name}'s attempt to intercept {target.name} fails.",
        )


# ── PROTECT ───────────────────────────────────────────────────────────────────

def resolve_protect(faction: Faction) -> ActionResult:
    old_entrench = faction.entrench
    faction.entrench = min(100, faction.entrench + 10)
    faction.health = min(100, faction.health + 5)
    delta = faction.entrench - old_entrench
    return ActionResult(
        "Protect", faction.id, None, "success",
        delta=float(delta),
        narrative=f"{faction.name} consolidates its position, strengthening internal cohesion.",
    )


# ── STEAL ─────────────────────────────────────────────────────────────────────

def resolve_steal(
    faction: Faction,
    target: Faction,
) -> ActionResult:
    if target.domain_primary != faction.domain_primary:
        return ActionResult(
            "Steal", faction.id, target.id, "blocked",
            narrative=f"{faction.name} cannot steal from {target.name} — different domain.",
        )

    outcome, margin, atk, dfn = resolve_contest(faction, target)

    if outcome == "decisive":
        transfer = 0.20
        faction.rating = round(min(RATING_MAX, faction.rating + transfer), 4)
        target.rating = round(max(1.0, target.rating - transfer), 4)
        return ActionResult(
            "Steal", faction.id, target.id, "decisive",
            margin=margin, delta=transfer,
            roll_attacker=atk, roll_defender=dfn,
            dramatic=True,
            narrative=f"{faction.name} outmaneuvers {target.name}, drawing away influence and resources.",
        )
    elif outcome == "partial":
        transfer = 0.10
        faction.rating = round(min(RATING_MAX, faction.rating + transfer), 4)
        target.rating = round(max(1.0, target.rating - transfer), 4)
        return ActionResult(
            "Steal", faction.id, target.id, "partial",
            margin=margin, delta=transfer,
            roll_attacker=atk, roll_defender=dfn,
            narrative=f"{faction.name} chips away at {target.name}'s standing.",
        )
    else:
        return ActionResult(
            "Steal", faction.id, target.id, "fail",
            margin=margin, delta=0.0,
            roll_attacker=atk, roll_defender=dfn,
            narrative=f"{faction.name} attempts to undermine {target.name} but is caught out.",
        )


# ── BUILD PROJECT ─────────────────────────────────────────────────────────────

def resolve_build_project(faction: Faction, project: Project) -> ActionResult:
    """Faction contributes construction work. DC 12. d20 + floor(rating)."""
    if project.status not in ("under_construction", "active"):
        return ActionResult(
            "BuildProject", faction.id, project.id, "blocked",
            narrative=f"{faction.name} cannot build — {project.name} is not in a buildable state.",
        )

    roll = random.randint(1, 20) + faction.floor
    if roll >= 12:
        increment = int(100 / max(1, project.faction_build_actions))
        project.health = min(100, project.health + increment)
        project.build_actions_this_cycle += 1
        completion = project.health >= 100 and project.status == "under_construction"
        return ActionResult(
            "BuildProject", faction.id, project.id, "success",
            delta=float(increment),
            dramatic=completion,
            narrative=(
                f"{faction.name} advances construction on {project.name} (+{increment} progress)."
                + (" Construction complete!" if completion else "")
            ),
        )
    else:
        return ActionResult(
            "BuildProject", faction.id, project.id, "fail",
            narrative=f"{faction.name} works on {project.name} but makes little headway.",
        )


# ── SABOTAGE PROJECT ──────────────────────────────────────────────────────────

def resolve_sabotage_project(faction: Faction, project: Project) -> ActionResult:
    """Any faction can sabotage any project. Contested vs project defense rating."""
    if project.status == "destroyed":
        return ActionResult(
            "SabotageProject", faction.id, project.id, "blocked",
            narrative=f"{project.name} is already destroyed.",
        )

    defense = project.defense_rating() + project.defense_bonus()
    atk_roll = random.randint(1, 20) + faction.floor
    dfn_roll = random.randint(1, 20) + defense
    margin = atk_roll - dfn_roll

    if margin >= 5:
        project.health = max(0, project.health - 25)
        destroyed = project.health == 0
        if destroyed:
            project.status = "destroyed"
        return ActionResult(
            "SabotageProject", faction.id, project.id, "decisive",
            margin=margin, delta=-25.0,
            roll_attacker=atk_roll, roll_defender=dfn_roll,
            dramatic=True,
            narrative=(
                f"{faction.name} deals a decisive blow to {project.name} (−25 health)."
                + (" The structure is destroyed!" if destroyed else "")
            ),
        )
    elif margin >= 1:
        project.health = max(0, project.health - 10)
        destroyed = project.health == 0
        if destroyed:
            project.status = "destroyed"
        return ActionResult(
            "SabotageProject", faction.id, project.id, "partial",
            margin=margin, delta=-10.0,
            roll_attacker=atk_roll, roll_defender=dfn_roll,
            narrative=f"{faction.name} damages {project.name} (−10 health).",
        )
    else:
        return ActionResult(
            "SabotageProject", faction.id, project.id, "fail",
            margin=margin, delta=0.0,
            roll_attacker=atk_roll, roll_defender=dfn_roll,
            narrative=f"{faction.name} attempts to sabotage {project.name} but fails.",
        )
