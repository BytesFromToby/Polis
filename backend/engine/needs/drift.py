"""
engine/needs/drift.py — drift, shortage, and plenty (public-needs_spec).

Turns a cycle's ChainOutput into trait movement, health/support deltas, and
population change. Constants provisional — tune by feel against
tests/test_needs_dynamics.py; tests must import them.
"""
from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING

from engine.models import ActionResult
from .bands import fed_band, happy_band, piety_band, unrest_band
from .chain import ChainOutput
from .scales import (
    piety_target, blame_factor, ZEALOT_SUPPORT_TAX,
    unrest_target, UNREST_EASE, GUARD_SUPPRESS, GUARD_HEAVY_THRESHOLD, GUARD_HEAVY_SUPPORT,
    consumption_target, is_drunk, CONSUMPTION_DRY_HEALTH,
)
from .bands import consumption_band
from engine.balance import NORMAL as _BAL

if TYPE_CHECKING:
    from engine.models import ThePublic, Mayor, Faction

# Tunables live in engine/balance.py; names preserved here for the modules/tests that import them.
DRIFT_STEP = _BAL.drift_step     # max trait movement toward target per cycle
HEALTH_DELTAS = _BAL.health_deltas
SUPPORT_DELTAS = _BAL.support_deltas
POP_GROWTH = _BAL.pop_growth     # ±fraction/cycle
POP_MIN = _BAL.pop_min


def _drift_toward(value: int, target: float, step: int = DRIFT_STEP) -> int:
    gap = target - value
    if abs(gap) <= step:
        return int(round(target))
    return value + step if gap > 0 else value - step


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
    guard_paid: bool = True,
    balance=_BAL,
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

    step = balance.drift_step
    public.fed = max(0, min(100, _drift_toward(public.fed, out.fed_target, step)))
    public.happy = max(0, min(100, _drift_toward(public.happy, out.happy_target, step)))

    new_fed_word = fed_band(public.fed)
    new_happy_word = happy_band(public.happy)

    public.health = max(0, min(100, public.health + balance.health_deltas.get(new_fed_word, 0)))

    # Support deltas, with the piety crisis-blame modifier scaling only the NEGATIVE part
    # (a godless city blames the impious Mayor for the heavens' displeasure; a devout one endures).
    fed_d = balance.support_deltas.get(new_fed_word, 0)
    happy_d = balance.support_deltas.get(new_happy_word, 0)
    raw = fed_d + happy_d
    neg = sum(d for d in (fed_d, happy_d) if d < 0)
    if neg:
        blamed = round(neg * blame_factor(public.piety, balance))
        raw += (blamed - neg)   # replace the negative part with its scaled version
    _apply_support(public, raw, mayor)

    if new_fed_word == "Well fed" and public.health >= 70:
        public.population = max(balance.pop_min, round(public.population * (1 + balance.pop_growth)))
    elif new_fed_word == "Starving" or public.health < 30:
        public.population = max(balance.pop_min, round(public.population * (1 - balance.pop_growth)))

    # Piety — drift toward the temple-produced target, then the zealot tax (high piety is not
    # purely good: over-mighty temples defy the Mayor).
    if factions is not None:
        public.piety = max(0, min(100, _drift_toward(public.piety, piety_target(factions, public.population, balance), step)))
        if piety_band(public.piety) == "Zealous":
            _apply_support(public, balance.zealot_support_tax, mayor)

    # Consumption — wine-driven (no misery→drink loop). Drift toward target, then derive `drunk`
    # from the band and apply the Dry bad-water health drain. Settles before unrest reads `drunk`.
    public.consumption = max(0, min(100, _drift_toward(public.consumption,
                                                       consumption_target(out.wine_happy, public.population, balance), step)))
    public.drunk = is_drunk(public.consumption)
    if consumption_band(public.consumption) == "Dry":
        public.health = max(0, min(100, public.health + balance.consumption_dry_health))

    # Unrest — the pressure aggregate (reads the just-settled piety band). Asymmetric memory:
    # rises toward a higher target fast, eases toward a lower one slowly.
    target = unrest_target(public, balance)
    if target >= public.unrest:
        public.unrest = min(100, _drift_toward(public.unrest, target, step))
    else:
        public.unrest = max(0, public.unrest - balance.unrest_ease)

    # City Guard — costed symptom suppression (does not touch the cause/target). Only if the
    # guard is present and was paid this cycle. Heavy-handedness breeds resentment.
    if factions is not None:
        guard = factions.get("city-guard")
        if guard is not None and guard.level >= 1 and guard_paid:
            removed = min(public.unrest, balance.guard_suppress * guard.level)
            public.unrest -= removed
            if removed >= balance.guard_heavy_threshold:
                _apply_support(public, balance.guard_heavy_support, mayor)

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
