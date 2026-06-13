"""
engine/needs/drift.py — drift, shortage, and plenty (public-needs_spec).

Turns a cycle's ChainOutput into trait movement, health/support deltas, and
population change. Constants provisional — tune by feel against
tests/test_needs_dynamics.py; tests must import them.
"""
from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING

from engine.models import ActionResult
from .bands import fed_band, happy_band
from .chain import ChainOutput

if TYPE_CHECKING:
    from engine.models import ThePublic, Mayor

DRIFT_STEP = 10                  # max trait movement toward target per cycle
HEALTH_DELTAS = {"Starving": -4, "Hungry": -2, "Well fed": +2}
SUPPORT_DELTAS = {"Starving": -5, "Hungry": -2, "Well fed": +2,
                  "Miserable": -2, "Festive": +2}
POP_GROWTH = 0.02                # ±2%/cycle
POP_MIN = 1000


def _drift_toward(value: int, target: float) -> int:
    gap = target - value
    if abs(gap) <= DRIFT_STEP:
        return int(round(target))
    return value + DRIFT_STEP if gap > 0 else value - DRIFT_STEP


def apply_needs(
    public: "ThePublic",
    out: ChainOutput,
    mayor: Optional["Mayor"] = None,
) -> List[ActionResult]:
    """Drift fed/happy toward targets, apply band effects, move population.

    Support deltas go through mayor.reputation["the_public"] when a mayor is
    present — that value is the source of truth and public.support syncs from
    it in process_the_public (see engine/special/public.py). Without a mayor,
    public.support is adjusted directly.
    """
    results: List[ActionResult] = []
    old_fed_word = fed_band(public.fed)
    old_happy_word = happy_band(public.happy)
    old_population = public.population

    public.fed = max(0, min(100, _drift_toward(public.fed, out.fed_target)))
    public.happy = max(0, min(100, _drift_toward(public.happy, out.happy_target)))
    public.drunk = out.drunk   # display cache — derived, never drifted

    new_fed_word = fed_band(public.fed)
    new_happy_word = happy_band(public.happy)

    public.health = max(0, min(100, public.health + HEALTH_DELTAS.get(new_fed_word, 0)))

    support_delta = SUPPORT_DELTAS.get(new_fed_word, 0) + SUPPORT_DELTAS.get(new_happy_word, 0)
    if support_delta:
        if mayor is not None:
            mayor.adjust_reputation("the_public", support_delta)
        else:
            public.support = max(-50, min(50, public.support + support_delta))

    if new_fed_word == "Well fed" and public.health >= 70:
        public.population = max(POP_MIN, round(public.population * (1 + POP_GROWTH)))
    elif new_fed_word == "Starving" or public.health < 30:
        public.population = max(POP_MIN, round(public.population * (1 - POP_GROWTH)))

    if new_fed_word != old_fed_word or new_happy_word != old_happy_word:
        results.append(ActionResult(
            action="PublicNeeds",
            actor_id="the_public",
            target_id=None,
            outcome="no_op",
            dramatic=(new_fed_word in ("Starving", "Hungry") and new_fed_word != old_fed_word),
            narrative=f"The people are {new_fed_word} and {new_happy_word} "
                      f"(were {old_fed_word}, {old_happy_word}).",
        ))
    if public.population != old_population:
        grew = public.population > old_population
        results.append(ActionResult(
            action="PublicNeeds",
            actor_id="the_public",
            target_id=None,
            outcome="no_op",
            dramatic=not grew,
            narrative=(f"The city {'grows' if grew else 'dwindles'}: "
                       f"{old_population:,} → {public.population:,}."),
        ))
    return results
