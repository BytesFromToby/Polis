"""
npc/behavior.py — Faction behavior engine (v3).

Entry point: select_faction_action(faction, factions, domains, world, projects) -> FactionPlan
Called per-faction per-turn with live current state (not a cycle-start snapshot).
Trait evolution: evolve_traits(faction, ...) -> None
"""
from __future__ import annotations
import random
from typing import Dict, List, Optional

from ..models import Faction, Domain, WorldState, FactionPlan, FactionTrait, Project


# ── Constants ─────────────────────────────────────────────────────────────────

SKIP_CHANCE = 0.05
MAX_TRAITS = 6

BASE_WEIGHTS: Dict[str, float] = {
    "Grow":            40.0,
    "Harm":            20.0,
    "Aid":             10.0,
    "Protect":         25.0,
    "Steal":           20.0,
    "BuildProject":    15.0,
    "SabotageProject": 10.0,
}

TRAIT_MODIFIERS: Dict[str, Dict[str, float]] = {
    "aggressive":    {"Harm": 20, "Steal": 10},
    "defensive":     {"Protect": 25, "Aid": 10, "Grow": 5},
    "ambitious":     {"Grow": 25, "Steal": 15, "Harm": 5},
    "paranoid":      {"Protect": 20, "Grow": -5},
    "opportunistic": {"Steal": 20, "Grow": 15, "Harm": 10},
    "expansionary":  {"Grow": 25, "Steal": 10, "Harm": 5},
    "conservative":  {"Protect": 15, "Grow": 10, "Harm": -10},
    "corrupt":       {"Steal": 25, "Harm": 15, "Grow": 5},
    "industrious":   {"BuildProject": 25, "Grow": 10, "Protect": 5},
    "destructive":   {"SabotageProject": 25, "Harm": 15, "Steal": 5},
}

INTENSITY_MULTIPLIERS: Dict[str, float] = {
    "slight":   0.5,
    "moderate": 1.0,
    "strong":   1.5,
    "very":     2.0,
}

INTENSITY_ORDER = ["slight", "moderate", "strong", "very"]


# ── Utility ───────────────────────────────────────────────────────────────────

def weighted_choice(weights: Dict[str, float]) -> str:
    actions = list(weights.keys())
    vals = [max(0.0, w) for w in weights.values()]
    total = sum(vals)
    if total <= 0:
        return random.choice(actions)
    r = random.uniform(0, total)
    cumulative = 0.0
    for action, w in zip(actions, vals):
        if w <= 0:
            continue
        cumulative += w
        if r <= cumulative:
            return action
    return actions[-1]


# ── Action Selection ──────────────────────────────────────────────────────────

