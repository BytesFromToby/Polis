"""
Mayor action implementations.
Each function executes one mayor action and returns an ActionResult.
Callers (cycle runner) are responsible for spending action points before calling.
"""
import random
from typing import Dict, List, Optional
from engine.models import Mayor, Treasury, Faction, Domain, MayorAction, ActionResult
from engine.formulas import resolve_contest


# ── Dispatcher ───────────────────────────────────────────────────────────────

ACTION_COSTS = {
    "MeetWithFaction":      1,
    "PubliclyEndorse":      1,
    "PubliclyCondemn":      1,
    "BrokerADeal":          2,
    "AllocateBudget":       1,
    "WithholdResources":    1,
    "IssueADecree":         2,
    "AppointAnOfficial":    2,
    "TurnABlindEye":        1,
    "RequestAReport":       1,
    "PlantARumor":          1,
    # Treasury actions (no action point cost — see treasury.py)
    "EmergencyGuardSurge":  0,
    "PublicWorksAllocation": 0,
}

MEET_COOLDOWN = 10  # cycles


def execute_mayor_actions(
    mayor_actions: List[MayorAction],
    mayor: Mayor,
    treasury: Treasury,
    factions: Dict[str, Faction],
    domains: Dict[str, Domain],
    logger=None,
) -> List[ActionResult]:
    """Execute all mayor actions submitted for this cycle. Returns results."""
    results = []
    for ma in mayor_actions:
        fn = _ACTION_MAP.get(ma.action)
        if fn is None:
            continue
        cost = ACTION_COSTS.get(ma.action, ma.cost)
        if not mayor.spend(cost):
            results.append(ActionResult(
                action=ma.action,
                actor_id="mayor",
                target_id=ma.target_id or None,
                outcome="fail",
                narrative=f"Insufficient action points for {ma.action}",
            ))
            continue
        result = fn(ma, mayor, treasury, factions, domains)
        results.append(result)
        if logger:
            logger.log_system(0, "MAYOR", "mayor", result.narrative)
    return results


def apply_reputation_decay(mayor: Mayor) -> None:
    """Decay reputation toward 0 each cycle for inactive relationships."""
    for fid in list(mayor.reputation):
        score = mayor.reputation[fid]
        if score > 10:
            mayor.reputation[fid] = score - 1
        elif score < -10:
            mayor.reputation[fid] = score + 1


# ── Political Actions ─────────────────────────────────────────────────────────

def _meet_with_faction(
    ma: MayorAction, mayor: Mayor, treasury: Treasury,
    factions: Dict[str, Faction], domains: Dict[str, Domain],
) -> ActionResult:
    fid = ma.target_id
    if fid in mayor.cooldowns:
        return ActionResult(
            action="MeetWithFaction", actor_id="mayor", target_id=fid,
            outcome="fail",
            narrative=f"Cannot meet {fid}: on cooldown ({mayor.cooldowns[fid]} cycles)",
        )
    mayor.adjust_reputation(fid, +5)
    mayor.cooldowns[fid] = MEET_COOLDOWN
    return ActionResult(
        action="MeetWithFaction", actor_id="mayor", target_id=fid,
        outcome="decisive", delta=5.0,
        narrative=f"Mayor met with {fid}: reputation +5; {MEET_COOLDOWN}-cycle cooldown set",
    )


def _publicly_endorse(
    ma: MayorAction, mayor: Mayor, treasury: Treasury,
    factions: Dict[str, Faction], domains: Dict[str, Domain],
) -> ActionResult:
    fid = ma.target_id
    target = factions.get(fid)
    if target is None:
        return ActionResult(
            action="PubliclyEndorse", actor_id="mayor", target_id=fid,
            outcome="fail", narrative=f"Faction {fid} not found",
        )
    mayor.adjust_reputation(fid, +10)
    # Domain peers lose -3
    for f in factions.values():
        if f.id != fid and f.domain_primary == target.domain_primary:
            mayor.adjust_reputation(f.id, -3)
    # Public effect
    public_delta = +5 if target.health >= 50 else -5
    mayor.adjust_reputation("the_public", public_delta)
    return ActionResult(
        action="PubliclyEndorse", actor_id="mayor", target_id=fid,
        outcome="decisive", delta=10.0,
        narrative=f"Mayor endorsed {fid}: rep +10; domain peers -3; Public {public_delta:+}",
    )


