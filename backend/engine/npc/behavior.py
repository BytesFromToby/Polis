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

# Withhold (actions_spec / faction-behavior_spec): base 0; earns weight only from anger —
# the Mayor's standing with the faction being low. Keeps a strike structurally rare + legible.
WITHHOLD_ANGER_THRESHOLD = -20   # mayor reputation with the faction at/below this → strike pressure
WITHHOLD_ANGER_WEIGHT = 40.0     # weight per step; +1 step per 10 points below the threshold

# Rally / Agitate — sway the Public's opinion of the Mayor, gated by the faction's standing with him.
RALLY_THRESHOLD = 20             # mayor reputation with the faction at/above this → rally pressure
AGITATE_THRESHOLD = -20          # at/below this → agitate pressure (mirrors the Withhold anger gate)
RALLY_WEIGHT = 30.0              # weight per step; +1 step per 10 points beyond the threshold
AGITATE_WEIGHT = 30.0
UNREST_CRIME_WEIGHT = 15.0       # Steal weight per unrest band at/above Restless (public-needs_spec)
CONFIDENCE_EMBOLDEN_WEIGHT = 10.0  # Harm/Steal lift at low confidence (Hostile/Suspicious)
CONFIDENCE_COOP_WEIGHT = 10.0      # Harm/Steal damp at high confidence (Favorable/Beloved)

