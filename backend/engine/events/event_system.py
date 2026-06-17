"""
event_system.py — Full event processing: random, scripted, and mayor-triggered events.
Active events are processed at Step 8 each cycle (after end-of-cycle).
"""
import random
from typing import Dict, List, Optional
from engine.models import (
    GameEvent, EventEffect, CascadeSpec,
    Faction, Domain, WorldState, ActionResult,
)


# ── Chaos → probability table ─────────────────────────────────────────────────

_CHAOS_CHANCE = {
    (0, 2): 0.05,
    (3, 5): 0.15,
    (6, 8): 0.30,
    (9, 10): 0.50,
}


def _chaos_event_chance(chaos_level: float) -> float:
    lvl = int(chaos_level)
    for (lo, hi), chance in _CHAOS_CHANCE.items():
        if lo <= lvl <= hi:
            return chance
    return 0.05


# ── Random event rolling ──────────────────────────────────────────────────────

def roll_for_random_events(
    world: WorldState,
    factions: Dict[str, Faction],
    domains: Dict[str, Domain],
    event_deck: List[dict],
    public=None,
) -> List[GameEvent]:
    """Roll for new random events this cycle. Returns newly-fired events.
    `public` enables Public-need gates on templates (events_spec — Public-need gates)."""
    if not event_deck:
        return []

    new_events = []
    for domain_id, chaos_val in world.chaos.items():
        chance = _chaos_event_chance(chaos_val)
        if random.random() > chance:
            continue

        # Filter deck entries valid for this domain
        candidates = [
            e for e in event_deck
            if e.get("type") == "random"
            and _matches_trigger(e, domain_id, chaos_val, factions, world, public)
        ]
        if not candidates:
            continue

        weights = [e.get("weight", 1) for e in candidates]
        chosen = random.choices(candidates, weights=weights, k=1)[0]
        event = _instantiate_event(chosen, factions, domains, domain_id)
        if event:
            new_events.append(event)

    return new_events


_NEED_GATE_KEYS = ("max_fed_band", "min_fed_band", "max_happy_band", "min_happy_band", "sickly",
                   "max_piety_band", "min_piety_band", "max_unrest_band", "min_unrest_band")


def _matches_trigger(
    template: dict,
    domain_id: str,
    chaos_val: float,
    factions: Dict[str, Faction],
    world: WorldState,
    public=None,
) -> bool:
    conds = template.get("trigger_conditions", {})
    if "domain" in conds and conds["domain"] != domain_id:
        return False
    if "min_chaos" in conds and chaos_val < conds["min_chaos"]:
        return False
    if "min_factions" in conds:
        count = sum(1 for f in factions.values() if f.domain_primary == domain_id)
        if count < conds["min_factions"]:
            return False
    if not _matches_need_gates(conds, public):
        return False
    return True


def _matches_need_gates(conds: dict, public) -> bool:
    """Public-need gates (events_spec). A template carrying any need gate is
    ineligible when no public is provided."""
    if not any(k in conds for k in _NEED_GATE_KEYS):
        return True
    if public is None:
        return False
    from ..needs.bands import FED_BANDS, HAPPY_BANDS, band_index, fed_band, happy_band, is_sickly
    fed_i = band_index(fed_band(public.fed), FED_BANDS)
    happy_i = band_index(happy_band(public.happy), HAPPY_BANDS)
    if "max_fed_band" in conds and fed_i > band_index(conds["max_fed_band"], FED_BANDS):
        return False
    if "min_fed_band" in conds and fed_i < band_index(conds["min_fed_band"], FED_BANDS):
        return False
    if "max_happy_band" in conds and happy_i > band_index(conds["max_happy_band"], HAPPY_BANDS):
        return False
    if "min_happy_band" in conds and happy_i < band_index(conds["min_happy_band"], HAPPY_BANDS):
        return False
    if "sickly" in conds and conds["sickly"] != is_sickly(public.health):
        return False
    from ..needs.bands import PIETY_BANDS, UNREST_BANDS, piety_band, unrest_band
    piety_i = band_index(piety_band(public.piety), PIETY_BANDS)
    unrest_i = band_index(unrest_band(public.unrest), UNREST_BANDS)
    if "max_piety_band" in conds and piety_i > band_index(conds["max_piety_band"], PIETY_BANDS):
        return False
    if "min_piety_band" in conds and piety_i < band_index(conds["min_piety_band"], PIETY_BANDS):
        return False
    if "max_unrest_band" in conds and unrest_i > band_index(conds["max_unrest_band"], UNREST_BANDS):
        return False
    if "min_unrest_band" in conds and unrest_i < band_index(conds["min_unrest_band"], UNREST_BANDS):
        return False
    return True


