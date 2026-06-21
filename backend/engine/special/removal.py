"""
engine/special/removal.py — the terminal Mayor-removal resolution (fail-states_spec).

One place that decides whether the Mayor loses office and the run ends. Multiple triggers feed
a single countdown on the Mayor; when it elapses the run is over (world.game_over latches with a
recorded cause). Implements mayor_spec "Mayor Removal" as an actual end state rather than the
narrative-only warnings that preceded it.

Slice 1 triggers:
  - Public reputation ≤ balance.removal_rep_threshold  → cause "public_revolt"
  - Treasury debt > balance.removal_threshold (the moneylender coalition) → cause "removal_coalition"

The countdown starts at balance.removal_grace_cycles when a trigger first holds, decrements each
cycle it persists, and clears the moment every trigger lifts (the player stabilised in time).

Deferred (noted in the spec): the 3+-hostile-factions coalition pressure and bankruptcy's distinct
grace; population collapse and the election verdict are separate triggers in later slices.
"""
from __future__ import annotations
from typing import Dict, List, Optional, TYPE_CHECKING

from engine.models import ActionResult
from engine.balance import NORMAL as _BAL

if TYPE_CHECKING:
    from engine.models import WorldState, Mayor, Treasury, Faction


def _active_trigger(mayor: "Mayor", treasury: Optional["Treasury"], balance) -> Optional[str]:
    """Return the cause string for the dominant active removal trigger, or None if stable."""
    if treasury is not None and treasury.debt > balance.removal_threshold:
        return "removal_coalition"
    if mayor.get_reputation("the_public") <= balance.removal_rep_threshold:
        return "public_revolt"
    return None


def process_mayor_removal(
    world: "WorldState",
    mayor: "Mayor",
    treasury: Optional["Treasury"] = None,
    factions: Optional[Dict[str, "Faction"]] = None,
    balance=_BAL,
) -> List[ActionResult]:
    """Advance the removal spiral one cycle. Sets world.game_over when the countdown elapses."""
    results: List[ActionResult] = []

    if world.game_over:
        return results  # already resolved; nothing further happens

    cause = _active_trigger(mayor, treasury, balance)

    # No trigger active → the Mayor stabilised; clear any in-progress countdown.
    if cause is None:
        if mayor.removal_countdown is not None:
            mayor.removal_countdown = None
            results.append(ActionResult(
                action="RemovalAverted", actor_id="the_public", target_id="mayor",
                outcome="no_op", dramatic=True,
                narrative="The removal coalition dissolves — the Mayor has steadied the city.",
            ))
        return results

    # Trigger active → start or advance the countdown.
    if mayor.removal_countdown is None:
        mayor.removal_countdown = balance.removal_grace_cycles
        results.append(ActionResult(
            action="RemovalCountdown", actor_id="the_public", target_id="mayor",
            outcome="no_op", dramatic=True,
            narrative=(f"A removal coalition forms ({cause.replace('_', ' ')}): "
                       f"{mayor.removal_countdown} cycles to recover or be removed."),
        ))
        return results

    mayor.removal_countdown -= 1
    if mayor.removal_countdown > 0:
        results.append(ActionResult(
            action="RemovalCountdown", actor_id="the_public", target_id="mayor",
            outcome="no_op", dramatic=True,
            narrative=(f"The removal coalition holds ({cause.replace('_', ' ')}): "
                       f"{mayor.removal_countdown} cycles remain."),
        ))
        return results

    # Countdown elapsed → the Mayor is removed; the run ends.
    world.game_over = True
    world.end_cause = cause
    mayor.removal_countdown = None
    results.append(ActionResult(
        action="MayorRemoved", actor_id="the_public", target_id="mayor",
        outcome="decisive", dramatic=True,
        narrative=("The Mayor is removed from office. The reign ends "
                   f"({cause.replace('_', ' ')})."),
    ))
    return results
