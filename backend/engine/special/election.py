"""
engine/special/election.py — the recurring election verdict (elections_spec).

Every `election_interval` cycles the city judges the Mayor's tenure. The verdict is a legible
weighted sum of currencies that already exist — the Public's support (popular vote) and per-faction
Mayor reputation weighted by faction rank (the influential vote). A campaign warning carrying the
projected approval fires in the run-up so a loss is foreseen, not random.

Slice 3a: win → a fresh mandate (the run continues); lose → the run ends
(world.game_over, end_cause="voted_out"). The forgiving title-ladder demotion and the
"support me in the election" deal term are deferred follow-ups (see elections_spec.md).
"""
from __future__ import annotations
from typing import Dict, List, Optional, TYPE_CHECKING

from engine.models import ActionResult
from engine.balance import NORMAL as _BAL

if TYPE_CHECKING:
    from engine.models import WorldState, Mayor, Faction, ThePublic


def election_approval(
    public: Optional["ThePublic"],
    factions: Optional[Dict[str, "Faction"]],
    mayor: "Mayor",
    balance=_BAL,
) -> float:
    """Projected vote, −50..+50. Popular vote (Public support) blended with the rank-weighted
    average of per-faction Mayor reputation."""
    popular = float(public.support) if public is not None else 0.0

    influential = 0.0
    if factions:
        total_rank = sum(f.rating for f in factions.values())
        if total_rank > 0:
            influential = sum(mayor.get_reputation(f.id) * f.rating
                              for f in factions.values()) / total_rank

    w = balance.election_public_weight
    return w * popular + (1.0 - w) * influential


def cycles_until_election(cycle: int, balance=_BAL) -> int:
    """Cycles remaining until the next election; 0 means an election is held this cycle."""
    interval = balance.election_interval
    if interval <= 0:
        return 0
    return (interval - cycle % interval) % interval


def process_election(
    world: "WorldState",
    public: Optional["ThePublic"],
    factions: Optional[Dict[str, "Faction"]],
    mayor: "Mayor",
    balance=_BAL,
) -> List[ActionResult]:
    """Hold the vote on election cycles; otherwise emit the campaign warning in the run-up."""
    results: List[ActionResult] = []
    if world.game_over or world.cycle <= 0:
        return results

    until = cycles_until_election(world.cycle, balance)

    # Election cycle — render the verdict.
    if until == 0:
        approval = election_approval(public, factions, mayor, balance)
        if approval >= balance.election_pass_score:
            results.append(ActionResult(
                action="ElectionWon", actor_id="the_public", target_id="mayor",
                outcome="decisive", dramatic=True,
                narrative=(f"The Assembly returns the Mayor to office "
                           f"(approval {approval:+.0f}). A fresh mandate begins."),
            ))
        else:
            world.game_over = True
            world.end_cause = "voted_out"
            results.append(ActionResult(
                action="ElectionLost", actor_id="the_public", target_id="mayor",
                outcome="decisive", dramatic=True,
                narrative=(f"The Assembly votes the Mayor out (approval {approval:+.0f}). "
                           f"The reign ends at the ballot."),
            ))
        return results

    # Campaign window — warn, carrying the projected approval so the player can fight for it.
    if 1 <= until <= balance.election_warn_window:
        approval = election_approval(public, factions, mayor, balance)
        leaning = "favoured" if approval >= balance.election_pass_score else "in danger"
        results.append(ActionResult(
            action="ElectionWarning", actor_id="the_public", target_id="mayor",
            outcome="no_op", dramatic=True,
            narrative=(f"Election in {until} cycle(s). Projected approval {approval:+.0f} "
                       f"— the Mayor is {leaning}."),
        ))
    return results


def election_summary(
    world: "WorldState",
    public: Optional["ThePublic"],
    factions: Optional[Dict[str, "Faction"]],
    mayor: Optional["Mayor"],
    balance=_BAL,
) -> Optional[dict]:
    """Display block for the UI approval readout. None when there is no Mayor to judge."""
    if mayor is None:
        return None
    return {
        "interval": balance.election_interval,
        "next_in": cycles_until_election(world.cycle, balance),
        "approval": round(election_approval(public, factions, mayor, balance), 1),
        "pass_score": balance.election_pass_score,
    }
