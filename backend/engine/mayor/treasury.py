"""
Treasury processing — income, expenditure, tax effects, debt.
Called at Step 0 of each cycle.
"""
import random
from typing import Dict, List, Optional
from engine.models import Treasury, Mayor, Faction, Domain, ActionResult, BaseProjectStack
from engine.formulas import BASE_INCOME, TAX_OFFICE_INCOME
from engine.balance import NORMAL as _BAL


def process_treasury_step0(
    treasury: Treasury,
    mayor: Mayor,
    factions: Dict[str, Faction],
    domains: Dict[str, Domain],
    active_project_count: int = 0,
    guard_paid: bool = True,
    logger=None,
    base_stacks: Optional[Dict[str, BaseProjectStack]] = None,
    rng: Optional[random.Random] = None,
    balance=_BAL,
) -> List[ActionResult]:
    """Apply income and fixed expenditure. Returns list of ActionResults for logging."""
    results = []
    treasury.reset_cycle_totals()

    # ── Income ──────────────────────────────────────────────────────────────
    income = _calc_income(base_stacks, balance)

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

    # ── Fixed expenditure (guard payroll + maintenance) ──────────────────────
    # treasury_spec v3: charge in full, pay what gold allows, clamp at 0. Any
    # shortfall is settled as infrastructure damage (Insolvency, below).
    guard_cost = 20
    maintenance = 2 * active_project_count
    required = guard_cost + maintenance

    paid = min(treasury.gold, required)
    treasury.gold -= paid
    treasury.expenditure_this_cycle += paid
    # The Guard is paid this cycle only if the full guard payroll cleared (unrest lever reads this).
    treasury.guard_paid_this_cycle = (paid >= guard_cost)

    results.append(ActionResult(
        action="GuardPayroll", actor_id="treasury", target_id=None,
        outcome="no_op", delta=-float(guard_cost),
        narrative=f"Guard payroll: -{guard_cost} gold",
    ))
    if maintenance > 0:
        results.append(ActionResult(
            action="ProjectMaintenance", actor_id="treasury", target_id=None,
            outcome="no_op", delta=-float(maintenance),
            narrative=f"Project maintenance: -{maintenance} gold ({active_project_count} projects)",
        ))

    # ── Insolvency: clamp at 0, pay the shortfall in infrastructure damage ────
    shortfall = required - paid
    if shortfall > 0:
        treasury.gold = 0
        destroyed = _apply_insolvency_damage(base_stacks, shortfall, rng)
        results.append(ActionResult(
            action="Insolvency", actor_id="treasury", target_id=None,
            outcome="no_op", delta=-float(shortfall),
            narrative=(f"Treasury insolvent: {shortfall} gold shortfall paid in "
                       f"infrastructure damage ({destroyed} destroyed)"),
        ))

    if logger:
        logger.log_system(0, "TREASURY", "treasury",
                          f"income +{income}, expenditure -{paid}")

    return results


def _apply_insolvency_damage(base_stacks, shortfall, rng=None) -> int:
    """Spend an insolvency shortfall as ~1:1 health damage on random NON-civic base
    stacks (treasury_spec v3). Tax Offices (civic) are never damaged. Reducing/destroying
    maintenance-costing projects lowers next cycle's upkeep — self-balancing. Returns the
    number of instances destroyed."""
    from engine.projects.processing import apply_sabotage_damage
    r = rng or random
    stacks = base_stacks or {}
    remaining = float(shortfall)
    destroyed = 0
    guard = 0
    while remaining > 0 and guard < 10000:
        guard += 1
        damageable = [s for did, s in stacks.items() if did != "civic" and s.count > 0]
        if not damageable:
            break
        s = r.choice(damageable)
        before = s.count
        if s.progress <= 0:
            apply_sabotage_damage(s, 0)   # a hit at 0 health destroys the top
            remaining -= 1
        else:
            hit = min(remaining, s.progress)
            apply_sabotage_damage(s, hit)
            remaining -= hit
        if s.count < before:
            destroyed += 1
    return destroyed


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


def _calc_income(base_stacks: Optional[Dict[str, BaseProjectStack]], balance=_BAL) -> int:
    """Income (treasury_spec v3): flat base + per completed civic Tax Office.
    The per-domain auto-tax is removed — income depends only on base + Tax Offices."""
    civic = (base_stacks or {}).get("civic")
    office_count = civic.active_count() if civic is not None else 0
    return balance.base_income + balance.tax_office_income * office_count


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
