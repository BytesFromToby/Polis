"""Consumption scale — wine-driven driver, bands, drunk-derivation, Dry health drain.

Spec: public-needs_spec (Feature: Consumption). Constants imported, never copied.
"""
from engine.models import ThePublic
from engine.needs.bands import consumption_band
from engine.needs.chain import ChainOutput
from engine.needs.drift import apply_needs, DRIFT_STEP
from engine.needs.scales import (
    consumption_target, is_drunk, CONSUMPTION_PARITY, CONSUMPTION_DRY_HEALTH,
)
from serializer import serialize_the_public, deserialize_the_public


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
