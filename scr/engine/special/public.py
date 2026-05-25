"""
The Public — support tracking, disposition derivation, trait evolution.
Called at end of each cycle after all other events are processed.
"""
from typing import Dict, List, Optional
from engine.models import ThePublic, Mayor, Faction, FactionTrait, ActionResult
from engine.npc.behavior import MAX_TRAITS, INTENSITY_ORDER


def process_the_public(
    public: ThePublic,
    mayor: Mayor,
    factions: Dict[str, Faction],
    cycle_results: List[ActionResult],
) -> List[ActionResult]:
    """Update Public state from cycle results. Sync with Mayor reputation."""
    results = []

    # Sync support from Mayor reputation (mayor.reputation["the_public"] is the source of truth)
    public.support = max(-50, min(50, mayor.get_reputation("the_public")))

    # Derive and update disposition
    old_disposition = public.disposition
    public.update_disposition()

    # Trait evolution based on disposition transitions
    results.extend(_evolve_public_traits(public, mayor, old_disposition))

    # Disposition effects on factions
    results.extend(_apply_disposition_effects(public, factions, mayor))

    if old_disposition != public.disposition:
        results.append(ActionResult(
            action="PublicDisposition",
            actor_id="the_public",
            target_id=None,
            outcome="no_op",
            dramatic=(public.disposition in ("restless", "angry")),
            narrative=f"Public mood shifted: {old_disposition} → {public.disposition} (support {public.support:+})",
        ))

    return results


def _evolve_public_traits(
    public: ThePublic,
    mayor: Mayor,
    old_disposition: str,
) -> List[ActionResult]:
    results = []
    disp = public.disposition

    if disp in ("restless", "angry"):
        _add_or_amplify(public, "distrusts", "mayor", "slight")
    if disp == "angry":
        _add_or_amplify(public, "angry at", "mayor", "moderate")
    if disp == "neutral" and old_disposition in ("restless", "angry"):
        _decay_trait(public, "distrusts", "mayor")
        _decay_trait(public, "angry at", "mayor")
    if disp == "content":
        _remove_trait(public, "distrusts", "mayor")
        _remove_trait(public, "angry at", "mayor")

    return results


def _apply_disposition_effects(
    public: ThePublic,
    factions: Dict[str, Faction],
    mayor: Mayor,
) -> List[ActionResult]:
    results = []
    disp = public.disposition

    if disp == "content":
        # Aggressive factions lose cover; decrees cost fewer AP — flagged for runner
        public._content_bonus = True
    elif disp == "angry":
        # Aggressive factions gain chaos cover — flagged for runner
        public._angry_penalty = True
        # Check for mayor removal risk
        results.append(ActionResult(
            action="RemovalRisk",
            actor_id="the_public",
            target_id="mayor",
            outcome="no_op",
            dramatic=True,
            narrative=f"Public is angry (support {public.support}): Mayor removal countdown active",
        ))

    return results


# ── Trait helpers ─────────────────────────────────────────────────────────────

def _add_or_amplify(entity, trait: str, target_id: str, min_intensity: str) -> None:
    for t in entity.traits:
        if t.trait == trait and t.target_id == target_id:
            idx = INTENSITY_ORDER.index(t.intensity)
            if idx < len(INTENSITY_ORDER) - 1:
                t.intensity = INTENSITY_ORDER[idx + 1]
            return
    if len(entity.traits) >= MAX_TRAITS:
        entity.traits.sort(key=lambda t: INTENSITY_ORDER.index(t.intensity))
        entity.traits.pop(0)
    entity.traits.append(FactionTrait(trait=trait, intensity=min_intensity, target_id=target_id))


def _decay_trait(entity, trait: str, target_id: str) -> None:
    for t in entity.traits:
        if t.trait == trait and t.target_id == target_id:
            idx = INTENSITY_ORDER.index(t.intensity)
            if idx == 0:
                entity.traits.remove(t)
            else:
                t.intensity = INTENSITY_ORDER[idx - 1]
            return


def _remove_trait(entity, trait: str, target_id: str) -> None:
    entity.traits = [t for t in entity.traits if not (t.trait == trait and t.target_id == target_id)]