def _publicly_condemn(
    ma: MayorAction, mayor: Mayor, treasury: Treasury,
    factions: Dict[str, Faction], domains: Dict[str, Domain],
) -> ActionResult:
    fid = ma.target_id
    target = factions.get(fid)
    if target is None:
        return ActionResult(
            action="PubliclyCondemn", actor_id="mayor", target_id=fid,
            outcome="fail", narrative=f"Faction {fid} not found",
        )
    mayor.adjust_reputation(fid, -15)
    # Domain peers gain +3
    for f in factions.values():
        if f.id != fid and f.domain_primary == target.domain_primary:
            mayor.adjust_reputation(f.id, +3)
    # Public effect: +5 if target is weak, neutral otherwise
    public_delta = +5 if target.health < 30 else 0
    if public_delta:
        mayor.adjust_reputation("the_public", public_delta)
    # Target adds 'angry at Mayor' (handled by trait evolution in behavior.py)
    return ActionResult(
        action="PubliclyCondemn", actor_id="mayor", target_id=fid,
        outcome="decisive", delta=-15.0,
        narrative=f"Mayor condemned {fid}: rep -15; domain peers +3; Public {public_delta:+}",
        dramatic=True,
    )


def _broker_a_deal(
    ma: MayorAction, mayor: Mayor, treasury: Treasury,
    factions: Dict[str, Faction], domains: Dict[str, Domain],
) -> ActionResult:
    parts = ma.target_id.split(",") if ma.target_id else []
    if len(parts) != 2:
        return ActionResult(
            action="BrokerADeal", actor_id="mayor", target_id=ma.target_id,
            outcome="fail", narrative="BrokerADeal requires target_id='factionA,factionB'",
        )
    a_id, b_id = parts[0].strip(), parts[1].strip()
    rep_a = mayor.get_reputation(a_id)
    rep_b = mayor.get_reputation(b_id)
    if rep_a < 10 or rep_b < 10:
        return ActionResult(
            action="BrokerADeal", actor_id="mayor", target_id=ma.target_id,
            outcome="fail",
            narrative=f"Broker failed: need rep >=10 with both factions (have {rep_a}/{rep_b})",
        )
    avg_rep = (rep_a + rep_b) // 2
    roll = random.randint(1, 20) + avg_rep
    dc = 15
    if roll >= dc:
        return ActionResult(
            action="BrokerADeal", actor_id="mayor", target_id=ma.target_id,
            outcome="decisive", delta=float(roll - dc),
            narrative=f"Broker deal success (roll {roll} vs DC {dc}): {a_id} and {b_id} gain trust",
            dramatic=True,
        )
    else:
        mayor.adjust_reputation(a_id, -5)
        mayor.adjust_reputation(b_id, -5)
        return ActionResult(
            action="BrokerADeal", actor_id="mayor", target_id=ma.target_id,
            outcome="fail", delta=float(roll - dc),
            narrative=f"Broker deal failed (roll {roll} vs DC {dc}): rep -5 with both factions",
        )


# ── Resource Actions ──────────────────────────────────────────────────────────

