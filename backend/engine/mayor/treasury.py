"""
Treasury processing — income, expenditure, tax effects, debt.
Called at Step 0 of each cycle.
"""
from typing import Dict, List
from engine.models import Treasury, Mayor, Faction, Domain, ActionResult
from engine.formulas import faction_weight


def process_treasury_step0(
    treasury: Treasury,
    mayor: Mayor,
    factions: Dict[str, Faction],
    domains: Dict[str, Domain],
    active_project_count: int = 0,
    guard_paid: bool = True,
    logger=None,
) -> List[ActionResult]:
    """Apply income and fixed expenditure. Returns list of ActionResults for logging."""
    results = []
    treasury.reset_cycle_totals()

    # ── Income ──────────────────────────────────────────────────────────────
    income = _calc_tax_income(factions, treasury, mayor)

    # Investment maturity
    if treasury.invest_cycles_remaining > 0:
        treasury.invest_cycles_remaining -= 1
        if treasury.invest_cycles_remaining == 0 and treasury.invested > 0:
            payout = int(treasury.invested * treasury.invest_return_rate)
            treasury.gold += payout
            treasury.income_this_cycle += payout
            results.append(ActionResult(
                action="InvestmentMature",
                actor_id="treasury",
                target_id=None,
                outcome="no_op",
                delta=float(payout),
                narrative=f"Investment matured: +{payout} gold",
            ))
            treasury.invested = 0
            treasury.invest_return_rate = 0.0

    treasury.gold += income
    treasury.income_this_cycle += income
    results.append(ActionResult(
        action="TaxIncome",
        actor_id="treasury",
        target_id=None,
        outcome="no_op",
        delta=float(income),
        narrative=f"Tax income: +{income} gold",
    ))

    # ── Debt interest ────────────────────────────────────────────────────────
    if treasury.debt > 0:
        rate = 0.10 if treasury.debt > 500 else treasury.debt_rate
        interest = max(1, int(treasury.debt * rate))
        if treasury.gold >= interest:
            treasury.gold -= interest
            treasury.expenditure_this_cycle += interest
        else:
            treasury.debt += interest  # can't pay — debt grows
        results.append(ActionResult(
            action="DebtInterest",
            actor_id="treasury",
            target_id="moneylender",
            outcome="no_op",
            delta=-float(interest),
            narrative=f"Debt interest: -{interest} gold (debt {treasury.debt})",
        ))

    # ── Fixed expenditure ────────────────────────────────────────────────────
    guard_cost = 20
    if treasury.gold >= guard_cost:
        treasury.gold -= guard_cost
        treasury.expenditure_this_cycle += guard_cost
        results.append(ActionResult(
            action="GuardPayroll",
            actor_id="treasury",
            target_id=None,
            outcome="no_op",
            delta=-float(guard_cost),
            narrative=f"Guard payroll: -{guard_cost} gold",
        ))
    else:
        results.append(ActionResult(
            action="GuardPayroll",
            actor_id="treasury",
            target_id=None,
            outcome="fail",
            delta=0.0,
            narrative="Guard payroll skipped — insufficient funds",
        ))

    maintenance = 2 * active_project_count
    if maintenance > 0:
        if treasury.gold >= maintenance:
            treasury.gold -= maintenance
            treasury.expenditure_this_cycle += maintenance
            results.append(ActionResult(
                action="ProjectMaintenance",
                actor_id="treasury",
                target_id=None,
                outcome="no_op",
                delta=-float(maintenance),
                narrative=f"Project maintenance: -{maintenance} gold ({active_project_count} projects)",
            ))
        else:
            results.append(ActionResult(
                action="ProjectMaintenance",
                actor_id="treasury",
                target_id=None,
                outcome="fail",
                delta=0.0,
                narrative="Project maintenance skipped — insufficient funds",
            ))

    if logger:
        logger.log_system(0, "TREASURY", "treasury",
                          f"income +{income}, expenditure -{guard_cost + maintenance}")

    return results


_PUBLIC_REP_BY_RATE = {
    0.00: +1,
    0.10: +1,
    0.20:  0,
    0.30: -1,
    0.40: -3,
    0.50: -5,
}


def apply_tax_effects(
    treasury: Treasury,
    mayor: Mayor,
    factions: Dict[str, Faction],
    domains: Dict[str, "Domain"] = None,
) -> List[ActionResult]:
    """Apply per-cycle reputation and faction effects from domain tax rates."""
    results = []

    # Aggregate public reputation delta across all domains
    domain_ids = list(domains.keys()) if domains else list(
        {f.domain_primary for f in factions.values()}
    )
    total_rep_delta = 0
    for domain_id in domain_ids:
        rate = treasury.get_rate(domain_id)
        total_rep_delta += _PUBLIC_REP_BY_RATE.get(rate, 0)

    if total_rep_delta != 0:
        mayor.adjust_reputation("the_public", total_rep_delta)

    results.append(ActionResult(
        action="TaxEffect",
        actor_id="treasury",
        target_id="the_public",
        outcome="no_op",
        delta=float(total_rep_delta),
        narrative=f"Tax effects applied across {len(domain_ids)} domains; public rep {total_rep_delta:+d}",
    ))

    # Reputation bonus for exempted factions
    for fid, cycles_left in mayor.exemptions.items():
        mayor.adjust_reputation(fid, +5)

    return results


