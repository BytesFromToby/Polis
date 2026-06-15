"""Dynamics suite — long-run behavior of the needs loop (public-needs_spec — Cycle integration).

Fixed seeds; constants imported, never copied. These four tests are the tuning
regression net: stability, legibility, recoverability, Toil matters.
"""
import os
import random

from engine.cycle.runner import run_cycle
from engine.models import Mayor, ThePublic, Treasury
from engine.needs.bands import FED_BANDS, band_index, fed_band
from loaders import load_state_from_json, load_chains

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CHAINS = load_chains()
ARISTOCRACY = ("eumelidai", "pyrrhidai", "skiadai")


def run_city(cycles, seed, mutate=None):
    """Run the standard city headless; mutate(factions, cycle) hooks each cycle.
    Returns the per-cycle fed trajectory."""
    random.seed(seed)
    world, factions, domains = load_state_from_json(DATA_DIR)
    public = ThePublic()
    fed_history = []
    for c in range(cycles):
        if mutate:
            mutate(factions, c)
        run_cycle(world, factions, domains, mayor=Mayor(), treasury=Treasury(),
                  public=public, chains=CHAINS)
        fed_history.append(public.fed)
    return fed_history


def band_i(value):
    return band_index(fed_band(value), FED_BANDS)


class TestStability:
    def test_balanced_city_does_not_starve(self):
        fed = run_city(60, seed=101)
        hungry_or_better = sum(1 for v in fed if band_i(v) >= 1)
        assert hungry_or_better >= 50


class TestLegibilityAndRecovery:
    def test_shortage_visible_within_5_recovery_within_15(self):
        # Two-source world: a one-time halve regrows + fish cushions, so it no longer
        # registers — the shortage must be a real *sustained* cut to be legible. Pin the
        # estates at 1.0 for cycles 10–19 (same pattern as Toil-matters), restore at 20.
        baseline = run_city(10, seed=202)
        start_band = band_i(baseline[9])
        originals = {}

        def mutate(factions, c):
            if 10 <= c < 20:
                for fid in ARISTOCRACY:
                    if c == 10:
                        originals[fid] = factions[fid].rating
                    factions[fid].rating = 1.0
            if c == 20:
                for fid, r in originals.items():
                    factions[fid].rating = r

        fed = run_city(40, seed=202, mutate=mutate)
        # Legibility: band at least one step lower within 5 cycles of the cut
        assert min(band_i(v) for v in fed[10:15]) <= start_band - 1
        # Recoverability: back to the starting band within 15 cycles of restoration
        assert any(band_i(v) >= start_band for v in fed[20:35])


class TestRedundancy:
    """Source redundancy (fish slice): one source out → Hungry not Starving; both → Starving.
    Removal = drop the producer factions (a faction's level can't be zeroed; rating floors at 1)."""

    def _run_without(self, remove_ids, cycles=30, seed=404):
        def mutate(factions, c):
            if c == 0:
                for fid in remove_ids:
                    factions.pop(fid, None)
        return run_city(cycles, seed, mutate=mutate)

    def test_both_sources_fed_or_better(self):
        fed = self._run_without(())
        assert min(band_i(v) for v in fed[-10:]) >= band_index("Fed", FED_BANDS)

    def test_barley_gone_hungry_never_starving(self):
        fed = self._run_without(ARISTOCRACY)
        assert all(band_i(v) >= band_index("Hungry", FED_BANDS) for v in fed)  # never Starving
        assert band_i(fed[-1]) == band_index("Hungry", FED_BANDS)              # settles Hungry

    def test_fish_gone_hungry_never_starving(self):
        fed = self._run_without(("netmenders",))
        assert all(band_i(v) >= band_index("Hungry", FED_BANDS) for v in fed)  # never Starving
        assert band_i(fed[-1]) == band_index("Hungry", FED_BANDS)              # settles Hungry

    def test_both_gone_starving(self):
        fed = self._run_without(ARISTOCRACY + ("netmenders",))
        assert band_i(fed[-1]) == band_index("Starving", FED_BANDS)


class TestToilMatters:
    def test_estate_toil_shallows_the_trough(self):
        """Committed Toil vs committed Protect under a sustained pinned shortage.

        The control must also be committed: an uncommitted hungry estate often
        Toils voluntarily (the prosocial shortage weight — by design), which
        erases the deal's marginal value and muddies the A/B."""
        def make_mutate(action):
            def mutate(factions, c):
                if 10 <= c < 20:
                    for fid in ARISTOCRACY:
                        factions[fid].rating = 1.0           # pinned shortage window
                        factions[fid].committed_action = action
                elif c == 20:
                    for fid in ARISTOCRACY:
                        factions[fid].committed_action = ""
            return mutate

        control = run_city(30, seed=303, mutate=make_mutate("Protect"))
        toiled = run_city(30, seed=303, mutate=make_mutate("Toil"))
        assert min(toiled[10:25]) > min(control[10:25])
