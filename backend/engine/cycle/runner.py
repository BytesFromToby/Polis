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
from ..formulas import faction_weight, stack_cap_contribution
from ..balance import NORMAL as _BAL
from ..events import process_world_chaos, process_active_events, roll_for_random_events
from .resolution import run_sequential_actions
from .end_of_cycle import run_end_of_cycle, run_leadership_events, run_break_sweep, tick_deals


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
    base_stacks: Optional[Dict[str, "BaseProjectStack"]] = None,
    active_events: Optional[List[GameEvent]] = None,
    event_deck: Optional[List[dict]] = None,
    public: Optional[ThePublic] = None,
    external_threats: Optional[List[ExternalThreat]] = None,
    chains: Optional[List[dict]] = None,
    logger=None,
    balance=_BAL,
) -> CycleResult:
    """Run one full simulation cycle. Returns CycleResult.

    `balance` is the active BalanceProfile (difficulty) — defaults to NORMAL so existing
    callers and tests are unchanged. Threaded into the per-cycle dial consumers below.
    """
    from ..mayor import process_treasury_step0, apply_tax_effects, execute_mayor_actions, apply_reputation_decay
    from ..projects import tick_projects, apply_project_effects
    from ..special import (process_the_public, process_moneylender, process_external_threats,
                           process_mayor_removal, process_population, process_election)
    from ..needs import compute_chain, apply_needs, chain_role_faction_ids

    chains = chains or []
    chain_roles = chain_role_faction_ids(chains, factions) if chains else set()

    cycle_num = world.cycle
    all_results: List[ActionResult] = []
    # Use the caller's projects dict directly so runtime-initiated base projects persist.
    if projects is None:
        projects = {}
    if base_stacks is None:
        base_stacks = {}

    # ── Step 0: Pre-cycle setup ───────────────────────────────────────────────

    # Recalculate domain utilization (Σ level) and re-derive cap
    # (base_cap frozen at load + Σ active base-project contribution).
    for domain_id, domain in domains.items():
        domain.utilization = sum(
            faction_weight(faction.level)
            for faction in factions.values()
            if faction.domain_primary == domain_id
        )
        if domain.utilization == 0:
            # Faction-less lane (civic): authored cap, no stack contribution (treasury_spec v3).
            domain.cap = domain.base_cap
        else:
            domain.cap = domain.base_cap + stack_cap_contribution(base_stacks.get(domain_id))

    # Treasury: income + fixed expenditure
    if treasury is not None and mayor is not None:
        # Active project count = completed base instances (per stack) + active tax_collection.
        n_active = sum(s.active_count() for s in base_stacks.values()) \
            + sum(1 for p in projects.values() if p.status == "active")
        treasury_results = process_treasury_step0(
            treasury, mayor, factions, domains,
            active_project_count=n_active, logger=logger,
            base_stacks=base_stacks, balance=balance,
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
        world, factions, domains, projects, cycle_num, logger, base_stacks=base_stacks,
        public=public, chain_roles=chain_roles, mayor=mayor,
    )
    all_results.extend(resolution_results)

    # Track per-faction cycle outcomes for trait evolution
    _track_cycle_outcomes(all_results, factions)

    # ── Steps 4–6: End-of-cycle, leadership, Break sweep ─────────────────────
    run_end_of_cycle(world, factions, domains, all_results, cycle_num, logger)
    run_leadership_events(factions, all_results, cycle_num, logger)
    run_break_sweep(factions, all_results, cycle_num, logger)
    # Tick active deals: decrement cycles_remaining, check compliance, expire (audience_spec).
    if mayor is not None:
        tick_deals(mayor, factions, all_results, cycle_num, logger=logger)

    # ── Item 5a: Active game event effects (events_spec) ──────────────────────
    # Applied BEFORE the needs step so a `withhold` event zeroes its target's chain
    # contribution this cycle (cycle-runner_spec — added with Withhold). New events are still
    # *rolled* after the needs step (below) so their band gates see this cycle's bands.
    if active_events:
        event_results = process_active_events(active_events, factions, domains, world, public=public)
        all_results.extend(event_results)
        # Remove resolved events
        active_events[:] = [e for e in active_events if e.status != "resolved"]

    # ── Item 5b: Public needs (public-needs_spec) ─────────────────────────────
    # Reads `toiling`/`withholding` flags (the latter just asserted by active events above).
    if public is not None:
        from ..needs.scales import production_efficiency
        needs_out = compute_chain(factions, public.population, chains,
                                  efficiency=production_efficiency(public, balance))
        guard_paid = treasury.guard_paid_this_cycle if treasury is not None else True
        all_results.extend(apply_needs(public, needs_out, factions=factions, mayor=mayor,
                                       guard_paid=guard_paid, balance=balance))

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

    # Roll for new random events (public enables need-gated templates)
    if event_deck and active_events is not None:
        new_events = roll_for_random_events(world, factions, domains, event_deck, public=public)
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
        ml_results = process_moneylender(treasury, mayor, factions, balance=balance)
        all_results.extend(ml_results)

    # The Public
    if public is not None and mayor is not None:
        pub_results = process_the_public(public, mayor, factions, all_results)
        all_results.extend(pub_results)

    # Terminal fail-state checks, after reputation/population have settled (fail-states_spec).
    # Population collapse first (it can latch game_over, which removal then sees as a no-op).
    if public is not None:
        all_results.extend(process_population(world, public, mayor, balance=balance))
    if mayor is not None:
        all_results.extend(process_mayor_removal(world, mayor, treasury, factions, balance=balance))
        # The election verdict — a scheduled judgment alongside the removal spiral.
        all_results.extend(process_election(world, public, factions, mayor, balance=balance))

    # Reset cycle-only Toil/Withhold flags after the needs step consumed them
    # (cycle-runner_spec — Cycle-Only State). An active withhold event re-asserts next cycle.
    for f in factions.values():
        f.toiling = False
        f.withholding = False

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


