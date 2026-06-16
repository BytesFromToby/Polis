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
from ..projects import apply_build_step, apply_sabotage_damage


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


# ── TOIL ──────────────────────────────────────────────────────────────────────

def resolve_toil(faction: Faction) -> ActionResult:
    """The faction works its trade instead of maneuvering (public-needs_spec).
    Sets the cycle-only `toiling` flag; the needs step multiplies this faction's
    chain contribution by TOIL_MULT. No rank, health, or project effect."""
    faction.toiling = True
    return ActionResult(
        "Toil", faction.id, None, "success",
        narrative=f"{faction.name} bend to their trade.",
    )


# ── WITHHOLD ───────────────────────────────────────────────────────────────────

def resolve_withhold(faction: Faction) -> ActionResult:
    """Toil's evil twin (public-needs_spec / actions_spec). The faction refuses to
    deliver its trade: sets the cycle-only `withholding` flag; the needs step
    multiplies this faction's chain contribution by 0. Pure opportunity cost —
    no rank, health, or project effect."""
    faction.withholding = True
    return ActionResult(
        "Withhold", faction.id, None, "success",
        narrative=f"{faction.name} seal their stores against the city.",
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

def resolve_build_project(faction: Faction, stack) -> ActionResult:
    """A faction contributes construction work to its own domain's base-project stack
    (projects_spec v6). Domain-gated; d20 + level vs DC 12. A success adds build_step%
    to the building top; reaching 100% completes it. Initiation (breaking ground) is
    handled by the dispatcher before this is called."""
    domain_id = stack.domain
    if faction.domain_primary not in stack.domains:
        return ActionResult(
            "BuildProject", faction.id, domain_id, "blocked",
            narrative=f"{faction.name} cannot build {stack.name} — not its domain.",
        )
    if not stack.top_is_building():
        return ActionResult(
            "BuildProject", faction.id, domain_id, "blocked",
            narrative=f"{faction.name} cannot build {stack.name} — no build site.",
        )

    roll = random.randint(1, 20) + faction.level
    if roll < 12:
        return ActionResult(
            "BuildProject", faction.id, domain_id, "fail",
            narrative=f"{faction.name} labors on {stack.name} but makes little headway.",
        )

    completed = apply_build_step(stack)
    stack.build_actions_this_cycle += 1
    return ActionResult(
        "BuildProject", faction.id, domain_id, "success",
        delta=float(stack.build_step), dramatic=completed,
        narrative=(
            f"{faction.name} advances {stack.name} ({int(stack.progress)}%)."
            + (" It is complete and now stands active." if completed else "")
        ),
    )


# ── SABOTAGE PROJECT ──────────────────────────────────────────────────────────

def resolve_sabotage_project(faction: Faction, stack) -> ActionResult:
    """Any faction can sabotage a domain's base-project stack — always the top, build
    site included (projects_spec v6). Contested vs the top's defense rating. Decisive
    −25%, partial −10%, fail 0 applied to `progress`; the destruction rule (count drops
    only on a hit while already at 0) is handled by apply_sabotage_damage."""
    domain_id = stack.domain
    if stack.count == 0:
        return ActionResult(
            "SabotageProject", faction.id, domain_id, "blocked",
            narrative=f"There is no {stack.name} to sabotage.",
        )

    defense = stack.defense_rating() + stack.defense_bonus()
    atk_roll = random.randint(1, 20) + faction.level
    dfn_roll = random.randint(1, 20) + defense
    margin = atk_roll - dfn_roll

    if margin >= 5:
        amount = 25.0
        destroyed = apply_sabotage_damage(stack, amount)
        return ActionResult(
            "SabotageProject", faction.id, domain_id, "decisive",
            margin=margin, delta=-amount,
            roll_attacker=atk_roll, roll_defender=dfn_roll, dramatic=True,
            narrative=(
                f"{faction.name} deals a decisive blow to {stack.name} (−25%)."
                + (" An instance is destroyed!" if destroyed else "")
            ),
        )
    elif margin >= 1:
        amount = 10.0
        destroyed = apply_sabotage_damage(stack, amount)
        return ActionResult(
            "SabotageProject", faction.id, domain_id, "partial",
            margin=margin, delta=-amount,
            roll_attacker=atk_roll, roll_defender=dfn_roll,
            narrative=(
                f"{faction.name} damages {stack.name} (−10%)."
                + (" An instance is destroyed!" if destroyed else "")
            ),
        )
    else:
        return ActionResult(
            "SabotageProject", faction.id, domain_id, "fail",
            margin=margin, delta=0.0,
            roll_attacker=atk_roll, roll_defender=dfn_roll,
            narrative=f"{faction.name} attempts to sabotage {stack.name} but fails.",
        )
