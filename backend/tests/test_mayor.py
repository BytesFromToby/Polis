"""Tests for Mayor and Treasury — actions, reputation, income, expenditure."""
import pytest
from engine.models import Mayor, Treasury, Faction, Domain, FactionTrait, Leader, MayorAction, WorldState, BaseProjectStack
from engine.mayor.treasury import (
    process_treasury_step0, apply_tax_effects,
    borrow_from_moneylender, invest_with_moneylender,
    spend_public_works, spend_emergency_guard_surge,
)
from engine.mayor.actions import execute_mayor_actions, apply_reputation_decay
from engine.cycle.runner import run_cycle


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_mayor(**kw):
    return Mayor(**kw)


def make_treasury(**kw):
    return Treasury(**kw)


def make_faction(fid="f1", domain="trade", rating=2.0, health=75, floor=None, **kw):
    # `floor` is accepted for back-compat; level now derives from rating (level = int(rating)).
    if floor is not None:
        rating = float(floor)
    kw.setdefault("leader", Leader(name="Test"))
    return Faction(id=fid, name=fid, domain_primary=domain, rating=rating,
                   health=health, **kw)


def make_domain(did="trade", cap=100):
    return Domain(id=did, name=did, cap=cap)


# ── Treasury ──────────────────────────────────────────────────────────────────

class TestTreasuryIncome:
    def test_income_added_to_gold(self):
        treasury = make_treasury(gold=100)
        mayor = make_mayor()
        factions = {"f1": make_faction(floor=2)}
        domains = {"trade": make_domain()}
        results = process_treasury_step0(treasury, mayor, factions, domains)
        # treasury_spec v3: income = flat base 20 (no Tax Offices); factions no longer tax.
        income_results = [r for r in results if r.action == "TaxIncome"]
        assert len(income_results) == 1
        assert treasury.income_this_cycle == 20

    def test_guard_payroll_deducted(self):
        treasury = make_treasury(gold=500)
        mayor = make_mayor()
        factions = {"f1": make_faction(floor=2)}
        domains = {"trade": make_domain()}
        process_treasury_step0(treasury, mayor, factions, domains)
        # Should have deducted 20 gold for guard payroll
        assert treasury.expenditure_this_cycle >= 20

    def test_guard_payroll_paid_from_base_income(self):
        # treasury_spec v3: base income (20) covers guard payroll (20), so a city
        # starting at 0 gold still pays the guard — it is not skipped.
        treasury = make_treasury(gold=0)
        mayor = make_mayor()
        results = process_treasury_step0(treasury, mayor, {}, {}, base_stacks={})
        skipped = [r for r in results if r.action == "GuardPayroll" and r.outcome == "fail"]
        assert len(skipped) == 0
        assert treasury.expenditure_this_cycle >= 20   # guard paid

    def test_debt_interest_applied(self):
        treasury = make_treasury(gold=500, debt=200, debt_rate=0.05)
        mayor = make_mayor()
        results = process_treasury_step0(treasury, mayor, {}, {})
        interest_results = [r for r in results if r.action == "DebtInterest"]
        assert len(interest_results) == 1

    def test_investment_matures(self):
        treasury = make_treasury(gold=100, invested=200, invest_cycles_remaining=1, invest_return_rate=1.10)
        mayor = make_mayor()
        results = process_treasury_step0(treasury, mayor, {}, {})
        mature = [r for r in results if r.action == "InvestmentMature"]
        assert len(mature) == 1
        assert treasury.invested == 0
        # v3: 100 start + 20 base income + 200*1.10=220 payout - 20 guard = 320
        assert treasury.gold == 320

    def test_cycle_totals_reset(self):
        treasury = make_treasury(gold=500)
        treasury.income_this_cycle = 999
        treasury.expenditure_this_cycle = 999
        mayor = make_mayor()
        process_treasury_step0(treasury, mayor, {}, {})
        assert treasury.income_this_cycle != 999  # was reset and refilled


