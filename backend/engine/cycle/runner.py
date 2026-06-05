"""
cycle/runner.py — run_cycle() orchestrator (v4, sequential initiative).

Steps 0–4 per cycle-runner_spec v1:
  0: Treasury
  1+2: Sequential initiative action loop (in resolution.py)
  3: Project ticks
  4: End of cycle, leadership, Break sweep, chaos, counters
"""
from __future__ import annotations
from typing import Dict, List, Optional

from ..models import (
    Faction, Domain, WorldState, ActionResult, CycleResult, CycleEvent,
    Mayor, Treasury, MayorAction, Project, GameEvent, ThePublic, ExternalThreat,
)
from ..formulas import faction_weight
from ..events import process_world_chaos, process_active_events, roll_for_random_events
from .resolution import run_sequential_actions
from .end_of_cycle import run_end_of_cycle, run_leadership_events, run_break_sweep


# ── CycleEvent Conversion ─────────────────────────────────────────────────────

def _to_cycle_event(result: ActionResult, cycle: int) -> CycleEvent:
    dramatic = 0
    if result.dramatic:
        if result.outcome == "decisive":
            dramatic = 3
        elif result.outcome in ("partial", "success"):
            dramatic = 2
        else:
            dramatic = 1
    return CycleEvent(
        cycle=cycle,
        actor_id=result.actor_id,
        action=result.action,
        target_id=result.target_id,
        domain=result.domain,
        narrative=result.narrative,
        dramatic=dramatic,
    )


# ── Main Cycle Runner ─────────────────────────────────────────────────────────

