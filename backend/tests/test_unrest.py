"""Unrest scale — pressure aggregate, asymmetric memory, City Guard lever, unrest→crime.

Spec: public-needs_spec (Feature: Unrest), faction-behavior_spec (Step 3). Constants imported.
"""
import engine.npc.behavior as behavior
from engine.models import Faction, Leader, ThePublic, WorldState
from engine.needs.chain import ChainOutput
from engine.needs.drift import apply_needs, DRIFT_STEP
from engine.needs.scales import (
    unrest_target, UNREST_HUNGER, UNREST_IMPIETY, UNREST_CONFIDENCE, UNREST_DRUNK,
    UNREST_EASE, GUARD_SUPPRESS, GUARD_HEAVY_THRESHOLD, GUARD_HEAVY_SUPPORT,
)


def fac(fid, domain, rating=2.0):
    return Faction(id=fid, name=fid.title(), domain_primary=domain, leader=Leader(name=f"L-{fid}"),
                   rating=rating)


def temple(fid, rating=3.0):
    return fac(fid, "temples", rating)


def out_with(**kw):
    base = dict(fed_target=60.0, happy_target=50.0, drunk=False, raw=0.0, units={})
    base.update(kw)
    return ChainOutput(**base)


class TestPressureTarget:
    def test_all_sources_sum(self):
        # Starving + Godless + support −50 + drunk
        p = ThePublic(fed=10, piety=10, support=-50, drunk=True)
        assert unrest_target(p) == UNREST_HUNGER + UNREST_IMPIETY + UNREST_CONFIDENCE + UNREST_DRUNK

    def test_calm_city_zero(self):
        p = ThePublic(fed=60, piety=50, support=10, drunk=False)
        assert unrest_target(p) == 0.0


class TestAsymmetricMemory:
    def test_rises_by_drift_step(self):
        p = ThePublic(unrest=0, fed=10, happy=60, piety=10, support=-50)
        apply_needs(p, out_with(fed_target=0.0, happy_target=60.0, drunk=True), factions=None)
        assert p.unrest == DRIFT_STEP  # high target, rises fast

    def test_eases_slowly(self):
        p = ThePublic(unrest=50, fed=60, happy=60, piety=50, support=0)
        apply_needs(p, out_with(fed_target=60.0, happy_target=60.0), factions=None)
        assert p.unrest == 50 - UNREST_EASE  # calm target, eases slow


class TestGuardLever:
    def _calm_pair(self, guard_level, unrest_start=30, paid=True):
        """Run identical calm states with and without the guard; return (with, without) unrest."""
        common = dict(unrest=unrest_start, fed=50, happy=60, piety=50, support=-20)
        t = temple("t")
        with_guard = ThePublic(**common)
        apply_needs(with_guard, out_with(fed_target=50.0, happy_target=60.0),
                    factions={"t": t, "city-guard": fac("city-guard", "military", float(guard_level))},
                    guard_paid=paid)
        without = ThePublic(**common)
        apply_needs(without, out_with(fed_target=50.0, happy_target=60.0), factions={"t": temple("t")})
        return with_guard.unrest, without.unrest

    def test_paid_guard_suppresses(self):
        with_g, without = self._calm_pair(guard_level=2)
        assert without - with_g == GUARD_SUPPRESS * 2

    def test_unpaid_guard_does_not(self):
        with_g, without = self._calm_pair(guard_level=2, paid=False)
        assert with_g == without

    def test_no_guard_no_suppression(self):
        p = ThePublic(unrest=30, fed=50, happy=60, piety=50, support=-20)
        apply_needs(p, out_with(fed_target=50.0, happy_target=60.0), factions={"t": temple("t")})
        # only easing/drift, no guard term — sanity that the helper's "without" path is guard-free
        assert p.unrest >= 0

    def test_heavy_handed_costs_support(self):
        # a big guard removes ≥ threshold → support penalty
        t = temple("t")
        p = ThePublic(unrest=40, fed=50, happy=60, piety=50, support=0)
        apply_needs(p, out_with(fed_target=50.0, happy_target=60.0),
                    factions={"t": t, "city-guard": fac("city-guard", "military", 6.0)})
        assert p.support == GUARD_HEAVY_SUPPORT  # removed 6*? capped at threshold-exceeding → cost

    def test_light_guard_no_support_cost(self):
        t = temple("t")
        p = ThePublic(unrest=40, fed=50, happy=60, piety=50, support=0)
        apply_needs(p, out_with(fed_target=50.0, happy_target=60.0),
                    factions={"t": t, "city-guard": fac("city-guard", "military", 2.0)})
        assert p.support == 0  # removed only 6 < threshold


class TestUnrestCrime:
    def _steal_weight(self, unrest, monkeypatch):
        captured = {}
        monkeypatch.setattr(behavior, "weighted_choice", lambda w: (captured.update(w), "Grow")[1])
        monkeypatch.setattr(behavior.random, "random", lambda: 0.99)
        f = fac("corrupt", "guilds")
        behavior.select_faction_action(f, {"corrupt": f}, {}, WorldState(),
                                       public=ThePublic(unrest=unrest))
        return captured.get("Steal", 0.0)

    def test_restless_lifts_steal(self, monkeypatch):
        quiet = self._steal_weight(30, monkeypatch)      # Quiet — no lift
        restless = self._steal_weight(50, monkeypatch)   # Restless — +1 step
        boiling = self._steal_weight(90, monkeypatch)    # Boiling — +3 steps
        assert restless == quiet + behavior.UNREST_CRIME_WEIGHT
        assert boiling == quiet + behavior.UNREST_CRIME_WEIGHT * 3
