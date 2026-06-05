"""
actions/faction.py — Faction action resolvers (v5, demo redesign).

Actions: Grow, Protect, Aid, Harm, Steal, BuildProject, SabotageProject.
Block removed. Harm damages health; Protect/Aid heal; Steal transfers rank.
A faction reduced to 0 health Breaks — that is resolved by the cycle layer.
"""
from __future__ import annotations
import random
from typing import Dict

from ..models import Faction, Domain, Project, ActionResult
from ..formulas import grow_increment, resolve_contest, RATING_MAX


# ── GROW ──────────────────────────────────────────────────────────────────────

def resolve_grow(faction: Faction, domains: Dict[str, Domain]) -> ActionResult:
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

    level_before = faction.level
    increment = grow_increment(level_before)
    faction.rating = round(min(RATING_MAX, faction.rating + increment), 4)
    leveled = faction.level > level_before

    return ActionResult(
        "Grow", faction.id, None, "success",
        delta=increment,
        dramatic=leveled,
        narrative=(
            f"{faction.name} expands its influence."
            + (" They rise to a new level of power." if leveled else "")
        ),
    )


# ── PROTECT ───────────────────────────────────────────────────────────────────

def resolve_protect(faction: Faction) -> ActionResult:
    old = faction.health
    faction.health = min(100, faction.health + 50)
    return ActionResult(
        "Protect", faction.id, None, "success",
        delta=float(faction.health - old),
        narrative=f"{faction.name} fortifies itself, recovering its strength.",
    )


# ── AID ───────────────────────────────────────────────────────────────────────

def resolve_aid(faction: Faction, target: Faction) -> ActionResult:
    """Heal an allied faction (+25 health). Ally validation (Friend / `allied with`)
    is performed by the behavior engine's target selection; cross-domain is allowed."""
    old = target.health
    target.health = min(100, target.health + 25)
    return ActionResult(
        "Aid", faction.id, target.id, "success",
        delta=float(target.health - old),
        narrative=f"{faction.name} sends aid to {target.name}, shoring up their strength.",
    )


# ── HARM ──────────────────────────────────────────────────────────────────────

def resolve_harm(faction: Faction, target: Faction, factions: Dict[str, Faction]) -> ActionResult:
    if target.domain_primary != faction.domain_primary:
        return ActionResult(
            "Harm", faction.id, target.id, "blocked",
            narrative=f"{faction.name} cannot reach {target.name} — different domain.",
        )
    if target.level <= 1:
        return ActionResult(
            "Harm", faction.id, target.id, "blocked",
            narrative=f"{faction.name} stays its hand against {target.name}, already at the bottom.",
        )

    outcome, margin, atk, dfn = resolve_contest(faction, target)

    if outcome == "decisive":
        target.health = max(0, target.health - 30)
        return ActionResult(
            "Harm", faction.id, target.id, "decisive",
            margin=margin, delta=30.0, roll_attacker=atk, roll_defender=dfn,
            dramatic=True,
            narrative=f"{faction.name} strikes hard against {target.name}, battering their organization.",
        )
    elif outcome == "partial":
        target.health = max(0, target.health - 15)
        return ActionResult(
            "Harm", faction.id, target.id, "partial",
            margin=margin, delta=15.0, roll_attacker=atk, roll_defender=dfn,
            narrative=f"{faction.name} pressures {target.name}, wearing them down.",
        )
    else:
        return ActionResult(
            "Harm", faction.id, target.id, "fail",
            margin=margin, delta=0.0, roll_attacker=atk, roll_defender=dfn,
            narrative=f"{faction.name} moves against {target.name} but fails to land a blow.",
        )


# ── STEAL ─────────────────────────────────────────────────────────────────────