def _allocate_budget(
    ma: MayorAction, mayor: Mayor, treasury: Treasury,
    factions: Dict[str, Faction], domains: Dict[str, Domain],
) -> ActionResult:
    domain_id = ma.target_id
    if domain_id not in domains:
        return ActionResult(
            action="AllocateBudget", actor_id="mayor", target_id=domain_id,
            outcome="fail", narrative=f"Domain {domain_id} not found",
        )
    cost_gold = 10  # nominal; logged but not deducted here (treasury step handles fixed costs)
    if treasury.gold < cost_gold:
        return ActionResult(
            action="AllocateBudget", actor_id="mayor", target_id=domain_id,
            outcome="fail", narrative="Insufficient gold to allocate budget",
        )
    treasury.gold -= cost_gold
    treasury.expenditure_this_cycle += cost_gold
    domains[domain_id].drift = min(domains[domain_id].drift + 0.02, 1.0)
    for f in factions.values():
        if f.domain_primary == domain_id:
            mayor.adjust_reputation(f.id, +5)
    return ActionResult(
        action="AllocateBudget", actor_id="mayor", target_id=domain_id,
        outcome="decisive", delta=-float(cost_gold),
        narrative=f"Budget allocated to {domain_id}: drift +0.02; all domain factions rep +5",
    )


def _withhold_resources(
    ma: MayorAction, mayor: Mayor, treasury: Treasury,
    factions: Dict[str, Faction], domains: Dict[str, Domain],
) -> ActionResult:
    fid = ma.target_id
    if fid not in factions:
        return ActionResult(
            action="WithholdResources", actor_id="mayor", target_id=fid,
            outcome="fail", narrative=f"Faction {fid} not found",
        )
    # Mark faction as growth-blocked this cycle (runner checks this flag)
    factions[fid]._growth_blocked = True
    mayor.adjust_reputation(fid, -10)
    return ActionResult(
        action="WithholdResources", actor_id="mayor", target_id=fid,
        outcome="decisive", delta=-10.0,
        narrative=f"Resources withheld from {fid}: Grow blocked this cycle; rep -10",
    )


# ── Authority Actions ─────────────────────────────────────────────────────────

def _issue_a_decree(
    ma: MayorAction, mayor: Mayor, treasury: Treasury,
    factions: Dict[str, Faction], domains: Dict[str, Domain],
) -> ActionResult:
    domain_id = ma.target_id
    if domain_id not in domains:
        return ActionResult(
            action="IssueADecree", actor_id="mayor", target_id=domain_id,
            outcome="fail", narrative=f"Domain {domain_id} not found",
        )
    # Mark domain factions: compliant/resistant resolved in declaration
    domains[domain_id]._decree_active = True
    return ActionResult(
        action="IssueADecree", actor_id="mayor", target_id=domain_id,
        outcome="decisive",
        narrative=f"Decree issued for {domain_id}: factions must comply or resist",
        dramatic=True,
    )


def _appoint_an_official(
    ma: MayorAction, mayor: Mayor, treasury: Treasury,
    factions: Dict[str, Faction], domains: Dict[str, Domain],
) -> ActionResult:
    fid = ma.target_id
    faction = factions.get(fid)
    if faction is None:
        return ActionResult(
            action="AppointAnOfficial", actor_id="mayor", target_id=fid,
            outcome="fail", narrative=f"Faction {fid} not found",
        )
    if not faction.is_leaderless():
        return ActionResult(
            action="AppointAnOfficial", actor_id="mayor", target_id=fid,
            outcome="fail", narrative=f"{fid} already has a leader",
        )
    from engine.models import Leader
    faction.leader = Leader(name="Appointed Official", status="present", traits=["conservative"])
    mayor.adjust_reputation(fid, +15)
    for f in factions.values():
        if f.id != fid and f.domain_primary == faction.domain_primary:
            mayor.adjust_reputation(f.id, -5)
    return ActionResult(
        action="AppointAnOfficial", actor_id="mayor", target_id=fid,
        outcome="decisive", delta=15.0,
        narrative=f"Official appointed to {fid}: rep +15; domain peers -5",
        dramatic=True,
    )


