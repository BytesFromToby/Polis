"""
engine/special/removal.py — terminal fail-state resolutions (fail-states_spec).

The "one end-state, many triggers" spine: each resolution can latch world.game_over with a
recorded cause when the run is lost. Implements mayor_spec "Mayor Removal" as an actual end state
rather than the narrative-only warnings that preceded it.

Triggers:
  - Mayor removal spiral (process_mayor_removal): Public reputation ≤ removal_rep_threshold
    → "public_revolt"; debt > removal_threshold (moneylender coalition) → "removal_coalition".
    A countdown starts at removal_grace_cycles when a trigger holds, decrements while it persists,
    and clears the moment every trigger lifts (the player stabilised in time).
  - Population collapse (process_population): a latched low-population warning with hysteresis
    (on ≤ pop_warn_on, off > pop_warn_off) that drains support while active; population reaching
    pop_collapse ends the run ("population_collapse") on profiles where pop_floor_is_death.

Deferred (noted in the spec): the 3+-hostile-factions coalition pressure and bankruptcy's distinct
grace; the election verdict and assassination are separate triggers in later slices.
"""
from __future__ import annotations
import random
from typing import Dict, List, Optional, TYPE_CHECKING

from engine.models import ActionResult
from engine.balance import NORMAL as _BAL

if TYPE_CHECKING:
    from engine.models import WorldState, Mayor, Treasury, Faction, ThePublic


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


def _drain_support(public: "ThePublic", mayor: Optional["Mayor"], delta: int) -> None:
    """Route a support delta through mayor reputation (source of truth) or public.support."""
    if mayor is not None:
        mayor.adjust_reputation("the_public", delta)
    else:
        public.support = max(-50, min(50, public.support + delta))


def process_population(
    world: "WorldState",
    public: "ThePublic",
    mayor: Optional["Mayor"] = None,
    balance=_BAL,
) -> List[ActionResult]:
    """Population collapse (terminal) + the latched low-population warning (fail-states_spec)."""
    results: List[ActionResult] = []
    if world.game_over:
        return results

    pop = public.population

    # Collapse → terminal, on profiles where the floor is lethal (normal/hard, not easy).
    if balance.pop_floor_is_death and pop <= balance.pop_collapse:
        world.game_over = True
        world.end_cause = "population_collapse"
        public.pop_warning = False
        results.append(ActionResult(
            action="PopulationCollapse", actor_id="the_public", target_id="mayor",
            outcome="decisive", dramatic=True,
            narrative=f"The city empties — only {pop:,} souls remain. The reign ends.",
        ))
        return results

    # Latched warning with hysteresis: on at/below pop_warn_on, off only once above pop_warn_off.
    if not public.pop_warning and pop <= balance.pop_warn_on:
        public.pop_warning = True
        results.append(ActionResult(
            action="PopulationWarning", actor_id="the_public", target_id="mayor",
            outcome="no_op", dramatic=True,
            narrative=f"The city is emptying ({pop:,}) — confidence bleeds away each cycle.",
        ))
    elif public.pop_warning and pop > balance.pop_warn_off:
        public.pop_warning = False
        results.append(ActionResult(
            action="PopulationRecovered", actor_id="the_public", target_id="mayor",
            outcome="no_op", dramatic=True,
            narrative=f"The city refills ({pop:,}) — the exodus has eased.",
        ))

    # Drain support each cycle the warning holds (feeds the removal spiral).
    if public.pop_warning and balance.pop_warn_support_drain:
        _drain_support(public, mayor, balance.pop_warn_support_drain)

    return results


def faction_reputation_sum(mayor: "Mayor", factions: Dict[str, "Faction"]) -> int:
    """Σ per-faction Mayor reputation — the collective standing of the great houses."""
    return sum(mayor.get_reputation(f.id) for f in factions.values())


def process_coup(
    world: "WorldState",
    mayor: "Mayor",
    factions: Optional[Dict[str, "Faction"]] = None,
    balance=_BAL,
    rng: Optional[random.Random] = None,
) -> List[ActionResult]:
    """The conspiracy of the great houses (fail-states_spec). When their collective standing falls
    below `coup_rep_threshold` a plot forms; each cycle it rolls for an assassination the player can
    fight off — by recovering faction reputation, or with a strong City Guard that defends the Mayor.
    A *risk*, not a countdown — non-deterministic but not arbitrary."""
    results: List[ActionResult] = []
    if world.game_over or not balance.coup_enabled or not factions:
        return results

    rep_sum = faction_reputation_sum(mayor, factions)
    if rep_sum >= balance.coup_rep_threshold:
        return results  # the houses are not collectively hostile enough to plot

    guard = factions.get("city-guard")
    guard_level = guard.level if guard is not None else 0
    chance = max(0.0, balance.coup_base_chance - guard_level * balance.coup_guard_protection)

    r = rng or random
    if r.random() < chance:
        world.game_over = True
        world.end_cause = "assassinated"
        results.append(ActionResult(
            action="MayorAssassinated", actor_id="factions", target_id="mayor",
            outcome="decisive", dramatic=True,
            narrative="A conspiracy of the great houses strikes the Mayor down. The reign ends in blood.",
        ))
    else:
        results.append(ActionResult(
            action="CoupPlot", actor_id="factions", target_id="mayor",
            outcome="no_op", dramatic=True,
            narrative=(f"The great houses conspire against the Mayor (standing {rep_sum:+d}) — "
                       f"a knife waits in the dark."),
        ))
    return results