def select_faction_action(
    faction: Faction,
    factions: Dict[str, Faction],
    domains: Dict[str, Domain],
    world: WorldState,
    projects: Optional[Dict[str, Project]] = None,
) -> FactionPlan:
    """Select one action and target for this faction this turn."""
    projects = projects or {}

    # ── Deal commitment override ──────────────────────────────────────────────
    if faction.committed_action:
        return _committed_plan(faction, factions, domains, projects)

    # ── Step 1: Base weights ──────────────────────────────────────────────────
    weights: Dict[str, float] = dict(BASE_WEIGHTS)

    # ── Step 2: Personality modifiers ────────────────────────────────────────
    rivals = [f for f in factions.values() if f.id != faction.id]
    rival_ids = {f.id for f in rivals}

    for ft in faction.traits:
        mult = INTENSITY_MULTIPLIERS.get(ft.intensity, 1.0)

        if ft.target_id is None:
            for action, delta in TRAIT_MODIFIERS.get(ft.trait, {}).items():
                weights[action] = weights.get(action, 0.0) + delta * mult
        else:
            if ft.target_id in rival_ids:
                if ft.trait == "distrusts":
                    weights["Protect"] = weights.get("Protect", 0.0) + 15 * mult
                elif ft.trait == "angry at":
                    weights["Harm"]  = weights.get("Harm",  0.0) + 25 * mult
                    weights["Steal"] = weights.get("Steal", 0.0) + 15 * mult
                elif ft.trait == "trusts":
                    weights["Aid"] = weights.get("Aid", 0.0) + 10 * mult
                    if rivals and all(r.id == ft.target_id for r in rivals):
                        weights["Harm"] = weights.get("Harm", 0.0) - 15 * mult
                elif ft.trait == "allied with":
                    weights["Harm"] = weights.get("Harm", 0.0) - 20 * mult
                    weights["Aid"]  = weights.get("Aid",  0.0) + 20 * mult

    # ── Leader influence ──────────────────────────────────────────────────────
    leader = faction.leader
    if leader.status != "absent":
        leader_mult = 0.5 if leader.status == "weakened" else 1.0
        faction_trait_names = {ft.trait for ft in faction.traits if ft.target_id is None}
        for lt in leader.traits:
            for action, delta in TRAIT_MODIFIERS.get(lt, {}).items():
                weights[action] = weights.get(action, 0.0) + delta * 0.25 * leader_mult

    # ── Step 3: State modifiers ───────────────────────────────────────────────
    if faction.health < 30:
        weights["Protect"] = weights.get("Protect", 0.0) + 20
        weights["Grow"]    = weights.get("Grow",    0.0) + 15
        weights["Harm"]    = weights.get("Harm",    0.0) - 10

    # Aid: pull toward shoring up a hurting ally (Friend / `allied with`, any domain)
    low_ally = _lowest_health_ally(faction, factions)
    if low_ally is None:
        weights.pop("Aid", None)
    elif low_ally.health < 50:
        weights["Aid"] = weights.get("Aid", 0.0) + 25

    domain_obj = domains.get(faction.domain_primary)
    if domain_obj and domain_obj.cap > 0:
        # utilization = Σ level; harder to grow as the domain fills
        if domain_obj.utilization >= domain_obj.cap * 0.9:
            weights["Grow"]  = weights.get("Grow",  0.0) - 20
            weights["Steal"] = weights.get("Steal", 0.0) + 15

    # Project state modifiers
    faction_domains = {faction.domain_primary}
    domain_projects = [
        p for p in projects.values()
        if any(d in faction_domains for d in p.domains)
        and p.status != "destroyed"
    ]
    rival_projects = [p for p in domain_projects if p.initiated_by != faction.id and p.initiated_by != "mayor"]

    if any(p.status == "under_construction" for p in domain_projects):
        weights["BuildProject"] = weights.get("BuildProject", 0.0) + 20

    if rival_projects:
        weights["SabotageProject"] = weights.get("SabotageProject", 0.0) + 20

    # Owned project is damaged — strong pull to repair it
    owned_damaged = [
        p for p in projects.values()
        if p.initiated_by == faction.id and p.status == "active" and p.health < 75
        and faction.domain_primary in p.domains
    ]
    if owned_damaged:
        weights["BuildProject"] = weights.get("BuildProject", 0.0) + 30

    faction_level_project = any(
        p.faction_level and p.initiated_by == faction.id and p.status == "active"
        for p in projects.values()
    )
    if faction_level_project:
        weights["Protect"] = weights.get("Protect", 0.0) + 10

    # Remove project actions if no valid targets exist
    buildable = _get_buildable_projects(faction, projects)
    sabotageable = [
        p for p in projects.values()
        if p.status != "destroyed"
        and not (getattr(p, "category", "standard") == "base" and p.status == "under_construction")
    ]
    can_initiate = _can_initiate_base(faction, domains, projects)
    if not buildable and not can_initiate:
        weights.pop("BuildProject", None)
    elif can_initiate:
        # near-cap pressure: pull toward breaking ground on a cap-raising base project
        weights["BuildProject"] = weights.get("BuildProject", 0.0) + 20
    if not sabotageable:
        weights.pop("SabotageProject", None)

    # ── Step 4: Select action ─────────────────────────────────────────────────
    if random.random() < SKIP_CHANCE:
        return FactionPlan(faction.id, "Skip", domain=faction.domain_primary)

    action = weighted_choice(weights)

    # ── Step 5: Select target ─────────────────────────────────────────────────
    target_id: Optional[str] = None

    if action in ("Harm", "Steal"):
        # same-domain rivals, excluding level-1 factions (the safe floor)
        same_domain_rivals = [
            f for f in rivals
            if f.domain_primary == faction.domain_primary and f.level > 1
        ]
        # committed_abstain: exclude the protected target for this action
        if faction.committed_abstain_action == action and faction.committed_abstain_target:
            same_domain_rivals = [f for f in same_domain_rivals if f.id != faction.committed_abstain_target]
        target_id = _pick_faction_target(faction, same_domain_rivals, domains)
        if target_id is None:
            action = "Grow"

    elif action == "Aid":
        target_id = low_ally.id if low_ally else None
        if target_id is None:
            action = "Protect"

    elif action == "BuildProject":
        project_target = _pick_build_target(faction, buildable)
        if project_target is None:
            if can_initiate:
                # break ground on a new base project in the faction's own domain
                return FactionPlan(
                    faction.id, action,
                    target_id=f"new_base:{faction.domain_primary}",
                    domain=faction.domain_primary,
                )
            action = "Grow"
        else:
            return FactionPlan(faction.id, action, target_id=project_target, domain=faction.domain_primary)

    elif action == "SabotageProject":
        project_target = _pick_sabotage_target(faction, sabotageable, factions, domains)
        if project_target is None:
            action = "Grow"
        else:
            return FactionPlan(faction.id, action, target_id=project_target, domain=faction.domain_primary)

    return FactionPlan(faction.id, action, target_id=target_id, domain=faction.domain_primary)