def _instantiate_event(
    template: dict,
    factions: Dict[str, Faction],
    domains: Dict[str, Domain],
    trigger_domain: str,
) -> Optional[GameEvent]:
    tmpl = template.get("template", {})

    # Resolve target_id: may be literal or "random_faction_in:<domain>"
    target_id = tmpl.get("target_id", trigger_domain)
    if target_id.startswith("random_faction_in:"):
        domain = target_id.split(":")[1]
        candidates = [f.id for f in factions.values() if f.domain_primary == domain]
        if not candidates:
            return None
        target_id = random.choice(candidates)

    effects = [EventEffect(**e) for e in tmpl.get("effects", [])]
    cascade_data = tmpl.get("cascade")
    cascade = None
    if cascade_data:
        cascade = CascadeSpec(
            delay=cascade_data.get("delay", 0),
            target_id=cascade_data.get("target_id", target_id),
            effects=[EventEffect(**e) for e in cascade_data.get("effects", [])],
        )

    return GameEvent(
        id=template["id"],
        name=template["name"],
        type=template.get("type", "random"),
        trigger=f"random (chaos in {trigger_domain})",
        target_type=tmpl.get("target_type", "faction"),
        target_id=target_id,
        duration=tmpl.get("duration", 1),
        cycles_remaining=tmpl.get("duration", 1),
        effects=effects,
        cascade=cascade,
        status="active",
    )


# ── Scripted event checking ───────────────────────────────────────────────────

def check_scripted_events(
    world: WorldState,
    factions: Dict[str, Faction],
    domains: Dict[str, Domain],
    treasury,
    scripted_deck: List[dict],
) -> List[GameEvent]:
    """Check if any scripted events should fire this cycle."""
    new_events = []
    for template in scripted_deck:
        if template.get("type") != "scripted":
            continue
        conds = template.get("trigger_conditions", {})
        if _scripted_conditions_met(conds, world, factions, domains, treasury):
            event = _instantiate_event(template, factions, domains, "world")
            if event:
                event.type = "scripted"
                new_events.append(event)
    return new_events


def _scripted_conditions_met(
    conds: dict,
    world: WorldState,
    factions: Dict[str, Faction],
    domains: Dict[str, Domain],
    treasury,
) -> bool:
    if "min_cycle" in conds and world.cycle < conds["min_cycle"]:
        return False
    if "max_gold" in conds and treasury and treasury.gold >= conds["max_gold"]:
        return False
    if "min_faction_rating" in conds:
        threshold = conds["min_faction_rating"]
        if not any(f.rating >= threshold for f in factions.values()):
            return False
    return True


# ── Active event processing (Step 8) ─────────────────────────────────────────

def process_active_events(
    active_events: List[GameEvent],
    factions: Dict[str, Faction],
    domains: Dict[str, Domain],
    world: WorldState,
    public=None,
) -> List[ActionResult]:
    """Apply effects of all active events. Decrement timers. Fire cascades."""
    results = []
    newly_cascading = []

    for event in list(active_events):
        if event.status == "resolved":
            continue

        if event.status == "active":
            # Apply effects this cycle
            results.extend(_apply_event_effects(event.effects, factions, domains, world, event, public))
            event.cycles_remaining -= 1

            if event.cycles_remaining <= 0:
                if event.cascade:
                    event.status = "cascading"
                    event.cascade_delay_remaining = event.cascade.delay
                else:
                    event.status = "resolved"

        elif event.status == "cascading":
            if event.cascade_delay_remaining > 0:
                event.cascade_delay_remaining -= 1
            else:
                results.extend(
                    _apply_event_effects(event.cascade.effects, factions, domains, world, event, public)
                )
                event.status = "resolved"
                results.append(ActionResult(
                    action="EventCascade",
                    actor_id=event.id,
                    target_id=event.cascade.target_id,
                    outcome="decisive",
                    dramatic=True,
                    narrative=f"Event cascade: {event.name} secondary effects fired",
                ))

    return results


