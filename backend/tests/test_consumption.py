"""Consumption scale — wine-driven driver, bands, drunk-derivation, Dry health drain.

Spec: public-needs_spec (Feature: Consumption). Constants imported, never copied.
"""
import os
import random

from engine.cycle.runner import run_cycle
from engine.models import Mayor, ThePublic, Treasury
from engine.needs.bands import consumption_band
from engine.needs.chain import ChainOutput
from engine.needs.drift import apply_needs, DRIFT_STEP
from engine.needs.scales import (
    consumption_target, is_drunk, production_efficiency,
    CONSUMPTION_PARITY, CONSUMPTION_DRY_HEALTH,
)
from loaders import load_state_from_json, load_chains
from serializer import serialize_the_public, deserialize_the_public

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CHAINS = load_chains()


def out_with(wine_happy=0.0, fed_target=60.0, happy_target=50.0):
    return ChainOutput(fed_target=fed_target, happy_target=happy_target, wine_happy=wine_happy)


class TestSerialization:
    def test_round_trip(self):
        p = ThePublic(consumption=72)
        d = serialize_the_public(p)
        assert d["consumption"] == 72 and d["consumption_band"] == "Tipsy"
        assert deserialize_the_public(d).consumption == 72

    def test_absent_defaults_45(self):
        assert deserialize_the_public({"fed": 60}).consumption == 45


class TestBands:
    def test_boundaries(self):
        assert [consumption_band(v) for v in (20, 40, 60, 80, 100)] == \
            ["Dry", "Sober", "Tempered", "Tipsy", "Sodden"]


class TestDriver:
    def test_parity_maps_to_midpoint(self):
        pop = 20000
        demand = pop / 1000.0
        # wine/demand == PARITY → target 50 (Tempered midpoint)
        assert abs(consumption_target(CONSUMPTION_PARITY * demand, pop) - 50.0) < 1e-9

    def test_zero_wine_zero_target(self):
        assert consumption_target(0.0, 20000) == 0.0

    def test_more_wine_higher(self):
        a = consumption_target(1.0, 20000)
        b = consumption_target(2.0, 20000)
        assert b > a

    def test_drifts_by_step_no_overshoot(self):
        p = ThePublic(consumption=20)
        apply_needs(p, out_with(wine_happy=100.0), factions=None)  # huge wine → target 100
        assert p.consumption == 20 + DRIFT_STEP
        p2 = ThePublic(consumption=95)
        apply_needs(p2, out_with(wine_happy=100.0), factions=None)
        assert p2.consumption == 100  # gap ≤ step → lands, no overshoot


class TestDrunkDerivation:
    def test_drunk_iff_tipsy_or_sodden(self):
        assert not is_drunk(55)   # Tempered
        assert not is_drunk(30)   # Sober
        assert is_drunk(65)       # Tipsy
        assert is_drunk(90)       # Sodden

    def test_apply_needs_sets_drunk_from_band(self):
        # sustained high wine → consumption climbs into Tipsy/Sodden → drunk True
        p = ThePublic(consumption=78)
        apply_needs(p, out_with(wine_happy=100.0), factions=None)
        assert consumption_band(p.consumption) in ("Tipsy", "Sodden")
        assert p.drunk is True

    def test_tempered_not_drunk(self):
        p = ThePublic(consumption=50)
        apply_needs(p, out_with(wine_happy=CONSUMPTION_PARITY * 20.0), factions=None)
        assert p.drunk is False


class TestStdCityRestsTempered:
    """Regression for the PARITY mis-tune (inspector FAIL 2026-06-17): the standard city must
    REST in Tempered and never pin Sodden/drunk. This asserts real run_cycle state — not the
    tautology `consumption_target(PARITY*demand) == 50`."""

    def _run(self, seed, cycles=30):
        random.seed(seed)
        world, factions, domains = load_state_from_json(DATA_DIR)
        public = ThePublic()
        bands = []
        for _ in range(cycles):
            run_cycle(world, factions, domains, mayor=Mayor(), treasury=Treasury(),
                      public=public, chains=CHAINS)
            bands.append(consumption_band(public.consumption))
        return bands

    def test_fresh_city_starts_tempered(self):
        # the opening cycles sit in the sweet spot, not pinned at an extreme
        bands = self._run(seed=101, cycles=5)
        assert all(b == "Tempered" for b in bands)

    def test_never_pins_sodden(self):
        # across seeds, the resting city is not chronically drunk (was 100% Sodden when mis-tuned)
        for seed in (101, 202, 303):
            bands = self._run(seed)
            assert bands.count("Sodden") == 0

    def test_resting_efficiency_has_no_drunk_drag(self):
        # a Tempered city carries no consumption penalty in the production wire
        p = ThePublic(health=50, consumption=50)  # Healthy + Tempered
        assert production_efficiency(p) == 1.0


class TestDryHealthDrain:
    def test_dry_drains_health(self):
        p = ThePublic(consumption=10, health=80)
        apply_needs(p, out_with(wine_happy=0.0), factions=None)  # stays Dry
        assert consumption_band(p.consumption) == "Dry"
        assert p.health == 80 + CONSUMPTION_DRY_HEALTH

    def test_tempered_no_drain(self):
        p = ThePublic(consumption=50, health=80)
        apply_needs(p, out_with(wine_happy=CONSUMPTION_PARITY * 20.0), factions=None)
        assert p.health == 80