def _calc_tax_income(
    factions: Dict[str, Faction],
    treasury: Treasury,
    mayor: Mayor,
) -> int:
    """Sum per-domain income, excluding exempt factions."""
    total = 0
    by_domain: Dict[str, list] = {}
    for f in factions.values():
        by_domain.setdefault(f.domain_primary, []).append(f)

    for domain_id, domain_factions in by_domain.items():
        rate = treasury.get_rate(domain_id)
        if rate == 0.0:
            continue
        weight = sum(
            faction_weight(f.level)
            for f in domain_factions
            if not mayor.is_exempt(f.id)
        )
        total += int(weight * rate * 10)
    return total


# ── Optional expenditure actions ─────────────────────────────────────────────

def spend_emergency_guard_surge(treasury: Treasury, mayor: Mayor) -> ActionResult:
    cost = 50
    if treasury.gold < cost:
        return ActionResult(
            action="EmergencyGuardSurge",
            actor_id="mayor",
            target_id=None,
            outcome="fail",
            narrative="Emergency guard surge: insufficient funds",
        )
    treasury.gold -= cost
    treasury.expenditure_this_cycle += cost
    return ActionResult(
        action="EmergencyGuardSurge",
        actor_id="mayor",
        target_id=None,
        outcome="decisive",
        delta=-float(cost),
        narrative=f"Emergency guard surge: -{cost} gold; city-wide chaos -1 this cycle",
    )


def spend_public_works(treasury: Treasury, mayor: Mayor) -> ActionResult:
    cost = 30
    if treasury.gold < cost:
        return ActionResult(
            action="PublicWorksAllocation",
            actor_id="mayor",
            target_id=None,
            outcome="fail",
            narrative="Public works: insufficient funds",
        )
    treasury.gold -= cost
    treasury.expenditure_this_cycle += cost
    mayor.adjust_reputation("the_public", +5)
    return ActionResult(
        action="PublicWorksAllocation",
        actor_id="mayor",
        target_id=None,
        outcome="decisive",
        delta=-float(cost),
        narrative=f"Public works allocation: -{cost} gold; Public reputation +5",
    )


def borrow_from_moneylender(treasury: Treasury, amount: int) -> ActionResult:
    max_per_cycle = 200
    max_total = 1000
    amount = min(amount, max_per_cycle)

    if treasury.debt + amount > max_total:
        amount = max_total - treasury.debt
    if amount <= 0:
        return ActionResult(
            action="Borrow",
            actor_id="mayor",
            target_id="moneylender",
            outcome="fail",
            narrative="Cannot borrow: at debt limit",
        )

    treasury.debt += amount
    treasury.gold += amount
    treasury.debt_rate = 0.05
    return ActionResult(
        action="Borrow",
        actor_id="mayor",
        target_id="moneylender",
        outcome="decisive",
        delta=float(amount),
        narrative=f"Borrowed {amount} gold from Moneylender (total debt: {treasury.debt})",
    )


def invest_with_moneylender(treasury: Treasury, amount: int, term: int) -> ActionResult:
    """term: 3, 6, or 12 cycles."""
    return_rates = {3: 1.10, 6: 1.25, 12: 1.50}
    if term not in return_rates:
        return ActionResult(
            action="Invest",
            actor_id="mayor",
            target_id="moneylender",
            outcome="fail",
            narrative=f"Invalid investment term: {term}",
        )
    if treasury.invested > 0:
        return ActionResult(
            action="Invest",
            actor_id="mayor",
            target_id="moneylender",
            outcome="fail",
            narrative="Already have an active investment",
        )
    if treasury.gold < amount:
        return ActionResult(
            action="Invest",
            actor_id="mayor",
            target_id="moneylender",
            outcome="fail",
            narrative="Insufficient gold to invest",
        )

    treasury.gold -= amount
    treasury.invested = amount
    treasury.invest_cycles_remaining = term
    treasury.invest_return_rate = return_rates[term]

    return ActionResult(
        action="Invest",
        actor_id="mayor",
        target_id="moneylender",
        outcome="decisive",
        delta=-float(amount),
        narrative=f"Invested {amount} gold for {term} cycles ({return_rates[term]:.0%} return)",
    )
