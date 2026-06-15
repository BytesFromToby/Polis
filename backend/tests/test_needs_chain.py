"""Tests for engine/needs/chain.py — the food chains per public-needs_spec.

Constants live in data/chains.json (data, not Python) — read them from the loaded
chain defs, never hardcode the numbers, so a re-tune doesn't silently rot the tests.
"""
import copy

from engine.models import Faction, Leader
from engine.needs.chain import (
    TOIL_MULT, PARITY_TARGET, POP_PER_SUPPLY_UNIT, DRUNK_THRESHOLD,
    ChainOutput, chain_role_faction_ids, compute_chain,
)
from loaders import load_chains


def mk_faction(fid, domain, rating):
    return Faction(id=fid, name=fid.title(), domain_primary=domain,
                   leader=Leader(name=f"L-{fid}"), rating=rating)


def mk_city(aristo_ratings=(4.0, 3.0, 2.0), ovenmen=2.0, winepressers=2.0):
    factions = {}
    for i, r in enumerate(aristo_ratings):
        factions[f"estate{i}"] = mk_faction(f"estate{i}", "aristocracy", r)
    factions["ovenmen"] = mk_faction("ovenmen", "guilds", ovenmen)
    factions["winepressers"] = mk_faction("winepressers", "guilds", winepressers)
    return factions


CHAINS = load_chains()
HARVEST = next(c for c in CHAINS if c["id"] == "harvest")
FISHERY = next(c for c in CHAINS if c["id"] == "fishery")
HPL = HARVEST["producers"]["per_level"]                 # harvest per-level
CAP = HARVEST["processors"][0]["per_level_capacity"]    # processor per-level capacity
WINE_HPU = HARVEST["processors"][1]["happy_per_unit"]   # winepressers happy/unit
PORRIDGE_FPU = HARVEST["unprocessed"]["fed_per_unit"]
FPL = FISHERY["producers"]["per_level"]                 # fish per-level
FFP = FISHERY["unprocessed"]["fed_per_unit"]            # fish fed/unit


class TestLoader:
    def test_loads_two_chains(self):
        assert [c["id"] for c in CHAINS] == ["harvest", "fishery"]

    def test_missing_file_returns_empty(self):
        assert load_chains("nonexistent/chains.json") == []


class TestChainRoles:
    def test_harvest_roles(self):
        factions = mk_city()
        roles = chain_role_faction_ids(CHAINS, factions)
        assert roles == {"estate0", "estate1", "estate2", "ovenmen", "winepressers"}


class TestPurity:
    def test_no_mutation_and_deterministic(self):
        factions = mk_city()
        snapshot = copy.deepcopy({fid: (f.rating, f.health, f.toiling) for fid, f in factions.items()})
        out1 = compute_chain(factions, 20000, CHAINS)
        out2 = compute_chain(factions, 20000, CHAINS)
        assert out1 == out2
        assert snapshot == {fid: (f.rating, f.health, f.toiling) for fid, f in factions.items()}


class TestProduction:
    def test_raw_per_aristocracy_level(self):
        factions = mk_city(aristo_ratings=(4.0, 3.0, 2.0))
        out = compute_chain(factions, 20000, CHAINS)
        assert out.raw == HPL * (4 + 3 + 2)

    def test_dead_estates(self):
        # No aristocracy factions (and no netmenders) → zero raw → nothing produced.
        factions = mk_city()
        for i in range(3):
            del factions[f"estate{i}"]
        out = compute_chain(factions, 20000, CHAINS)
        assert out.raw == 0
        assert all(v == 0 for v in out.units.values())
        assert out.fed_target == 0


class TestSplit:
    def test_under_capacity_proportional_no_leftover(self):
        # one level-3 estate → raw HPL*3, well under capacity 24 → proportional, no porridge
        factions = mk_city(aristo_ratings=(3.0,))
        out = compute_chain(factions, 20000, CHAINS)
        raw = HPL * 3
        assert out.units["bread"] == raw * 0.5
        assert out.units["wine"] == raw * 0.5
        assert out.units["porridge"] == 0

    def test_over_capacity_full_caps_plus_porridge(self):
        # three level-9 estates → raw HPL*27, over capacity 24 → each cap 12, remainder porridge
        factions = mk_city(aristo_ratings=(9.0, 9.0, 9.0))
        out = compute_chain(factions, 20000, CHAINS)
        cap_each = CAP * 2  # ovenmen / winepressers at level 2
        assert out.units["bread"] == cap_each
        assert out.units["wine"] == cap_each
        assert out.units["porridge"] == HPL * 27 - 2 * cap_each

    def test_conservation(self):
        for ratings in [(4.0, 3.0, 2.0), (1.0,), (9.0, 9.0, 9.0)]:
            factions = mk_city(aristo_ratings=ratings)
            out = compute_chain(factions, 20000, CHAINS)
            assert abs(sum(out.units.values()) - out.raw) < 1e-9


