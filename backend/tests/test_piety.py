"""Piety scale — driver, bands, drift, crisis-blame modifier, zealot tax (public-needs_spec).

Constants imported, never copied.
"""
from engine.models import Faction, Leader, ThePublic
from engine.needs.bands import piety_band, unrest_band
from engine.needs.chain import ChainOutput, TOIL_MULT
from engine.needs.drift import apply_needs, DRIFT_STEP, SUPPORT_DELTAS
from engine.needs.scales import (
    piety_supply, piety_target, PIETY_PER_LEVEL, PIETY_PARITY, PIETY_BLAME, ZEALOT_SUPPORT_TAX,
)
from serializer import serialize_the_public, deserialize_the_public


def temple(fid, rating):
    return Faction(id=fid, name=fid.title(), domain_primary="temples",
                   leader=Leader(name=f"L-{fid}"), rating=rating)


def out_with(**kw):
    base = dict(fed_target=60.0, happy_target=50.0, wine_happy=0.0, raw=0.0, units={})
    base.update(kw)
    return ChainOutput(**base)


class TestSerialization:
    def test_round_trip_piety_unrest(self):
        p = ThePublic(piety=72, unrest=44)
        d = serialize_the_public(p)
        assert d["piety"] == 72 and d["unrest"] == 44
        assert d["piety_band"] == "Devout" and d["unrest_band"] == "Restless"
        p2 = deserialize_the_public(d)
        assert p2.piety == 72 and p2.unrest == 44

    def test_absent_fields_default(self):
        p = deserialize_the_public({"fed": 60})  # legacy save without piety/unrest
        assert p.piety == 50 and p.unrest == 10


class TestBands:
    def test_piety_boundaries(self):
        assert [piety_band(v) for v in (20, 21, 40, 41, 60, 61, 80, 81)] == \
            ["Godless", "Lax", "Lax", "Observant", "Observant", "Devout", "Devout", "Zealous"]

    def test_unrest_boundaries(self):
        assert [unrest_band(v) for v in (20, 40, 60, 80, 100)] == \
            ["Placid", "Quiet", "Restless", "Agitated", "Boiling"]


class TestDriver:
    def test_supply_temple_only(self):
        factions = {
            "t1": temple("t1", 3.0),                  # level 3
            "t2": temple("t2", 2.0),                  # level 2
            "ovenmen": Faction(id="ovenmen", name="O", domain_primary="guilds",
                               leader=Leader(name="L")),  # not a temple
        }
        assert piety_supply(factions) == PIETY_PER_LEVEL * (3 + 2)

    def test_zero_temples_zero_target(self):
        factions = {"ovenmen": Faction(id="ovenmen", name="O", domain_primary="guilds",
                                       leader=Leader(name="L"))}
        assert piety_target(factions, 20000) == 0.0

    def test_toil_and_withhold_on_temple(self):
        base = {"t": temple("t", 3.0)}
        assert piety_supply(base) == PIETY_PER_LEVEL * 3
        base["t"].toiling = True
        assert piety_supply(base) == PIETY_PER_LEVEL * 3 * TOIL_MULT
        base["t"].toiling = False
        base["t"].withholding = True
        assert piety_supply(base) == 0.0  # a priestly strike

    def test_target_parity(self):
        # supply == demand*parity → target 100*1/parity capped... pick levels so supply==demand
        factions = {"t": temple("t", 5.0)}  # level 5 → supply 20
        pop = int(PIETY_PER_LEVEL * 5 / PIETY_PARITY * 1000)  # demand s.t. target == 100
        assert piety_target(factions, pop) == 100.0


class TestDrift:
    def test_drifts_by_step_when_far(self):
        p = ThePublic(piety=40)
        factions = {"t": temple("t", 10.0)}  # huge supply → target 100
        apply_needs(p, out_with(), factions=factions)
        assert p.piety == 40 + DRIFT_STEP

    def test_lands_without_overshoot(self):
        p = ThePublic(piety=95)
        factions = {"t": temple("t", 10.0)}  # target 100, gap 5 ≤ step
        apply_needs(p, out_with(), factions=factions)
        assert p.piety == 100


class TestCrisisBlame:
    def _starving_support_drop(self, piety):
        # fed_target 0 → drifts toward Starving; happy neutral (Content, no delta)
        p = ThePublic(fed=20, happy=60, piety=piety, support=0)
        apply_needs(p, out_with(fed_target=0.0, happy_target=60.0), factions={})
        return p.support  # negative

    def test_godless_amplifies_devout_cushions(self):
        godless = self._starving_support_drop(10)     # band Godless ×1.5
        observant = self._starving_support_drop(50)   # band Observant ×1.0
        devout = self._starving_support_drop(70)      # band Devout ×0.75
        assert godless < observant < devout           # godless loses the most support
        # exact: observant == base Starving delta
        assert observant == SUPPORT_DELTAS["Starving"]
        assert godless == round(SUPPORT_DELTAS["Starving"] * PIETY_BLAME["Godless"])

    def test_positive_deltas_unscaled(self):
        # Well fed (+2) + Festive (+2) with Godless piety → not amplified (blame only hits negatives)
        p = ThePublic(fed=80, happy=80, piety=10, support=0)
        apply_needs(p, out_with(fed_target=100.0, happy_target=100.0), factions={})
        assert p.support == SUPPORT_DELTAS["Well fed"] + SUPPORT_DELTAS["Festive"]


class TestZealotTax:
    def test_zealous_costs_support(self):
        p = ThePublic(piety=95, fed=60, happy=60, support=0)
        factions = {"t": temple("t", 10.0)}  # keeps piety Zealous
        apply_needs(p, out_with(), factions=factions)
        assert piety_band(p.piety) == "Zealous"
        assert p.support == ZEALOT_SUPPORT_TAX

    def test_observant_no_tax(self):
        p = ThePublic(piety=50, fed=60, happy=60, support=0)
        factions = {"t": temple("t", 3.0)}
        apply_needs(p, out_with(), factions=factions)
        assert p.support == 0