BASE_WEIGHTS: Dict[str, float] = {
    "Grow":            40.0,
    "Harm":            20.0,
    "Aid":             10.0,
    "Protect":         25.0,
    "Steal":           20.0,
    "Toil":            10.0,   # only factions with a chain role keep this (public-needs_spec)
    "Withhold":        0.0,    # chain-role only; lifts off 0 only under anger (Step 3)
    "BuildProject":    15.0,
    "SabotageProject": 10.0,
    "Rally":           0.0,    # any faction; lifts only from high Mayor standing (Step 3)
    "Agitate":         0.0,    # any faction; lifts only from low Mayor standing (Step 3)
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
    "industrious":   {"BuildProject": 25, "Grow": 10, "Protect": 5, "Toil": 10},
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
    base_stacks: Optional[Dict[str, "BaseProjectStack"]] = None,
    public: Optional["ThePublic"] = None,
    chain_roles: Optional[set] = None,
    mayor: Optional["Mayor"] = None,
) -> FactionPlan:
    """Select one action and target for this faction this turn.

    `public` and `chain_roles` (faction ids with a supply-chain role) enable the
    Toil action and its shortage modifier (public-needs_spec); absent → no Toil."""
    projects = projects or {}
    base_stacks = base_stacks or {}

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
    # Toil — only chain-role factions may toil; shortage pulls them toward it
    # (the prosocial branch beside hungry→Steal; public-needs_spec).
    if chain_roles and faction.id in chain_roles:
        if public is not None:
            from ..needs.bands import FED_BANDS, band_index, fed_band
            if band_index(fed_band(public.fed), FED_BANDS) <= band_index("Hungry", FED_BANDS):
                weights["Toil"] = weights.get("Toil", 0.0) + 25
        # Withhold — base 0; anger (low Mayor standing with this faction) lifts it off the floor,
        # scaling with how far below the threshold (faction-behavior_spec Step 3).
        if mayor is not None:
            rep = mayor.get_reputation(faction.id)
            if rep <= WITHHOLD_ANGER_THRESHOLD:
                steps = 1 + (WITHHOLD_ANGER_THRESHOLD - rep) // 10
                weights["Withhold"] = weights.get("Withhold", 0.0) + WITHHOLD_ANGER_WEIGHT * steps
    else:
        weights.pop("Toil", None)
        weights.pop("Withhold", None)

    # Rally / Agitate — any faction sways the Public's opinion of the Mayor based on its standing
    # with him (faction-behavior_spec Step 3 / actions_spec). Base 0; lifts only at the tiers, and
    # scales one step per 10 points beyond the threshold — mirroring the Withhold anger gate.
    if mayor is not None:
        m_rep = mayor.get_reputation(faction.id)
        if m_rep >= RALLY_THRESHOLD:
            steps = 1 + (m_rep - RALLY_THRESHOLD) // 10
            weights["Rally"] = weights.get("Rally", 0.0) + RALLY_WEIGHT * steps
        elif m_rep <= AGITATE_THRESHOLD:
            steps = 1 + (AGITATE_THRESHOLD - m_rep) // 10
            weights["Agitate"] = weights.get("Agitate", 0.0) + AGITATE_WEIGHT * steps

    # Unrest → crime: civic disorder is cover for theft (public-needs_spec Unrest). Restless+
    # lifts Steal, scaling one step at Agitated and again at Boiling.
    if public is not None:
        from ..needs.bands import UNREST_BANDS, band_index, unrest_band
        u = band_index(unrest_band(public.unrest), UNREST_BANDS)
        restless = band_index("Restless", UNREST_BANDS)
        if u >= restless:
            weights["Steal"] = weights.get("Steal", 0.0) + UNREST_CRIME_WEIGHT * (u - restless + 1)

    # Confidence posture: a distrusted Mayor can't shield rivals (low → embolden Harm/Steal); the
    # public's backing raises the cost of open aggression (high → damp). Neutral = no change.
    if public is not None:
        from ..needs.bands import confidence_band
        cb = confidence_band(public.support)
        if cb in ("Hostile", "Suspicious"):
            weights["Harm"] = weights.get("Harm", 0.0) + CONFIDENCE_EMBOLDEN_WEIGHT
            weights["Steal"] = weights.get("Steal", 0.0) + CONFIDENCE_EMBOLDEN_WEIGHT
        elif cb in ("Favorable", "Beloved"):
            weights["Harm"] = weights.get("Harm", 0.0) - CONFIDENCE_COOP_WEIGHT
            weights["Steal"] = weights.get("Steal", 0.0) - CONFIDENCE_COOP_WEIGHT

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

    # Project state modifiers — base-project stacks (projects_spec v6).
    own_stack = base_stacks.get(faction.domain_primary)
    own_domain_obj = domains.get(faction.domain_primary)
    # Continue an in-progress build on the faction's own domain.
    can_build_own = own_stack is not None and own_stack.top_is_building()
    # Break ground under near-cap pressure (utilization ≥ 0.85×cap) with a pristine/empty top.
    can_initiate_own = (
        own_stack is not None
        and (own_stack.count == 0 or own_stack.top_is_pristine())
        and own_domain_obj is not None and own_domain_obj.cap > 0
        and own_domain_obj.utilization >= 0.85 * own_domain_obj.cap
    )
    if can_build_own or can_initiate_own:
        weights["BuildProject"] = weights.get("BuildProject", 0.0) + 20
    else:
        weights.pop("BuildProject", None)

    # Sabotage: any other domain with a standing stack (count ≥ 1) is attackable.
    sabotage_domains = [
        did for did, s in base_stacks.items()
        if did != faction.domain_primary and s.count >= 1
    ]
    if sabotage_domains:
        weights["SabotageProject"] = weights.get("SabotageProject", 0.0) + 20
    else:
        weights.pop("SabotageProject", None)

    # Targetless committed_abstain (e.g. "cease agitating") — zero that action's weight outright.
    # A *targeted* abstain (Harm/Steal vs a named faction) is handled in target selection below.
    if faction.committed_abstain_action and not faction.committed_abstain_target:
        weights[faction.committed_abstain_action] = 0.0

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
        # Target is the faction's own domain stack (the dispatcher breaks ground if needed).
        if can_build_own or can_initiate_own:
            return FactionPlan(faction.id, action, target_id=faction.domain_primary,
                               domain=faction.domain_primary)
        action = "Grow"

    elif action == "SabotageProject":
        target_domain = _pick_sabotage_stack(faction, sabotage_domains, domains)
        if target_domain is None:
            action = "Grow"
        else:
            return FactionPlan(faction.id, action, target_id=target_domain,
                               domain=faction.domain_primary)

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
        # Build the faction's own domain stack (dispatcher breaks ground if needed).
        return FactionPlan(faction.id, action, target_id=faction.domain_primary,
                           domain=faction.domain_primary)

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


def _pick_sabotage_stack(
    faction: Faction,
    sabotage_domains: List[str],
    domains: Optional[Dict[str, Domain]] = None,
) -> Optional[str]:
    """Choose which domain's base-project stack to sabotage. Foe-domain stacks are
    weighted ×3 (projects_spec v6 — sabotage targets the domain stack's top)."""
    if not sabotage_domains:
        return None
    pool: Dict[str, float] = {did: 1.0 for did in sabotage_domains}
    if domains:
        domain_obj = domains.get(faction.domain_primary)
        if domain_obj:
            foe_domains = {r.domain_id for r in domain_obj.relationships if r.trait == "Foe"}
            for did in pool:
                if did in foe_domains:
                    pool[did] *= 3.0
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
