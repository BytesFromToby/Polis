"""
tests/test_coup.py — the assassination / coup risk (fail-states_spec, slice 4).

Covers the plot trigger (Σ faction reputation < threshold), the per-cycle risk roll, City-Guard
protection, difficulty gating (easy off, hard harsher), and run_cycle integration.
"""
from __future__ import annotations

from dataclasses import replace
from engine.balance import NORMAL, EASY
from engine.models import WorldState, Mayor, Faction, Leader
from engine.special.removal import process_coup, faction_reputation_sum


class FakeRng:
    """Deterministic stand-in for random — always returns `value` from random()."""
    def __init__(self, value): self.value = value
    def random(self): return self.value


def fac(fid, rating=2.0):
    return Faction(id=fid, name=fid.title(), domain_primary="trade",
                   leader=Leader(name=f"L-{fid}"), rating=rating)


def _hostile(mayor, factions, each=-40):
    for f in factions.values():
        mayor.set_reputation(f.id, each)


def _has(results, action):
    return any(r.action == action for r in results)


# ── Plot trigger ─────────────────────────────────────────────────────────────────

def test_no_plot_when_houses_content():
    world, mayor = WorldState(), Mayor()
    factions = {"a": fac("a"), "b": fac("b")}
    mayor.set_reputation("a", 10); mayor.set_reputation("b", 10)
    assert process_coup(world, mayor, factions, NORMAL, rng=FakeRng(0.0)) == []


def test_plot_forms_below_threshold_and_can_strike():
    world, mayor = WorldState(), Mayor()
    factions = {"a": fac("a"), "b": fac("b")}
    _hostile(mayor, factions)                      # sum -80 < -60
    assert faction_reputation_sum(mayor, factions) == -80
    results = process_coup(world, mayor, factions, NORMAL, rng=FakeRng(0.0))  # roll succeeds
    assert world.game_over is True and world.end_cause == "assassinated"
    assert _has(results, "MayorAssassinated")


def test_plot_can_miss():
    world, mayor = WorldState(), Mayor()
    factions = {"a": fac("a"), "b": fac("b")}
    _hostile(mayor, factions)
    results = process_coup(world, mayor, factions, NORMAL, rng=FakeRng(0.99))  # roll fails
    assert world.game_over is False
    assert _has(results, "CoupPlot")


# ── City Guard protection ────────────────────────────────────────────────────────

def test_guard_lowers_the_chance():
    world, mayor = WorldState(), Mayor()
    # base_chance 0.15; a level-3 guard removes 3*0.05 = 0.15 → chance 0 → never strikes.
    factions = {"a": fac("a"), "b": fac("b"), "city-guard": fac("city-guard", rating=3.0)}
    _hostile(mayor, {"a": factions["a"], "b": factions["b"]})
    mayor.set_reputation("city-guard", -40)
    results = process_coup(world, mayor, factions, NORMAL, rng=FakeRng(0.0))
    assert world.game_over is False and _has(results, "CoupPlot")


# ── Difficulty gating ────────────────────────────────────────────────────────────

def test_easy_has_no_coup():
    world, mayor = WorldState(), Mayor()
    factions = {"a": fac("a"), "b": fac("b")}
    _hostile(mayor, factions)
    assert process_coup(world, mayor, factions, EASY, rng=FakeRng(0.0)) == []
    assert world.game_over is False


def test_hard_plots_sooner():
    hard_world, mayor = WorldState(), Mayor()
    factions = {"a": fac("a"), "b": fac("b")}
    for f in factions.values():
        mayor.set_reputation(f.id, -28)            # sum -56: past hard's -50, not normal's -60
    from engine.balance import HARD
    assert process_coup(hard_world, mayor, factions, HARD, rng=FakeRng(0.99)) != []
    assert process_coup(WorldState(), mayor, factions, NORMAL, rng=FakeRng(0.99)) == []


# ── run_cycle integration ────────────────────────────────────────────────────────

def test_run_cycle_assassination():
    from engine.cycle.runner import run_cycle
    world = WorldState(cycle=1, chaos={})
    mayor = Mayor()
    factions = {"a": fac("a"), "b": fac("b")}
    _hostile(mayor, factions)
    # No public/treasury so only the coup can end it; guaranteed strike via a 0-chance-beating roll.
    import engine.special.removal as removal
    orig = removal.random
    try:
        removal.random = FakeRng(0.0)
        run_cycle(world, factions, {}, mayor=mayor, balance=NORMAL)
    finally:
        removal.random = orig
    assert world.game_over is True and world.end_cause == "assassinated"