class TestTaxEffects:
    def test_low_tax_boosts_public_rep(self):
        treasury = make_treasury()
        treasury.set_rate("trade", 0.00)
        mayor = make_mayor()
        domains = {"trade": make_domain("trade")}
        apply_tax_effects(treasury, mayor, {}, domains)
        assert mayor.get_reputation("the_public") == 1

    def test_elevated_tax_penalizes_public_rep(self):
        treasury = make_treasury()
        treasury.set_rate("trade", 0.30)
        mayor = make_mayor()
        domains = {"trade": make_domain("trade")}
        apply_tax_effects(treasury, mayor, {}, domains)
        assert mayor.get_reputation("the_public") == -1

    def test_punishing_tax_heavy_penalty(self):
        treasury = make_treasury()
        treasury.set_rate("trade", 0.50)
        mayor = make_mayor()
        domains = {"trade": make_domain("trade")}
        apply_tax_effects(treasury, mayor, {}, domains)
        assert mayor.get_reputation("the_public") == -5


class TestBorrowAndInvest:
    def test_borrow_adds_debt_and_gold(self):
        treasury = make_treasury(gold=100)
        result = borrow_from_moneylender(treasury, 100)
        assert result.outcome == "decisive"
        assert treasury.debt == 100
        assert treasury.gold == 200

    def test_borrow_caps_at_max_total(self):
        treasury = make_treasury(gold=100, debt=900)
        result = borrow_from_moneylender(treasury, 200)
        assert result.outcome == "decisive"
        assert treasury.debt == 1000

    def test_borrow_at_limit_fails(self):
        treasury = make_treasury(gold=100, debt=1000)
        result = borrow_from_moneylender(treasury, 100)
        assert result.outcome == "fail"

    def test_invest_locks_gold(self):
        treasury = make_treasury(gold=500)
        result = invest_with_moneylender(treasury, 200, 3)
        assert result.outcome == "decisive"
        assert treasury.invested == 200
        assert treasury.gold == 300

    def test_invest_invalid_term_fails(self):
        treasury = make_treasury(gold=500)
        result = invest_with_moneylender(treasury, 200, 4)
        assert result.outcome == "fail"

    def test_invest_insufficient_gold_fails(self):
        treasury = make_treasury(gold=50)
        result = invest_with_moneylender(treasury, 200, 3)
        assert result.outcome == "fail"


# ── Mayor ─────────────────────────────────────────────────────────────────────

class TestMayorReputation:
    def test_adjust_clamped_to_bounds(self):
        mayor = make_mayor()
        mayor.adjust_reputation("f1", 100)
        assert mayor.get_reputation("f1") == 50

    def test_adjust_negative_clamped(self):
        mayor = make_mayor()
        mayor.adjust_reputation("f1", -100)
        assert mayor.get_reputation("f1") == -50

    def test_reputation_label(self):
        mayor = make_mayor()
        mayor.set_reputation("f1", 35)
        assert mayor.reputation_label("f1") == "trusted"
        mayor.set_reputation("f1", -35)
        assert mayor.reputation_label("f1") == "hostile"

    def test_decay_moves_toward_band(self):
        from engine.balance import NORMAL
        b = NORMAL.reputation_decay_band
        mayor = make_mayor(reputation={"f1": b + 5, "f2": -(b + 5), "f3": 5})
        apply_reputation_decay(mayor)
        assert mayor.get_reputation("f1") == b + 4   # pulled one step toward the band
        assert mayor.get_reputation("f2") == -(b + 4)
        assert mayor.get_reputation("f3") == 5        # no decay inside the band

    def test_refill_caps_at_max(self):
        mayor = make_mayor(action_points=5, action_cap=6)
        mayor.refill()
        assert mayor.action_points == 6

    def test_spend_deducts_points(self):
        mayor = make_mayor(action_points=3)
        assert mayor.spend(2) is True
        assert mayor.action_points == 1

    def test_spend_fails_if_insufficient(self):
        mayor = make_mayor(action_points=1)
        assert mayor.spend(2) is False
        assert mayor.action_points == 1


