"""
engine/needs/drift.py — drift, shortage, and plenty (public-needs_spec).

Turns a cycle's ChainOutput into trait movement, health/support deltas, and
population change. Constants provisional — tune by feel against
tests/test_needs_dynamics.py; tests must import them.
"""
from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING

from engine.models import ActionResult
from .bands import fed_band, happy_band, piety_band
from .chain import ChainOutput
from .scales import piety_target, blame_factor, ZEALOT_SUPPORT_TAX

if TYPE_CHECKING:
    from engine.models import ThePublic, Mayor, Faction

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


def _apply_support(public: "ThePublic", delta: int, mayor: Optional["Mayor"]) -> None:
    """Route a support delta through mayor reputation (source of truth) or public.support."""
    if not delta:
        return
    if mayor is not None:
        mayor.adjust_reputation("the_public", delta)
    else:
        public.support = max(-50, min(50, public.support + delta))


def apply_needs(
    public: "ThePublic",
    out: ChainOutput,
    factions: Optional[Dict[str, "Faction"]] = None,
    mayor: Optional["Mayor"] = None,
) -> List[ActionResult]:
    """Drift fed/happy/piety toward targets, apply band effects, move population, then unrest.

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

    # Support deltas, with the piety crisis-blame modifier scaling only the NEGATIVE part
    # (a godless city blames the impious Mayor for the heavens' displeasure; a devout one endures).
    fed_d = SUPPORT_DELTAS.get(new_fed_word, 0)
    happy_d = SUPPORT_DELTAS.get(new_happy_word, 0)
    raw = fed_d + happy_d
    neg = sum(d for d in (fed_d, happy_d) if d < 0)
    if neg:
        blamed = round(neg * blame_factor(public.piety))
        raw += (blamed - neg)   # replace the negative part with its scaled version
    _apply_support(public, raw, mayor)

    if new_fed_word == "Well fed" and public.health >= 70:
        public.population = max(POP_MIN, round(public.population * (1 + POP_GROWTH)))
    elif new_fed_word == "Starving" or public.health < 30:
        public.population = max(POP_MIN, round(public.population * (1 - POP_GROWTH)))

    # Piety — drift toward the temple-produced target, then the zealot tax (high piety is not
    # purely good: over-mighty temples defy the Mayor).
    if factions is not None:
        public.piety = max(0, min(100, _drift_toward(public.piety, piety_target(factions, public.population))))
        if piety_band(public.piety) == "Zealous":
            _apply_support(public, ZEALOT_SUPPORT_TAX, mayor)

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
