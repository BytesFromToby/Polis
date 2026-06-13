"""Tests for engine/needs/chain.py — the harvest chain per public-needs_spec."""
import copy

from engine.models import Faction, Leader
from engine.needs.chain import (
    TOIL_MULT, PARITY_TARGET, POP_PER_SUPPLY_UNIT,
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


class TestLoader:
    def test_loads_one_chain(self):
        assert len(CHAINS) == 1
        assert CHAINS[0]["id"] == "harvest"

    def test_missing_file_returns_empty(self):
        assert load_chains("nonexistent/chains.json") == []


class TestChainRoles:
    def test_roles(self):
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
    def test_raw_is_three_per_aristocracy_level(self):
        factions = mk_city(aristo_ratings=(4.0, 3.0, 2.0))
        out = compute_chain(factions, 20000, CHAINS)
        assert out.raw == 3 * (4 + 3 + 2)

    def test_dead_estates(self):
        # No aristocracy factions at all → zero raw → nothing processed.
        factions = mk_city()
        for i in range(3):
            del factions[f"estate{i}"]
        out = compute_chain(factions, 20000, CHAINS)
        assert out.raw == 0
        assert all(v == 0 for v in out.units.values())
        assert out.fed_target == 0


class TestSplit:
    def test_under_capacity_proportional_no_leftover(self):
        # raw 9 (one level-3 estate), capacity 12+12 → proportional, no porridge
        factions = mk_city(aristo_ratings=(3.0,))
        out = compute_chain(factions, 20000, CHAINS)
        assert out.units["bread"] == 4.5
        assert out.units["wine"] == 4.5
        assert out.units["porridge"] == 0

    def test_over_capacity_full_caps_plus_porridge(self):
        # raw 27, capacity 24 → each takes 12, 3 porridge
        factions = mk_city()
        out = compute_chain(factions, 20000, CHAINS)
        assert out.units["bread"] == 12
        assert out.units["wine"] == 12
        assert out.units["porridge"] == 3

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
        assert out.raw == 27
        assert out.units["porridge"] == 27
        # fed_supply = 0.4 × raw, nonzero
        expected_fed = min(100.0, PARITY_TARGET * (0.4 * 27) / (20000 / POP_PER_SUPPLY_UNIT))
        assert abs(out.fed_target - expected_fed) < 1e-9
        assert out.fed_target > 0


class TestDrunkThreshold:
    def test_flips_across_the_boundary(self):
        # Standard city: wine units 12 → wine_happy 7.2. DRUNK_THRESHOLD 0.25
        # crosses between demand 28 (0.257 → drunk) and demand 30 (0.24 → sober).
        from engine.needs.chain import DRUNK_THRESHOLD
        factions = mk_city()
        assert compute_chain(factions, 28000, CHAINS).drunk
        assert not compute_chain(factions, 30000, CHAINS).drunk
        assert DRUNK_THRESHOLD == 0.25  # test geometry depends on it; fail loudly if tuned


class TestToil:
    def test_toiling_producer(self):
        factions = mk_city(aristo_ratings=(3.0,))
        baseline = compute_chain(factions, 20000, CHAINS)
        factions["estate0"].toiling = True
        boosted = compute_chain(factions, 20000, CHAINS)
        assert boosted.raw == baseline.raw * TOIL_MULT

    def test_toiling_processor(self):
        # Capacity ×1.5: ovenmen 12→18, total 30 ≥ raw 27 → proportional split
        factions = mk_city()
        factions["ovenmen"].toiling = True
        out = compute_chain(factions, 20000, CHAINS)
        assert abs(out.units["bread"] - 27 * (18 / 30)) < 1e-9
        assert out.units["bread"] > 12  # strictly more than the non-toiling share
        assert out.units["porridge"] == 0
