"""
tests/test_removal.py — the terminal Mayor-removal resolution (fail-states_spec, slice 1).

Covers the countdown state machine (start → persist → elapse → game over), recovery, the debt
trigger, difficulty scaling of the grace window, the run_cycle integration, and serialization of
the new terminal state.
"""
from __future__ import annotations

from engine.balance import NORMAL, EASY, HARD
from engine.models import WorldState, Mayor, Treasury
from engine.special.removal import process_mayor_removal


def _has(results, action):
    return any(r.action == action for r in results)


# ── Countdown state machine ──────────────────────────────────────────────────────

def test_low_rep_starts_then_elapses_to_game_over():
    world = WorldState()
    mayor = Mayor()
    mayor.set_reputation("the_public", -40)   # at/below threshold

    # Cycle 1: starts the countdown at the grace value.
    r1 = process_mayor_removal(world, mayor, balance=NORMAL)
    assert mayor.removal_countdown == NORMAL.removal_grace_cycles
    assert _has(r1, "RemovalCountdown") and not world.game_over

    # Decrement across the grace window; game over on the cycle it hits zero.
    for _ in range(NORMAL.removal_grace_cycles - 1):
        process_mayor_removal(world, mayor, balance=NORMAL)
        assert not world.game_over
    final = process_mayor_removal(world, mayor, balance=NORMAL)
    assert world.game_over is True
    assert world.end_cause == "public_revolt"
    assert _has(final, "MayorRemoved")


def test_recovery_clears_countdown():
    world = WorldState()
    mayor = Mayor()
    mayor.set_reputation("the_public", -40)
    process_mayor_removal(world, mayor, balance=NORMAL)
    assert mayor.removal_countdown is not None

    # Mayor recovers above the threshold → countdown clears, no game over.
    mayor.set_reputation("the_public", 0)
    results = process_mayor_removal(world, mayor, balance=NORMAL)
    assert mayor.removal_countdown is None
    assert not world.game_over
    assert _has(results, "RemovalAverted")


def test_debt_trigger_cause():
    world = WorldState()
    mayor = Mayor()
    treasury = Treasury()
    treasury.debt = NORMAL.removal_threshold + 1
    for _ in range(NORMAL.removal_grace_cycles + 1):
        process_mayor_removal(world, mayor, treasury, balance=NORMAL)
    assert world.game_over is True
    assert world.end_cause == "removal_coalition"


def test_stable_mayor_never_in_jeopardy():
    world = WorldState()
    mayor = Mayor()
    mayor.set_reputation("the_public", 25)
    for _ in range(20):
        process_mayor_removal(world, mayor, balance=NORMAL)
    assert mayor.removal_countdown is None and not world.game_over


def test_grace_scales_with_difficulty():
    def cycles_to_fall(profile):
        world = WorldState(); mayor = Mayor(); mayor.set_reputation("the_public", -40)
        n = 0
        while not world.game_over and n < 50:
            process_mayor_removal(world, mayor, balance=profile)
            n += 1
        return n
    # Easy gives a longer grace window than hard.
    assert cycles_to_fall(EASY) > cycles_to_fall(HARD)


def test_game_over_latches():
    world = WorldState(game_over=True, end_cause="public_revolt")
    mayor = Mayor()
    mayor.set_reputation("the_public", 50)   # even a healthy mayor stays removed
    results = process_mayor_removal(world, mayor, balance=NORMAL)
    assert results == [] and world.game_over and world.end_cause == "public_revolt"


# ── run_cycle integration ────────────────────────────────────────────────────────

def test_run_cycle_ends_run_on_sustained_low_rep():
    from engine.cycle.runner import run_cycle
    from engine.models import ThePublic
    world = WorldState(chaos={})
    mayor = Mayor(); mayor.set_reputation("the_public", -45)
    treasury = Treasury()
    public = ThePublic()
    # Public processing re-syncs support from reputation, which stays at -45, so the
    # removal condition holds every cycle. Within grace+1 cycles the run must end.
    for _ in range(NORMAL.removal_grace_cycles + 1):
        run_cycle(world, {}, {}, mayor=mayor, treasury=treasury, public=public)
    assert world.game_over is True


# ── Serialization round-trip ─────────────────────────────────────────────────────

def test_terminal_state_survives_serialization():
    from serializer import (serialize_world_state, deserialize_world_state,
                            serialize_mayor, deserialize_mayor)
    world = WorldState(cycle=7, game_over=True, end_cause="removal_coalition")
    w2 = deserialize_world_state(serialize_world_state(world))
    assert w2.game_over is True and w2.end_cause == "removal_coalition"

    mayor = Mayor(); mayor.removal_countdown = 3
    m2 = deserialize_mayor(serialize_mayor(mayor))
    assert m2.removal_countdown == 3
