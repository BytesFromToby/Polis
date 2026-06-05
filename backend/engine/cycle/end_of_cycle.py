"""
cycle/end_of_cycle.py — Steps 4–6: end-of-cycle updates, leadership events,
                         Break sweep (factions at 0 health Break; they never die).
"""
from __future__ import annotations
import random
import string
from typing import Dict, List, Optional

from ..models import Faction, Domain, WorldState, ActionResult, Leader, Mayor
from ..npc.behavior import evolve_traits
from ..formulas import faction_weight


# ── Step 4: End-of-Cycle Updates ─────────────────────────────────────────────

def run_end_of_cycle(
    world: WorldState,
    factions: Dict[str, Faction],
    domains: Dict[str, Domain],
    all_results: List[ActionResult],
    cycle_num: int,
    logger=None,
) -> None:
    """Steps 4–6 in place. Appends events to all_results."""

    # 4.1 Health decay
    for fid, faction in list(factions.items()):
        decay = -1
        old_h = faction.health
        faction.health = max(0, faction.health + decay)
        if logger and faction.health != old_h:
            logger.log_system(cycle_num, "HEALTH", fid,
                              f"HealthDecay: {old_h} → {faction.health} ({decay:+d})")

    # 4.2 Trait evolution — basic streak tracking
    for fid, faction in factions.items():
        grow_streak = getattr(faction, '_grow_streak', 0)
        protect_streak = getattr(faction, '_protect_streak', 0)
        hostile_drought = getattr(faction, '_hostile_drought', 0)
        was_harmed = getattr(faction, '_was_harmed_by', None)
        harm_landed = getattr(faction, '_harm_landed_on', None)
        evolve_traits(
            faction,
            was_harmed_by=was_harmed,
            harm_landed_on=harm_landed,
            grew_streak=grow_streak,
            protect_streak=protect_streak,
            hostile_drought=hostile_drought,
        )

    # 4.5 Leadership need tick (also done in step 0 — just decay here)
    # Step 0 already increments; this block is informational only.

    # 4.6 Reset cycle-only state
    for faction in factions.values():
        faction.reset_cycle_state()
        # Clear per-cycle trait evolution scratch state
        for attr in ('_was_harmed_by', '_harm_landed_on',
                     '_grow_streak', '_protect_streak', '_hostile_drought'):
            if hasattr(faction, attr):
                delattr(faction, attr)


# ── Step 5: Leadership Events ─────────────────────────────────────────────────

def run_leadership_events(
    factions: Dict[str, Faction],
    all_results: List[ActionResult],
    cycle_num: int,
    logger=None,
) -> None:
    """Step 5: Leader status decay and replacement."""
    for fid, faction in factions.items():
        leader = faction.leader
        weakened_cycles = getattr(faction, '_leader_weakened_cycles', 0)
        absent_cycles = getattr(faction, '_leader_absent_cycles', 0)

        if leader.status == "weakened":
            weakened_cycles += 1
            faction._leader_weakened_cycles = weakened_cycles
            if weakened_cycles >= 2:
                leader.status = "absent"
                faction._leader_weakened_cycles = 0
                narrative = f"{faction.name}'s leader {leader.name} is no longer able to lead."
                all_results.append(ActionResult(
                    "LeaderAbsent", fid, None, "success",
                    dramatic=True, narrative=narrative,
                ))
                if logger:
                    logger.log_dramatic(cycle_num, narrative)

        elif leader.status == "absent":
            absent_cycles += 1
            faction._leader_absent_cycles = absent_cycles
            if absent_cycles >= 3:
                _replace_leader(faction, all_results, cycle_num, logger)
                faction._leader_absent_cycles = 0
        else:
            faction._leader_weakened_cycles = 0


def _replace_leader(
    faction: Faction,
    all_results: List[ActionResult],
    cycle_num: int,
    logger=None,
) -> None:
    """Generate a new leader derived from faction traits."""
    trait_names = [t.trait for t in faction.traits if t.target_id is None]
    selected = random.sample(trait_names, min(2, len(trait_names)))
    new_name = _generate_leader_name()
    faction.leader = Leader(name=new_name, traits=selected, status="present")

    narrative = (f"{faction.name} finds new leadership. "
                 f"{new_name} steps forward to lead the faction.")
    all_results.append(ActionResult(
        "LeaderReplaced", faction.id, None, "success",
        dramatic=True, narrative=narrative,
    ))
    if logger:
        logger.log_dramatic(cycle_num, narrative)


def _generate_leader_name() -> str:
    first = ["Aldric", "Mara", "Corvus", "Sela", "Dorin", "Vex",
             "Thena", "Cael", "Brynn", "Orwen", "Lira", "Fenn"]
    last = ["Stone", "Vane", "Marsh", "Croft", "Holt", "Cross",
            "Ward", "Bell", "Dunn", "Falk", "Gray", "Reeve"]
    return f"{random.choice(first)} {random.choice(last)}"


