"""Tests for engine/needs/bands.py — band boundaries per public-needs_spec."""
from engine.models import ThePublic
from engine.needs.bands import (
    FED_BANDS, HAPPY_BANDS, fed_band, happy_band, band_index, is_sickly, needs_line,
)
from serializer import serialize_the_public, deserialize_the_public


class TestFedBands:
    def test_boundaries(self):
        assert fed_band(0) == "Starving"
        assert fed_band(20) == "Starving"
        assert fed_band(21) == "Hungry"
        assert fed_band(45) == "Hungry"
        assert fed_band(46) == "Fed"
        assert fed_band(75) == "Fed"
        assert fed_band(76) == "Well fed"
        assert fed_band(100) == "Well fed"


class TestHappyBands:
    def test_boundaries(self):
        assert happy_band(0) == "Miserable"
        assert happy_band(20) == "Miserable"
        assert happy_band(21) == "Sullen"
        assert happy_band(45) == "Sullen"
        assert happy_band(46) == "Content"
        assert happy_band(75) == "Content"
        assert happy_band(76) == "Festive"
        assert happy_band(100) == "Festive"


class TestBandIndex:
    def test_orders_fed_bands(self):
        assert band_index("Starving", FED_BANDS) == 0
        assert band_index("Well fed", FED_BANDS) == 3
        assert band_index("Sullen", HAPPY_BANDS) == 1


class TestSickly:
    def test_threshold(self):
        assert is_sickly(39)
        assert not is_sickly(40)


class TestNeedsLine:
    def test_plain(self):
        p = ThePublic(fed=80, happy=10, health=100)
        assert needs_line(p, drunk=False) == "The people are Well fed, and Miserable."

    def test_all_flags(self):
        p = ThePublic(fed=80, happy=10, health=30)
        assert needs_line(p, drunk=True) == "The people are Well fed, drunk, sickly, and Miserable."


class TestSerialization:
    def test_round_trip(self):
        p = ThePublic(support=12, health=88, population=31000, fed=33, happy=71)
        p2 = deserialize_the_public(serialize_the_public(p))
        assert (p2.support, p2.health, p2.population, p2.fed, p2.happy) == (12, 88, 31000, 33, 71)
        assert p2.disposition == p.disposition

    def test_missing_fields_default(self):
        p = deserialize_the_public({})
        assert (p.support, p.health, p.population, p.fed, p.happy) == (0, 100, 20000, 60, 50)
