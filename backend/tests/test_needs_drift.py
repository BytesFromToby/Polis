"""Tests for engine/needs/drift.py — drift, shortage, plenty per public-needs_spec."""
from engine.models import ThePublic, Mayor
from engine.needs.chain import ChainOutput, compute_chain
from engine.needs.drift import (
    DRIFT_STEP, HEALTH_DELTAS, SUPPORT_DELTAS, POP_GROWTH, POP_MIN, apply_needs,
)
from loaders import load_chains, load_factions_from_json
import os

CHAINS = load_chains()
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def out_with(fed_target=60.0, happy_target=50.0, wine_happy=0.0):
    return ChainOutput(fed_target=fed_target, happy_target=happy_target, wine_happy=wine_happy)


class TestDrift:
    def test_far_below_rises_exactly_step(self):
        p = ThePublic(fed=30)
        apply_needs(p, out_with(fed_target=60.0))
        assert p.fed == 30 + DRIFT_STEP

    def test_near_target_lands_exactly(self):
        p = ThePublic(fed=55)
        apply_needs(p, out_with(fed_target=60.0))
        assert p.fed == 60

    def test_drifts_down_too(self):
        p = ThePublic(fed=90, health=100)
        apply_needs(p, out_with(fed_target=20.0))
        assert p.fed == 80


class TestHealthDriver:
    def test_starving_drains(self):
        p = ThePublic(fed=0, health=50)
        apply_needs(p, out_with(fed_target=0.0))
        assert p.health == 50 + HEALTH_DELTAS["Starving"]

    def test_hungry_drains(self):
        p = ThePublic(fed=30, health=50)
        apply_needs(p, out_with(fed_target=30.0))
        assert p.health == 50 + HEALTH_DELTAS["Hungry"]

    def test_well_fed_heals_capped(self):
        p = ThePublic(fed=90, health=99)
        apply_needs(p, out_with(fed_target=90.0))
        assert p.health == 100

    def test_fed_band_neutral(self):
        p = ThePublic(fed=60, health=50)
        apply_needs(p, out_with(fed_target=60.0))
        assert p.health == 50


class TestSupportDeltas:
    def test_starving_and_miserable_stack_via_mayor(self):
        p = ThePublic(fed=0, happy=0)
        m = Mayor()
        apply_needs(p, out_with(fed_target=0.0, happy_target=0.0), mayor=m)
        assert m.get_reputation("the_public") == (
            SUPPORT_DELTAS["Starving"] + SUPPORT_DELTAS["Miserable"]
        )

    def test_well_fed_festive_positive_no_mayor(self):
        p = ThePublic(fed=90, happy=90, support=0)
        apply_needs(p, out_with(fed_target=90.0, happy_target=90.0))
        assert p.support == SUPPORT_DELTAS["Well fed"] + SUPPORT_DELTAS["Festive"]


class TestPopulation:
    def test_grows_when_well_fed_and_healthy(self):
        p = ThePublic(fed=90, health=80, population=20000)
        apply_needs(p, out_with(fed_target=90.0))
        assert p.population == round(20000 * (1 + POP_GROWTH))

    def test_shrinks_when_starving(self):
        p = ThePublic(fed=0, health=80, population=20000)
        apply_needs(p, out_with(fed_target=0.0))
        assert p.population == round(20000 * (1 - POP_GROWTH))

    def test_shrinks_when_health_critical(self):
        p = ThePublic(fed=60, health=20, population=20000)
        apply_needs(p, out_with(fed_target=60.0))
        assert p.population == round(20000 * (1 - POP_GROWTH))

    def test_floor(self):
        p = ThePublic(fed=0, health=0, population=POP_MIN)
        apply_needs(p, out_with(fed_target=0.0))
        assert p.population == POP_MIN

    def test_demand_scales_with_population(self):
        factions = load_factions_from_json(os.path.join(DATA_DIR, "factions.json"))
        small = compute_chain(factions, 20000, CHAINS)
        large = compute_chain(factions, 40000, CHAINS)
        assert abs(large.fed_target - small.fed_target / 2) < 1e-9


class TestDrunkCity:
    def test_strong_winepressers_weak_ovenmen(self):
        factions_balanced = load_factions_from_json(os.path.join(DATA_DIR, "factions.json"))
        factions_swapped = load_factions_from_json(os.path.join(DATA_DIR, "factions.json"))
        factions_swapped["winepressers"].rating = 4.0
        factions_swapped["ovenmen"].rating = 1.0

        results = {}
        for name, factions in (("balanced", factions_balanced), ("swapped", factions_swapped)):
            p = ThePublic()
            for _ in range(10):
                out = compute_chain(factions, p.population, CHAINS)
                apply_needs(p, out)
            results[name] = p

        assert results["swapped"].happy > results["balanced"].happy
        assert results["swapped"].fed < results["balanced"].fed