class TestPorridgeFloor:
    def test_no_processors_degrades_not_cliffs(self):
        factions = mk_city()
        del factions["ovenmen"]
        del factions["winepressers"]
        out = compute_chain(factions, 20000, CHAINS)
        raw = HPL * 9
        assert out.raw == raw
        assert out.units["porridge"] == raw
        expected_fed = min(100.0, PARITY_TARGET * (PORRIDGE_FPU * raw) / (20000 / POP_PER_SUPPLY_UNIT))
        assert abs(out.fed_target - expected_fed) < 1e-9
        assert out.fed_target > 0


class TestDrunkThreshold:
    def test_flips_across_the_boundary(self):
        # drunk = wine_happy / demand >= DRUNK_THRESHOLD; boundary computed from live wine output
        factions = mk_city()
        wine_units = compute_chain(factions, 20000, CHAINS).units["wine"]
        wine_happy = wine_units * WINE_HPU
        boundary_pop = int(wine_happy / DRUNK_THRESHOLD * POP_PER_SUPPLY_UNIT)
        assert compute_chain(factions, boundary_pop - 1000, CHAINS).drunk
        assert not compute_chain(factions, boundary_pop + 1000, CHAINS).drunk


class TestToil:
    def test_toiling_producer(self):
        factions = mk_city(aristo_ratings=(3.0,))
        baseline = compute_chain(factions, 20000, CHAINS)
        factions["estate0"].toiling = True
        boosted = compute_chain(factions, 20000, CHAINS)
        assert boosted.raw == baseline.raw * TOIL_MULT

    def test_toiling_processor(self):
        # ovenmen toiling: cap 12→18, total 30 ≥ raw HPL*9 → proportional, more bread
        factions = mk_city()
        factions["ovenmen"].toiling = True
        out = compute_chain(factions, 20000, CHAINS)
        raw = HPL * 9
        oven_cap = CAP * 2 * TOIL_MULT
        total_cap = oven_cap + CAP * 2
        assert abs(out.units["bread"] - raw * (oven_cap / total_cap)) < 1e-9
        assert out.units["bread"] > raw * 0.5  # more than the non-toiling proportional share
        assert out.units["porridge"] == 0


def mk_fish_city(netmenders=2.0, with_other_harbor=False):
    factions = {"netmenders": mk_faction("netmenders", "harbor", netmenders)}
    if with_other_harbor:
        factions["quaymen"] = mk_faction("quaymen", "harbor", 4.0)
    return factions


class TestFishery:
    def test_faction_keyed_sums_only_netmenders(self):
        # another harbor faction must contribute no fish (producer is faction-keyed)
        out = compute_chain(mk_fish_city(with_other_harbor=True), 20000, CHAINS)
        assert out.units["fish"] == FPL * 2   # netmenders level 2 only
        assert out.raw == FPL * 2

    def test_processor_less_routes_raw_to_fed(self):
        out = compute_chain(mk_fish_city(netmenders=2.0), 20000, CHAINS)
        raw_fish = FPL * 2
        assert out.units["fish"] == raw_fish
        demand = 20000 / POP_PER_SUPPLY_UNIT
        expected_fed = min(100.0, PARITY_TARGET * (raw_fish * FFP) / demand)
        assert abs(out.fed_target - expected_fed) < 1e-9

    def test_zero_netmenders_zero_fish(self):
        out = compute_chain({}, 20000, CHAINS)
        assert out.units.get("fish", 0.0) == 0.0
        assert out.raw == 0

    def test_toiling_netmenders(self):
        factions = mk_fish_city()
        baseline = compute_chain(factions, 20000, CHAINS).units["fish"]
        factions["netmenders"].toiling = True
        boosted = compute_chain(factions, 20000, CHAINS).units["fish"]
        assert boosted == baseline * TOIL_MULT

    def test_per_chain_conservation(self):
        out = compute_chain(mk_fish_city(), 20000, CHAINS)
        assert out.units["fish"] == out.raw   # fishery only → fish == its raw

    def test_netmenders_has_chain_role(self):
        assert "netmenders" in chain_role_faction_ids(CHAINS, mk_fish_city())
