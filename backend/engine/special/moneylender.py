"""
Moneylender — leverage mechanics, removal coalition trigger.
Called each cycle after treasury processing.
"""
from typing import Dict, List
from engine.models import Treasury, Mayor, Faction, FactionTrait, ActionResult
from engine.npc.behavior import INTENSITY_ORDER, MAX_TRAITS
from engine.balance import NORMAL as _BAL


# Tunables live in engine/balance.py; names preserved here for the modules/tests that import them.
LEVERAGE_THRESHOLD = _BAL.leverage_threshold
REMOVAL_THRESHOLD = _BAL.removal_threshold
REMOVAL_GRACE_CYCLES = _BAL.removal_grace_cycles


def process_moneylender(
    treasury: Treasury,
    mayor: Mayor,
    factions: Dict[str, Faction],
    moneylender_id: str = "moneylender",
    removal_countdown: List[int] = None,
) -> List[ActionResult]:
    """Apply moneylender leverage effects. Returns results."""
    results = []

    if treasury.debt <= 0:
        return results

    if treasury.debt > LEVERAGE_THRESHOLD:
        results.append(ActionResult(
            action="MoneylenderLeverage",
            actor_id=moneylender_id,
            target_id="mayor",
            outcome="no_op",
            narrative=f"Moneylender leverage active (debt {treasury.debt}): Steal +10 vs all factions",
        ))
        # Flag for behavior engine: Moneylender gets +10 Steal this cycle
        ml = factions.get(moneylender_id)
        if ml:
            ml._leverage_steal_bonus = 10

    if treasury.debt > REMOVAL_THRESHOLD:
        # Add 'angry at Mayor' trait to moneylender faction
        ml = factions.get(moneylender_id)
        if ml:
            _add_or_amplify(ml, "angry at", "mayor", "moderate")

        results.append(ActionResult(
            action="MoneylenderAngry",
            actor_id=moneylender_id,
            target_id="mayor",
            outcome="no_op",
            dramatic=True,
            narrative=f"Moneylender is furious (debt {treasury.debt}): removal coalition possible",
        ))

        # Removal coalition trigger
        if removal_countdown is not None:
            if len(removal_countdown) == 0:
                removal_countdown.append(REMOVAL_GRACE_CYCLES)
            else:
                removal_countdown[0] -= 1
                if removal_countdown[0] <= 0:
                    results.append(ActionResult(
                        action="MayorRemovalAttempt",
                        actor_id=moneylender_id,
                        target_id="mayor",
                        outcome="decisive",
                        dramatic=True,
                        narrative="Moneylender backs removal coalition — Mayor under threat",
                    ))

    return results


def _add_or_amplify(faction: Faction, trait: str, target_id: str, min_intensity: str) -> None:
    for t in faction.traits:
        if t.trait == trait and t.target_id == target_id:
            idx = INTENSITY_ORDER.index(t.intensity)
            if idx < len(INTENSITY_ORDER) - 1:
                t.intensity = INTENSITY_ORDER[idx + 1]
            return
    if len(faction.traits) >= MAX_TRAITS:
        faction.traits.sort(key=lambda t: INTENSITY_ORDER.index(t.intensity))
        faction.traits.pop(0)
    faction.traits.append(FactionTrait(trait=trait, intensity=min_intensity, target_id=target_id))
