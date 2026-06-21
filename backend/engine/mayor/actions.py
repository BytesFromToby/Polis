"""
Mayor action implementations.
Each function executes one mayor action and returns an ActionResult.
Callers (cycle runner) are responsible for spending action points before calling.
"""
from typing import Dict, List
from engine.models import Mayor, Treasury, Faction, Domain, MayorAction, ActionResult
from engine.balance import NORMAL as _BAL


# ── Dispatcher ───────────────────────────────────────────────────────────────

ACTION_COSTS = {
    "MeetWithFaction":      1,
    "PubliclyEndorse":      1,
    "PubliclyCondemn":      1,
    "Sabotage":             1,
    # Treasury actions (no action point cost — see treasury.py)
    "EmergencyGuardSurge":  0,
    "PublicWorksAllocation": 0,
}

MEET_COOLDOWN = _BAL.meet_cooldown  # cycles (tunable in engine/balance.py)
SABOTAGE_GOLD = _BAL.sabotage_gold  # gold cost of a Sabotage (tunable in engine/balance.py)


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


# ── Resource Actions ──────────────────────────────────────────────────────────

def _sabotage(
    ma: MayorAction, mayor: Mayor, treasury: Treasury,
    factions: Dict[str, Faction], domains: Dict[str, Domain],
) -> ActionResult:
    """Covertly undermine a faction. Guaranteed (no contest) but bounded so it can
    never single-handedly de-level or Break a target:
      - rating loses 50% of its fractional margin above the current integer level
        (3.50 -> 3.25); an integer-rating faction loses nothing, so a single
        Sabotage never crosses a level boundary.
      - health loses 50% of current (floored), so it never reaches 0.
    Costs 1 AP (spent by the dispatcher) + 50 gold. Level-1 factions are valid
    targets (no safe-floor guard). The action point is refunded if it can't land."""
    fid = ma.target_id
    target = factions.get(fid)
    if target is None:
        mayor.action_points += ACTION_COSTS["Sabotage"]  # refund — nothing happened
        return ActionResult(
            action="Sabotage", actor_id="mayor", target_id=fid,
            outcome="fail", narrative=f"Faction {fid} not found",
        )
    if treasury.gold < SABOTAGE_GOLD:
        mayor.action_points += ACTION_COSTS["Sabotage"]  # refund
        return ActionResult(
            action="Sabotage", actor_id="mayor", target_id=fid,
            outcome="fail",
            narrative=f"Sabotage failed: need {SABOTAGE_GOLD} gold, have {treasury.gold}",
        )
    treasury.gold -= SABOTAGE_GOLD
    treasury.expenditure_this_cycle += SABOTAGE_GOLD
    target.rating -= 0.50 * (target.rating - int(target.rating))
    target.health -= target.health // 2
    mayor.adjust_reputation(fid, -10)
    return ActionResult(
        action="Sabotage", actor_id="mayor", target_id=fid,
        outcome="decisive", delta=-float(SABOTAGE_GOLD), dramatic=True,
        narrative=(
            f"Mayor sabotaged {fid}: rating now {target.rating:.2f}, "
            f"health {target.health}; rep -10; treasury -{SABOTAGE_GOLD}"
        ),
    )


# ── Action map ────────────────────────────────────────────────────────────────

_ACTION_MAP = {
    "MeetWithFaction":      _meet_with_faction,
    "PubliclyEndorse":      _publicly_endorse,
    "PubliclyCondemn":      _publicly_condemn,
    "Sabotage":             _sabotage,
}