def resolve_steal(faction: Faction, target: Faction) -> ActionResult:
    if target.domain_primary != faction.domain_primary:
        return ActionResult(
            "Steal", faction.id, target.id, "blocked",
            narrative=f"{faction.name} cannot steal from {target.name} — different domain.",
        )
    if target.level <= 1:
        return ActionResult(
            "Steal", faction.id, target.id, "blocked",
            narrative=f"{faction.name} finds nothing worth taking from {target.name}.",
        )

    outcome, margin, atk, dfn = resolve_contest(faction, target)
    if outcome == "fail":
        return ActionResult(
            "Steal", faction.id, target.id, "fail",
            margin=margin, delta=0.0, roll_attacker=atk, roll_defender=dfn,
            narrative=f"{faction.name} attempts to undermine {target.name} but is caught out.",
        )

    base = 0.5 / (faction.level + 1)
    transfer = round(base if outcome == "decisive" else base / 2, 4)
    faction.rating = round(min(RATING_MAX, faction.rating + transfer), 4)
    target.rating = round(max(1.0, target.rating - transfer), 4)
    return ActionResult(
        "Steal", faction.id, target.id, outcome,
        margin=margin, delta=transfer, roll_attacker=atk, roll_defender=dfn,
        dramatic=(outcome == "decisive"),
        narrative=(
            f"{faction.name} draws influence away from {target.name}."
            if outcome == "decisive"
            else f"{faction.name} chips away at {target.name}'s standing."
        ),
    )


# ── BUILD PROJECT ─────────────────────────────────────────────────────────────

def resolve_build_project(faction: Faction, project: Project) -> ActionResult:
    """Faction contributes construction work. DC 12, d20 + level.
    Base projects build in work units (4 = complete) and are domain-gated; legacy
    (standard/tax_collection) projects keep the v4 health-as-progress path."""
    if project.category == "base":
        return _build_base_project(faction, project)

    if project.status not in ("under_construction", "active"):
        return ActionResult(
            "BuildProject", faction.id, project.id, "blocked",
            narrative=f"{faction.name} cannot build — {project.name} is not in a buildable state.",
        )

    roll = random.randint(1, 20) + faction.level
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


def _build_base_project(faction: Faction, project: Project) -> ActionResult:
    """Base project: 4 work units to complete. Domain-gated (own domain only).
    Each successful d20+level vs DC 12 adds one work unit; 4 units → active."""
    if faction.domain_primary not in project.domains:
        return ActionResult(
            "BuildProject", faction.id, project.id, "blocked",
            narrative=f"{faction.name} cannot build {project.name} — not its domain.",
        )
    if project.status != "under_construction":
        return ActionResult(
            "BuildProject", faction.id, project.id, "blocked",
            narrative=f"{faction.name} cannot build {project.name} — already complete.",
        )

    roll = random.randint(1, 20) + faction.level
    if roll < 12:
        return ActionResult(
            "BuildProject", faction.id, project.id, "fail",
            narrative=f"{faction.name} labors on {project.name} but makes little headway.",
        )

    project.build_progress += 1
    project.build_actions_this_cycle += 1
    completed = project.build_progress >= 4
    if completed:
        project.status = "active"
        project.health = 100
    return ActionResult(
        "BuildProject", faction.id, project.id, "success",
        delta=1.0, dramatic=completed,
        narrative=(
            f"{faction.name} advances {project.name} ({project.build_progress}/4)."
            + (" It is complete and now stands active." if completed else "")
        ),
    )


# ── SABOTAGE PROJECT ──────────────────────────────────────────────────────────

def resolve_sabotage_project(faction: Faction, project: Project) -> ActionResult:
    """Any faction can sabotage any built project. Contested vs project defense rating.
    A base project under construction has no structural health yet — nothing to burn."""
    if project.category == "base" and project.status == "under_construction":
        return ActionResult(
            "SabotageProject", faction.id, project.id, "blocked",
            narrative=f"{project.name} is still a building site — nothing to sabotage yet.",
        )
    if project.status == "destroyed":
        return ActionResult(
            "SabotageProject", faction.id, project.id, "blocked",
            narrative=f"{project.name} is already destroyed.",
        )

    defense = project.defense_rating() + project.defense_bonus()
    atk_roll = random.randint(1, 20) + faction.level
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