class TestMayorActions:
    def setup_method(self):
        self.mayor = make_mayor(action_points=10)
        self.treasury = make_treasury(gold=500)
        self.factions = {
            "f1": make_faction("f1", "trade", floor=2),
            "f2": make_faction("f2", "trade", floor=2),
            "f3": make_faction("f3", "docks", floor=3),
        }
        self.domains = {
            "trade": make_domain("trade"),
            "docks": make_domain("docks"),
        }

    def test_meet_with_faction_grants_rep(self):
        results = execute_mayor_actions(
            [MayorAction(action="MeetWithFaction", target_id="f1")],
            self.mayor, self.treasury, self.factions, self.domains,
        )
        assert any(r.outcome == "decisive" for r in results)
        assert self.mayor.get_reputation("f1") == 5
        assert "f1" in self.mayor.cooldowns

    def test_meet_with_faction_cooldown_blocks_repeat(self):
        self.mayor.cooldowns["f1"] = 3
        results = execute_mayor_actions(
            [MayorAction(action="MeetWithFaction", target_id="f1")],
            self.mayor, self.treasury, self.factions, self.domains,
        )
        assert any(r.outcome == "fail" for r in results)

    def test_publicly_endorse_boosts_target_penalizes_peers(self):
        execute_mayor_actions(
            [MayorAction(action="PubliclyEndorse", target_id="f1")],
            self.mayor, self.treasury, self.factions, self.domains,
        )
        assert self.mayor.get_reputation("f1") == 10
        assert self.mayor.get_reputation("f2") == -3

    def test_publicly_condemn_hurts_target(self):
        execute_mayor_actions(
            [MayorAction(action="PubliclyCondemn", target_id="f1")],
            self.mayor, self.treasury, self.factions, self.domains,
        )
        assert self.mayor.get_reputation("f1") == -15

    def test_insufficient_action_points_fails(self):
        self.mayor.action_points = 0
        results = execute_mayor_actions(
            [MayorAction(action="MeetWithFaction", target_id="f1")],
            self.mayor, self.treasury, self.factions, self.domains,
        )
        assert any(r.outcome == "fail" for r in results)
        assert self.mayor.action_points == 0


# ── Cycle integration ─────────────────────────────────────────────────────────

class TestMayorCycleIntegration:
    def test_run_cycle_with_mayor_treasury(self):
        world = WorldState()
        factions = {"f1": make_faction("f1", "trade", floor=2)}
        domains = {"trade": make_domain("trade")}
        mayor = make_mayor(action_points=6)
        treasury = make_treasury(gold=500)
        result = run_cycle(world, factions, domains, mayor=mayor, treasury=treasury)
        assert result.cycle == 0
        assert world.cycle == 1

    def test_treasury_income_applied_each_cycle(self):
        world = WorldState()
        factions = {"f1": make_faction("f1", "trade", floor=2)}
        domains = {"trade": make_domain("trade")}
        mayor = make_mayor()
        treasury = make_treasury(gold=500)
        # v3: a Tax Office makes income (40) exceed guard payroll, so gold moves.
        base_stacks = {"civic": BaseProjectStack(name="Tax Office", domains=["civic"],
                                                 count=1, completed=True, progress=100.0)}
        run_cycle(world, factions, domains, mayor=mayor, treasury=treasury, base_stacks=base_stacks)
        assert treasury.gold != 500

    def test_mayor_refills_each_cycle(self):
        world = WorldState()
        factions = {}
        domains = {}
        mayor = make_mayor(action_points=0)
        treasury = make_treasury(gold=500)
        run_cycle(world, factions, domains, mayor=mayor, treasury=treasury)
        assert mayor.action_points == 1  # +1 per cycle

    def test_run_cycle_without_mayor_still_works(self):
        world = WorldState()
        factions = {"f1": make_faction("f1", "trade", floor=2)}
        domains = {"trade": make_domain("trade")}
        result = run_cycle(world, factions, domains)
        assert result.cycle == 0

    def test_treasury_runs_without_player_action(self):
        # The treasury system advances on its own (passive tax income / payroll /
        # maintenance) with no mayor action ever submitted — the economy breathes
        # even though the demo surfaces no treasury controls.
        world = WorldState()
        factions = {"f1": make_faction("f1", "trade", floor=2)}
        domains = {"trade": make_domain("trade")}
        mayor = make_mayor(action_points=6)
        treasury = make_treasury(gold=500)
        start_gold = treasury.gold
        # v3: a Tax Office gives net positive income so the economy visibly moves.
        base_stacks = {"civic": BaseProjectStack(name="Tax Office", domains=["civic"],
                                                 count=1, completed=True, progress=100.0)}
        for _ in range(3):
            run_cycle(world, factions, domains, mayor=mayor, treasury=treasury, base_stacks=base_stacks)
        assert treasury.gold != start_gold  # gold moved with no player treasury action
