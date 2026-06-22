"""
tests/test_election.py — the recurring election verdict (elections_spec, slice 3a).

Covers the approval math (popular + rank-weighted faction vote), the cadence + campaign-warning
window, the win/lose verdict, loss → game over, difficulty cadence, and run_cycle integration.
"""
from __future__ import annotations

from dataclasses import replace
from engine.balance import NORMAL
from engine.models import WorldState, Mayor, ThePublic, Faction, Leader
from engine.special.election import (
    election_approval, cycles_until_election, process_election, election_summary,
)


def fac(fid, rating):
    return Faction(id=fid, name=fid.title(), domain_primary="trade",
                   leader=Leader(name=f"L-{fid}"), rating=rating)


def _has(results, action):
    return any(r.action == action for r in results)


# ── Approval math ────────────────────────────────────────────────────────────────

def test_approval_blends_public_and_factions():
    public = ThePublic(support=40)
    mayor = Mayor()
    factions = {"a": fac("a", 4.0), "b": fac("b", 2.0)}
    mayor.set_reputation("a", 10)
    mayor.set_reputation("b", -20)
    # influential = (10*4 + -20*2) / 6 = 0 ; public weight 0.5 → 0.5*40 + 0.5*0 = 20
    assert election_approval(public, factions, mayor, NORMAL) == 20.0


def test_approval_rank_weighting():
    public = ThePublic(support=0)
    mayor = Mayor()
    # The high-rank ally outweighs the low-rank foe.
    factions = {"big": fac("big", 9.0), "small": fac("small", 1.0)}
    mayor.set_reputation("big", 30)
    mayor.set_reputation("small", -30)
    assert election_approval(public, factions, mayor, NORMAL) > 0


# ── Cadence ──────────────────────────────────────────────────────────────────────

def test_cadence_modular():
    assert cycles_until_election(0, NORMAL) == NORMAL.election_interval  # fresh run — none at c0
    assert cycles_until_election(12, NORMAL) == 0     # election cycle
    assert cycles_until_election(10, NORMAL) == 2
    assert cycles_until_election(8, NORMAL) == 4
    assert cycles_until_election(1, NORMAL) == 11


def test_cadence_scales_with_difficulty():
    fast = replace(NORMAL, election_interval=6)
    assert cycles_until_election(6, fast) == 0
    assert cycles_until_election(4, fast) == 2


# ── Verdict ──────────────────────────────────────────────────────────────────────

def test_win_keeps_governing():
    world = WorldState(cycle=NORMAL.election_interval)   # an election cycle
    public = ThePublic(support=30)
    mayor = Mayor()
    results = process_election(world, public, {}, mayor, NORMAL)
    assert _has(results, "ElectionWon")
    assert world.game_over is False


def test_loss_ends_run():
    world = WorldState(cycle=NORMAL.election_interval)
    public = ThePublic(support=-30)
    mayor = Mayor()
    results = process_election(world, public, {}, mayor, NORMAL)
    assert _has(results, "ElectionLost")
    assert world.game_over is True and world.end_cause == "voted_out"


def test_campaign_warning_in_window():
    world = WorldState(cycle=NORMAL.election_interval - NORMAL.election_warn_window)  # exactly the window edge
    public = ThePublic(support=-10)
    mayor = Mayor()
    results = process_election(world, public, {}, mayor, NORMAL)
    assert _has(results, "ElectionWarning")
    assert not world.game_over


def test_no_warning_outside_window():
    world = WorldState(cycle=1)
    results = process_election(world, ThePublic(support=0), {}, Mayor(), NORMAL)
    assert results == []


# ── Summary readout ──────────────────────────────────────────────────────────────

def test_summary_none_without_mayor():
    assert election_summary(WorldState(cycle=3), ThePublic(), {}, None, NORMAL) is None


def test_summary_reports_next_and_approval():
    world = WorldState(cycle=10)
    s = election_summary(world, ThePublic(support=20), {}, Mayor(), NORMAL)
    assert s["next_in"] == 2 and s["approval"] == 10.0 and s["interval"] == 12


# ── run_cycle integration ────────────────────────────────────────────────────────

# ── Title ladder ─────────────────────────────────────────────────────────────────

def _election_now(support, rank, balance):
    world = WorldState(cycle=balance.election_interval)
    mayor = Mayor(); mayor.title_rank = rank
    results = process_election(world, ThePublic(support=support), {}, mayor, balance)
    return world, mayor, results


def test_win_climbs_the_ladder():
    world, mayor, results = _election_now(40, 0, NORMAL)
    assert mayor.title_rank == 1
    assert not world.game_over and _has(results, "ElectionWon")


def test_reaching_top_rung_is_victory():
    from engine.titles import TOP_RANK
    world, mayor, results = _election_now(40, TOP_RANK - 1, NORMAL)
    assert mayor.title_rank == TOP_RANK
    assert world.game_over is True and world.end_cause == "victory"


def test_loss_demotes_on_forgiving_profile():
    world, mayor, results = _election_now(-40, 2, NORMAL)   # NORMAL is non-terminal
    assert mayor.title_rank == 1
    assert not world.game_over and _has(results, "ElectionDemoted")


def test_loss_at_bottom_rung_is_game_over():
    world, mayor, results = _election_now(-40, 0, NORMAL)   # demoting below the floor
    assert world.game_over is True and world.end_cause == "voted_out"


def test_hard_loss_is_terminal_at_any_rank():
    from dataclasses import replace
    hard = replace(NORMAL, election_loss_is_terminal=True)
    world, mayor, results = _election_now(-40, 3, hard)
    assert world.game_over is True and world.end_cause == "voted_out"
    assert _has(results, "ElectionLost")


def test_title_rank_survives_serialization():
    from serializer import serialize_mayor, deserialize_mayor
    mayor = Mayor(); mayor.title_rank = 3
    assert deserialize_mayor(serialize_mayor(mayor)).title_rank == 3


def test_run_cycle_holds_election_and_can_end_run():
    from engine.cycle.runner import run_cycle
    world = WorldState(cycle=NORMAL.election_interval - 1, chaos={})
    mayor = Mayor(); mayor.set_reputation("the_public", -50)
    public = ThePublic(support=-50, population=20000)
    # Stepping into the election cycle with deep unpopularity → voted out.
    run_cycle(world, {}, {}, mayor=mayor, treasury=None, public=public, balance=NORMAL)
    assert world.game_over is True and world.end_cause == "voted_out"