def _turn_a_blind_eye(
    ma: MayorAction, mayor: Mayor, treasury: Treasury,
    factions: Dict[str, Faction], domains: Dict[str, Domain],
) -> ActionResult:
    fid = ma.target_id
    if fid not in factions:
        return ActionResult(
            action="TurnABlindEye", actor_id="mayor", target_id=fid,
            outcome="fail", narrative=f"Faction {fid} not found",
        )
    factions[fid]._uncontested = True
    mayor.adjust_reputation(fid, +10)
    mayor.adjust_reputation("the_public", -5)
    return ActionResult(
        action="TurnABlindEye", actor_id="mayor", target_id=fid,
        outcome="decisive", delta=10.0,
        narrative=f"Mayor turned blind eye to {fid}: action uncontested; Public -5",
    )


# ── Information Actions ───────────────────────────────────────────────────────

def _request_a_report(
    ma: MayorAction, mayor: Mayor, treasury: Treasury,
    factions: Dict[str, Faction], domains: Dict[str, Domain],
) -> ActionResult:
    fid = ma.target_id
    faction = factions.get(fid)
    if faction is None:
        return ActionResult(
            action="RequestAReport", actor_id="mayor", target_id=fid,
            outcome="fail", narrative=f"Faction {fid} not found",
        )
    traits_str = ", ".join(f"{t.trait}({t.intensity})" for t in faction.traits) or "none"
    return ActionResult(
        action="RequestAReport", actor_id="mayor", target_id=fid,
        outcome="no_op",
        narrative=f"Report on {fid}: traits=[{traits_str}] health={faction.health} rating={faction.rating:.2f}",
    )


def _plant_a_rumor(
    ma: MayorAction, mayor: Mayor, treasury: Treasury,
    factions: Dict[str, Faction], domains: Dict[str, Domain],
) -> ActionResult:
    # target_id format: "target_faction,about_faction"
    parts = ma.target_id.split(",") if ma.target_id else []
    if len(parts) != 2:
        return ActionResult(
            action="PlantARumor", actor_id="mayor", target_id=ma.target_id,
            outcome="fail", narrative="PlantARumor requires target_id='target_faction,about_faction'",
        )
    target_id, about_id = parts[0].strip(), parts[1].strip()
    target = factions.get(target_id)
    if target is None:
        return ActionResult(
            action="PlantARumor", actor_id="mayor", target_id=ma.target_id,
            outcome="fail", narrative=f"Target faction {target_id} not found",
        )
    from engine.models import FactionTrait
    from engine.npc.behavior import MAX_TRAITS, INTENSITY_ORDER
    existing = target.get_relational_trait("distrusts", about_id)
    if existing is None:
        if len(target.traits) >= MAX_TRAITS:
            target.traits.sort(key=lambda t: INTENSITY_ORDER.index(t.intensity))
            target.traits.pop(0)
        target.traits.append(FactionTrait(trait="distrusts", intensity="slight", target_id=about_id))
    else:
        idx = INTENSITY_ORDER.index(existing.intensity)
        if idx < len(INTENSITY_ORDER) - 1:
            existing.intensity = INTENSITY_ORDER[idx + 1]
    return ActionResult(
        action="PlantARumor", actor_id="mayor", target_id=ma.target_id,
        outcome="decisive",
        narrative=f"Rumor planted: {target_id} now distrusts {about_id} (3-cycle effect)",
    )


# ── Action map ────────────────────────────────────────────────────────────────

_ACTION_MAP = {
    "MeetWithFaction":      _meet_with_faction,
    "PubliclyEndorse":      _publicly_endorse,
    "PubliclyCondemn":      _publicly_condemn,
    "BrokerADeal":          _broker_a_deal,
    "AllocateBudget":       _allocate_budget,
    "WithholdResources":    _withhold_resources,
    "IssueADecree":         _issue_a_decree,
    "AppointAnOfficial":    _appoint_an_official,
    "TurnABlindEye":        _turn_a_blind_eye,
    "RequestAReport":       _request_a_report,
    "PlantARumor":          _plant_a_rumor,
}