# ── Deal Commitment Plan ─────────────────────────────────────────────────────

def _committed_plan(
    faction: Faction,
    factions: Dict[str, Faction],
    domains: Dict[str, Domain],
    projects: Dict[str, Project],
) -> FactionPlan:
    """Return a FactionPlan forced by faction.committed_action."""
    action = faction.committed_action
    target_id: Optional[str] = faction.committed_target or None

    if action == "BuildProject":
        buildable = _get_buildable_projects(faction, projects)
        tid = target_id if target_id and target_id in {p.id for p in buildable} else _pick_build_target(faction, buildable)
        return FactionPlan(faction.id, action, target_id=tid, domain=faction.domain_primary)

    if action in ("Harm", "Steal"):
        if target_id and target_id in factions:
            return FactionPlan(faction.id, action, target_id=target_id, domain=faction.domain_primary)
        rivals = [
            f for f in factions.values()
            if f.id != faction.id and f.domain_primary == faction.domain_primary and f.level > 1
        ]
        tid = _pick_faction_target(faction, rivals, domains)
        return FactionPlan(faction.id, action, target_id=tid, domain=faction.domain_primary)

    # Protect / Grow — no target needed
    return FactionPlan(faction.id, action, target_id=target_id or None, domain=faction.domain_primary)


# ── Target Selection ──────────────────────────────────────────────────────────

def _pick_faction_target(
    faction: Faction,
    rivals: List[Faction],
    domains: Dict[str, Domain],
) -> Optional[str]:
    if not rivals:
        return None

    pool: Dict[str, float] = {r.id: 1.0 for r in rivals}

    for ft in faction.traits:
        if ft.target_id and ft.target_id in pool:
            if ft.trait in ("angry at", "distrusts"):
                pool[ft.target_id] *= 3.0

    domain_obj = domains.get(faction.domain_primary)
    if domain_obj:
        foe_domains = {r.domain_id for r in domain_obj.relationships if r.trait == "Foe"}
        for r in rivals:
            if r.domain_primary in foe_domains:
                pool[r.id] = pool.get(r.id, 1.0) * 2.0

    weakest = min(rivals, key=lambda f: f.rating)
    pool[weakest.id] = pool.get(weakest.id, 1.0) + 1.0

    return weighted_choice(pool)