def _apply_event_effects(
    effects: List[EventEffect],
    factions: Dict[str, Faction],
    domains: Dict[str, Domain],
    world: WorldState,
    event: GameEvent,
    public=None,
) -> List[ActionResult]:
    results = []
    for eff in effects:
        _apply_single_event_effect(eff, factions, domains, world, public)
        results.append(ActionResult(
            action="EventEffect",
            actor_id=event.id,
            target_id=eff.target_id,
            outcome="no_op",
            delta=eff.value,
            narrative=f"{event.name} → {eff.target_id}: {eff.field} {eff.value:+.1f} ({eff.label})",
        ))
    return results


_PUBLIC_EFFECT_FIELDS = ("piety", "unrest", "support", "fed", "happy", "health")


def _apply_single_event_effect(
    eff: EventEffect,
    factions: Dict[str, Faction],
    domains: Dict[str, Domain],
    world: WorldState,
    public=None,
) -> None:
    tid = eff.target_id

    if tid == "the_public" and public is not None and eff.field in _PUBLIC_EFFECT_FIELDS:
        # Events can finally touch the Public (events_spec 2026-06-16): clamp-apply a scale delta.
        # support is the only -50..+50 scale; the rest are 0..100.
        lo, hi = (-50, 50) if eff.field == "support" else (0, 100)
        cur = getattr(public, eff.field)
        setattr(public, eff.field, max(lo, min(hi, cur + int(eff.value))))
        return

    if tid in factions:
        faction = factions[tid]
        if eff.field == "health":
            faction.health = max(0, min(100, faction.health + int(eff.value)))
        elif eff.field == "rating":
            faction.rating = max(1.0, min(10.0, faction.rating + eff.value))
        elif eff.field == "withhold":
            # Disaster face of the supply-interruption primitive: force this faction's chain
            # contribution to 0 this cycle (value ignored). Re-asserted each active cycle; the
            # runner's end-of-cycle reset clears it (events_spec / public-needs_spec).
            faction.withholding = True

    elif tid in domains:
        domain = domains[tid]
        if eff.field == "drift":
            domain.drift = max(-1.0, min(1.0, domain.drift + eff.value))

    elif tid == "world" or eff.field == "chaos":
        # Apply to domain chaos
        domain_id = eff.target_id if eff.target_id in world.chaos else list(world.chaos.keys())[0] if world.chaos else None
        if domain_id:
            world.chaos[domain_id] = max(0.0, min(10.0, world.chaos.get(domain_id, 0) + eff.value))


# ── Mayor-triggered event creation ───────────────────────────────────────────

def create_mayor_triggered_event(
    trigger_action: str,
    target_id: str,
    factions: Dict[str, Faction],
    cycle: int,
) -> Optional[GameEvent]:
    """Create an event as a side effect of a mayor action."""

    if trigger_action == "PubliclyCondemn":
        # Rival factions in same domain get confidence boost
        target = factions.get(target_id)
        if not target:
            return None
        rival_ids = [
            f.id for f in factions.values()
            if f.id != target_id and f.domain_primary == target.domain_primary
        ]
        if not rival_ids:
            return None
        return GameEvent(
            id=f"condemn_boost_{cycle}",
            name="Rivals Emboldened",
            type="mayor_triggered",
            trigger=f"Mayor condemned {target_id}",
            target_type="faction",
            target_id=rival_ids[0],
            duration=1,
            cycles_remaining=1,
            effects=[
                EventEffect(
                    field="action_weight", target_id=rid,
                    value=5.0, label="confidence boost from condemnation"
                )
                for rid in rival_ids
            ],
            status="active",
        )

    if trigger_action == "WithholdResources":
        return GameEvent(
            id=f"withhold_pressure_{cycle}",
            name="Outside Pressure",
            type="mayor_triggered",
            trigger=f"Mayor withheld resources from {target_id}",
            target_type="faction",
            target_id=target_id,
            duration=2,
            cycles_remaining=2,
            effects=[
                EventEffect(
                    field="health", target_id=target_id,
                    value=-5.0, label="resource deprivation"
                )
            ],
            status="active",
        )

    return None