def run_cycle(
    world: WorldState,
    factions: Dict[str, Faction],
    domains: Dict[str, Domain],
    mayor: Optional[Mayor] = None,
    treasury: Optional[Treasury] = None,
    mayor_actions: Optional[List[MayorAction]] = None,
    projects: Optional[Dict[str, Project]] = None,
    active_events: Optional[List[GameEvent]] = None,
    event_deck: Optional[List[dict]] = None,
    public: Optional[ThePublic] = None,
    external_threats: Optional[List[ExternalThreat]] = None,
    logger=None,
) -> CycleResult:
    """Run one full simulation cycle. Returns CycleResult."""
    from ..mayor import process_treasury_step0, apply_tax_effects, execute_mayor_actions, apply_reputation_decay
    from ..projects import tick_projects, apply_project_effects
    from ..special import process_the_public, process_moneylender, process_external_threats

    cycle_num = world.cycle
    all_results: List[ActionResult] = []

    # ── Step 0: Pre-cycle setup ───────────────────────────────────────────────

    # Recalculate domain utilization (Σ level)
    for domain_id, domain in domains.items():
        domain.utilization = sum(
            faction_weight(faction.level)
            for faction in factions.values()
            if faction.domain_primary == domain_id
        )

    # Treasury: income + fixed expenditure
    if treasury is not None and mayor is not None:
        n_active = sum(1 for p in (projects or {}).values() if p.status == "active")
        treasury_results = process_treasury_step0(
            treasury, mayor, factions, domains,
            active_project_count=n_active, logger=logger,
        )
        all_results.extend(treasury_results)
        all_results.extend(apply_tax_effects(treasury, mayor, factions))

    # External threats (before mayor actions so their effects are visible)
    if external_threats and treasury is not None and mayor is not None:
        all_results.extend(
            process_external_threats(external_threats, factions, domains, world, treasury, mayor)
        )

    # Mayor actions (submitted by player before this cycle)
    if mayor is not None and mayor_actions:
        mayor_results = execute_mayor_actions(
            mayor_actions, mayor, treasury, factions, domains, logger=logger,
        )
        all_results.extend(mayor_results)

    # ── Steps 1–2: Sequential initiative action loop ─────────────────────────
    resolution_results = run_sequential_actions(
        world, factions, domains, projects or {}, cycle_num, logger
    )
    all_results.extend(resolution_results)

    # Track per-faction cycle outcomes for trait evolution
    _track_cycle_outcomes(all_results, factions)

    # ── Steps 4–6: End-of-cycle, leadership, Break sweep ─────────────────────
    run_end_of_cycle(world, factions, domains, all_results, cycle_num, logger)
    run_leadership_events(factions, all_results, cycle_num, logger)
    run_break_sweep(factions, all_results, cycle_num, logger)

    # ── Step 8: Active game events ────────────────────────────────────────────
    if active_events:
        event_results = process_active_events(active_events, factions, domains, world)
        all_results.extend(event_results)
        # Remove resolved events
        active_events[:] = [e for e in active_events if e.status != "resolved"]

    # ── Step 4–6 already ran above ────────────────────────────────────────────
    # Project ticking (health, construction, effects)
    if projects and treasury is not None:
        proj_results = tick_projects(projects, factions, domains, treasury, logger)
        all_results.extend(proj_results)
        if mayor is not None:
            apply_project_effects(projects, factions, domains, treasury, mayor.reputation)

    # ── Step 8: World chaos ───────────────────────────────────────────────────
    chaos_results = process_world_chaos(world, factions, domains)
    for r in chaos_results:
        all_results.append(r)
        if logger and r.dramatic and r.narrative:
            logger.log_dramatic(cycle_num, r.narrative)

    # Roll for new random events
    if event_deck and active_events is not None:
        new_events = roll_for_random_events(world, factions, domains, event_deck)
        active_events.extend(new_events)

    # ── Step 9: Increment cycle + Mayor end-of-cycle ─────────────────────────
    world.cycle += 1
    if mayor is not None:
        mayor.refill()
        mayor.tick_cooldowns()
        mayor.tick_exemptions()
        mayor.tick_commitments()
        apply_reputation_decay(mayor)

    # Moneylender processing
    if treasury is not None and mayor is not None:
        ml_results = process_moneylender(treasury, mayor, factions)
        all_results.extend(ml_results)

    # The Public
    if public is not None and mayor is not None:
        pub_results = process_the_public(public, mayor, factions, all_results)
        all_results.extend(pub_results)

    # ── Build CycleResult ─────────────────────────────────────────────────────
    cycle_events = [_to_cycle_event(r, cycle_num) for r in all_results]
    faction_action_count = sum(
        1 for r in all_results
        if r.actor_id in factions and r.action not in ("Skip",)
    )

    return CycleResult(
        cycle=cycle_num,
        events=cycle_events,
        faction_actions=faction_action_count,
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _track_cycle_outcomes(
    results: List[ActionResult],
    factions: Dict[str, Faction],
) -> None:
    """Tag factions with scratch state used by trait evolution in end_of_cycle."""
    # Track harm events
    for r in results:
        if r.action == "Harm" and r.outcome in ("decisive", "partial"):
            attacker = factions.get(r.actor_id)
            defender = factions.get(r.target_id or "")
            if attacker:
                attacker._harm_landed_on = r.target_id
            if defender:
                defender._was_harmed_by = r.actor_id

    # Track action streaks from resolved results
    acted: Dict[str, str] = {}  # faction_id -> action taken this cycle
    for r in results:
        if r.actor_id in factions and r.action not in ("Break",):
            acted[r.actor_id] = r.action

    for fid, faction in factions.items():
        action = acted.get(fid)
        if action == "Grow":
            faction._grow_streak = getattr(faction, '_grow_streak', 0) + 1
            faction._protect_streak = 0
        elif action == "Protect":
            faction._protect_streak = getattr(faction, '_protect_streak', 0) + 1
            faction._grow_streak = 0
        elif action is not None:
            faction._grow_streak = 0
            faction._protect_streak = 0

        hostile = action in ("Harm", "Steal", "SabotageProject")
        if not hostile:
            faction._hostile_drought = getattr(faction, '_hostile_drought', 0) + 1
        else:
            faction._hostile_drought = 0