def _lowest_health_ally(
    faction: Faction,
    factions: Dict[str, Faction],
) -> Optional[Faction]:
    """The most endangered ally (Friend relationship or `allied with X`), any domain.
    Returns None if the faction has no ally."""
    allied_ids = {ft.target_id for ft in faction.traits if ft.trait == "allied with" and ft.target_id}
    allies = [
        f for f in factions.values()
        if f.id != faction.id
        and (faction.get_faction_relationship(f.id) == "Friend" or f.id in allied_ids)
    ]
    if not allies:
        return None
    return min(allies, key=lambda a: a.health)


def _get_buildable_projects(
    faction: Faction,
    projects: Dict[str, Project],
) -> List[Project]:
    out: List[Project] = []
    for p in projects.values():
        if faction.domain_primary not in p.domains:
            continue
        if getattr(p, "category", "standard") == "base":
            # a base project is buildable only while under construction (active = done)
            if p.status == "under_construction":
                out.append(p)
        elif p.status in ("under_construction", "active"):
            out.append(p)
    return out


def _can_initiate_base(
    faction: Faction,
    domains: Dict[str, Domain],
    projects: Dict[str, Project],
) -> bool:
    """A faction may break ground on a new base project in its own domain when that
    domain is near cap (utilization ≥ 85% of cap) and none is already under construction."""
    domain = domains.get(faction.domain_primary)
    if domain is None or domain.cap <= 0:
        return False
    if domain.utilization < 0.85 * domain.cap:
        return False
    for p in projects.values():
        if (getattr(p, "category", "standard") == "base"
                and faction.domain_primary in p.domains
                and p.status == "under_construction"):
            return False
    return True


def _pick_build_target(faction: Faction, buildable: List[Project]) -> Optional[str]:
    if not buildable:
        return None
    # Prefer under_construction, then by progress (closest to completion first)
    under_construction = [p for p in buildable if p.status == "under_construction"]
    if under_construction:
        return max(under_construction, key=lambda p: p.health).id
    # Fallback: damaged active project
    damaged = [p for p in buildable if p.status == "active" and p.health < 100]
    if damaged:
        return min(damaged, key=lambda p: p.health).id
    return buildable[0].id


def _pick_sabotage_target(
    faction: Faction,
    sabotageable: List[Project],
    factions: Dict[str, Faction],
    domains: Optional[Dict[str, Domain]] = None,
) -> Optional[str]:
    if not sabotageable:
        return None

    pool: Dict[str, float] = {p.id: 1.0 for p in sabotageable}

    # Hostile faction-owned projects weighted ×3
    hostile_faction_ids = set()
    for ft in faction.traits:
        if ft.target_id and ft.trait in ("angry at", "distrusts"):
            hostile_faction_ids.add(ft.target_id)

    # Foe domain relationships transfer to project targeting
    foe_domains: set = set()
    if domains:
        domain_obj = domains.get(faction.domain_primary)
        if domain_obj:
            foe_domains = {r.domain_id for r in domain_obj.relationships if r.trait == "Foe"}

    for p in sabotageable:
        if p.initiated_by in hostile_faction_ids:
            pool[p.id] = pool.get(p.id, 1.0) * 3.0
        if any(d in foe_domains for d in p.domains):
            pool[p.id] = pool.get(p.id, 1.0) * 2.0
        if p.status == "active":
            pool[p.id] = pool.get(p.id, 1.0) + p.health / 100.0

    return weighted_choice(pool)


# ── Trait Evolution ───────────────────────────────────────────────────────────

