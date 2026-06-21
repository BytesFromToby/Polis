"""
tests/test_population_fail.py — population collapse + the latched warning (fail-states_spec, slice 2).

Covers the terminal collapse (gated by difficulty), the hysteresis warning (on ≤1500, off >1750),
the support drain while active, the run_cycle integration, and serialization of the latch.
"""
from __future__ import annotations

from engine.balance import NORMAL, EASY, HARD
from engine.models import WorldState, ThePublic, Mayor
from engine.special.removal import process_population


def _has(results, action):
    return any(r.action == action for r in results)


# ── Collapse (terminal) ──────────────────────────────────────────────────────────

def test_collapse_ends_run_on_normal():
    world = WorldState()
    public = ThePublic(population=NORMAL.pop_collapse)
    results = process_population(world, public, balance=NORMAL)
    assert world.game_over is True
    assert world.end_cause == "population_collapse"
    assert _has(results, "PopulationCollapse")


def test_easy_floors_but_never_dies():
    world = WorldState()
    public = ThePublic(population=EASY.pop_collapse)   # at the floor
    process_population(world, public, balance=EASY)
    assert world.game_over is False                    # easy: the floor is not lethal
    assert public.pop_warning is True                  # but the warning still fires


# ── Latched warning with hysteresis ──────────────────────────────────────────────

def test_warning_latches_on_below_threshold():
    world = WorldState()
    public = ThePublic(population=1400)
    results = process_population(world, public, balance=NORMAL)
    assert public.pop_warning is True
    assert _has(results, "PopulationWarning")


def test_warning_persists_in_hysteresis_band():
    """Between off-threshold and on-threshold (1500 < pop ≤ 1750) the warning stays latched."""
    world = WorldState()
    public = ThePublic(population=1400)
    process_population(world, public, balance=NORMAL)        # latch on
    public.population = 1700                                 # in the band — not yet recovered
    results = process_population(world, public, balance=NORMAL)
    assert public.pop_warning is True
    assert not _has(results, "PopulationRecovered")


def test_warning_clears_above_off_threshold():
    world = WorldState()
    public = ThePublic(population=1400)
    process_population(world, public, balance=NORMAL)        # latch on
    public.population = 1800                                 # above off-threshold
    results = process_population(world, public, balance=NORMAL)
    assert public.pop_warning is False
    assert _has(results, "PopulationRecovered")


def test_warning_drains_support_each_cycle():
    world = WorldState()
    public = ThePublic(population=1400)
    mayor = Mayor()
    mayor.set_reputation("the_public", 10)
    process_population(world, public, mayor, balance=NORMAL)   # latch + drain
    assert mayor.get_reputation("the_public") == 10 + NORMAL.pop_warn_support_drain


# ── run_cycle integration ────────────────────────────────────────────────────────

def test_run_cycle_collapses_low_population():
    from engine.cycle.runner import run_cycle
    world = WorldState(chaos={})
    public = ThePublic(population=NORMAL.pop_collapse)
    mayor = Mayor()
    run_cycle(world, {}, {}, mayor=mayor, treasury=None, public=public, balance=NORMAL)
    assert world.game_over is True and world.end_cause == "population_collapse"


# ── Serialization ────────────────────────────────────────────────────────────────

def test_pop_warning_survives_serialization():
    from serializer import serialize_the_public, deserialize_the_public
    public = ThePublic(population=1400, pop_warning=True)
    p2 = deserialize_the_public(serialize_the_public(public))
    assert p2.pop_warning is True