# ── Step 6: Break Sweep ───────────────────────────────────────────────────────

def run_break_sweep(
    factions: Dict[str, Faction],
    all_results: List[ActionResult],
    cycle_num: int,
    logger=None,
) -> None:
    """Any faction at 0 health Breaks (it is never removed). Covers non-aggression
    sources of health-0 (decay, events); aggression-driven Breaks already fired
    inline during the action loop."""
    from .resolution import resolve_break
    for fid, faction in factions.items():
        if faction.health <= 0:
            brk = resolve_break(faction)
            all_results.append(brk)
            if logger and brk.narrative:
                logger.log_dramatic(cycle_num, brk.narrative)


# ── Deal Tick & Compliance ────────────────────────────────────────────────────

def tick_deals(
    mayor: Mayor,
    factions: Dict[str, Faction],
    all_results: List[ActionResult],
    cycle_num: int,
    db=None,
    logger=None,
) -> None:
    """
    Decrement deal cycles_remaining, check faction compliance, expire finished deals.
    Call once per cycle after action resolution.
    """
    from engine.models import Deal

    acted_this_cycle: Dict[str, str] = {
        r.actor_id: r.action for r in all_results if r.actor_id
    }

    for deal_id, deal in list(mayor.deals.items()):
        if deal.status not in ("active", "suspended"):
            continue

        faction = factions.get(deal.faction_id)

        # Compliance check for committed_action
        for term in deal.faction_terms:
            if term.type == "committed_action":
                actual_action = acted_this_cycle.get(deal.faction_id)
                complied = actual_action == term.action
                if not complied:
                    deal.suspension_streak += 1
                    deal.status = "suspended"
                    if logger:
                        logger.log_system(cycle_num, "DEAL", deal.faction_id,
                                          f"Deal {deal_id[:8]} suspended (non-compliance streak {deal.suspension_streak})")
                    if deal.suspension_streak >= 3:
                        deal.status = "fulfilled"
                        _clear_deal_effects(deal, faction, mayor)
                        if logger:
                            logger.log_system(cycle_num, "DEAL", deal.faction_id,
                                              f"Deal {deal_id[:8]} expired (3 suspension strikes)")
                else:
                    deal.suspension_streak = 0
                    deal.status = "active"
                break

        if deal.status in ("active",):
            deal.cycles_remaining -= 1
            if deal.cycles_remaining <= 0:
                deal.status = "fulfilled"
                _clear_deal_effects(deal, faction, mayor)
                if logger:
                    logger.log_system(cycle_num, "DEAL", deal.faction_id,
                                      f"Deal {deal_id[:8]} fulfilled")

        # Persist status change to DB
        if db is not None:
            try:
                from db.models import Deal as DBDeal
                row = db.query(DBDeal).filter(DBDeal.deal_id == deal_id).first()
                if row:
                    row.cycles_remaining = deal.cycles_remaining
                    row.status = deal.status
                    row.suspension_streak = deal.suspension_streak
                    db.flush()
            except Exception:
                pass


def _clear_deal_effects(deal, faction, mayor: Mayor) -> None:
    """Remove committed fields from faction and any deal-linked exemptions."""
    if faction and faction.committed_deal_id == deal.id:
        faction.committed_action = ""
        faction.committed_target = ""
        faction.committed_deal_id = ""
        faction.committed_abstain_action = ""
        faction.committed_abstain_target = ""

    # Remove exemption if it was granted as part of this deal
    for term in deal.mayor_terms:
        if term.type == "tax_exemption" and deal.faction_id in mayor.exemptions:
            del mayor.exemptions[deal.faction_id]


# ── Domain Jealousy ──────────────────────────────────────────────────────────

def apply_domain_jealousy(
    mayor: Mayor,
    factions: Dict[str, Faction],
    logger=None,
    cycle_num: int = 0,
) -> None:
    """
    Factions in the same domain as an exempt faction lose -3 rep/cycle with mayor.
    Call once per cycle after exemption ticking.
    """
    exempt_domains: set = set()
    for fid in mayor.exemptions:
        f = factions.get(fid)
        if f:
            exempt_domains.add(f.domain_primary)

    for fid, faction in factions.items():
        if mayor.is_exempt(fid):
            continue
        if faction.domain_primary in exempt_domains:
            mayor.adjust_reputation(fid, -3)
            if logger:
                logger.log_system(cycle_num, "REP", fid,
                                  f"DomainJealousy: -3 rep (domain {faction.domain_primary} has exempt faction)")