def _intensity_up(current: str) -> str:
    idx = INTENSITY_ORDER.index(current) if current in INTENSITY_ORDER else 1
    return INTENSITY_ORDER[min(idx + 1, len(INTENSITY_ORDER) - 1)]


def _intensity_down(current: str) -> Optional[str]:
    idx = INTENSITY_ORDER.index(current) if current in INTENSITY_ORDER else 1
    if idx == 0:
        return None
    return INTENSITY_ORDER[idx - 1]


def _find_general_trait(faction: Faction, name: str) -> Optional[FactionTrait]:
    return next((t for t in faction.traits if t.trait == name and t.target_id is None), None)


def _find_relational_trait(faction: Faction, name: str, target_id: str) -> Optional[FactionTrait]:
    return next((t for t in faction.traits if t.trait == name and t.target_id == target_id), None)


def _add_or_amplify_general(faction: Faction, trait_name: str, default_intensity: str = "moderate") -> None:
    existing = _find_general_trait(faction, trait_name)
    if existing:
        existing.intensity = _intensity_up(existing.intensity)
    else:
        faction.traits.append(FactionTrait(trait=trait_name, intensity=default_intensity))
    _enforce_trait_cap(faction)


def _add_or_amplify_relational(faction: Faction, trait_name: str, target_id: str, default_intensity: str = "moderate") -> None:
    existing = _find_relational_trait(faction, trait_name, target_id)
    if existing:
        existing.intensity = _intensity_up(existing.intensity)
    else:
        faction.traits.append(FactionTrait(trait=trait_name, intensity=default_intensity, target_id=target_id))
    _enforce_trait_cap(faction)


def _enforce_trait_cap(faction: Faction) -> None:
    if len(faction.traits) > MAX_TRAITS:
        faction.traits.sort(key=lambda t: INTENSITY_ORDER.index(t.intensity) if t.intensity in INTENSITY_ORDER else 0)
        faction.traits.pop(0)


def evolve_traits(
    faction: Faction,
    was_harmed_by: Optional[str] = None,
    harm_landed_on: Optional[str] = None,
    repeated_harm_from: Optional[str] = None,
    grew_streak: int = 0,
    protect_streak: int = 0,
    hostile_drought: int = 0,
) -> None:
    if was_harmed_by:
        _add_or_amplify_relational(faction, "angry at", was_harmed_by, default_intensity="slight")
        _add_or_amplify_general(faction, "aggressive", default_intensity="slight")

    if harm_landed_on:
        _add_or_amplify_general(faction, "aggressive", default_intensity="moderate")

    if repeated_harm_from:
        existing = _find_relational_trait(faction, "angry at", repeated_harm_from)
        if existing:
            existing.intensity = "strong"
        else:
            faction.traits.append(FactionTrait(trait="angry at", intensity="strong", target_id=repeated_harm_from))
        _enforce_trait_cap(faction)

    if grew_streak >= 3:
        _add_or_amplify_general(faction, "ambitious", default_intensity="moderate")

    if protect_streak >= 3:
        t = _find_general_trait(faction, "defensive") or _find_general_trait(faction, "paranoid")
        if t:
            t.intensity = _intensity_up(t.intensity)
        else:
            _add_or_amplify_general(faction, "defensive", default_intensity="moderate")

    if faction.health < 20:
        existing = _find_general_trait(faction, "defensive")
        if not existing:
            faction.traits.append(FactionTrait(trait="defensive", intensity="moderate"))
            _enforce_trait_cap(faction)

    if hostile_drought >= 5:
        decayed: List[FactionTrait] = []
        for t in faction.traits:
            if t.trait in ("aggressive", "angry at"):
                new_intensity = _intensity_down(t.intensity)
                if new_intensity is None:
                    continue
                t.intensity = new_intensity
                decayed.append(t)
        faction.traits = [
            t for t in faction.traits
            if t.trait not in ("aggressive", "angry at") or t in decayed
        ]
