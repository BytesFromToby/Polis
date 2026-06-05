"""
test_formulas.py — Tests for v3 formula functions.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from engine.formulas import (
    grow_increment,
    faction_roll,
    resolve_contest,
    faction_weight,
    domain_cap_resistance,
)
from engine.models import Faction, FactionTrait, Leader


def make_faction(rating=2.0, leader_status="present") -> Faction:
    return Faction(
        id="test", name="Test Faction", domain_primary="political",
        leader=Leader(name="Test", status=leader_status or "present"),
        rating=rating, health=75,
    )


class TestGrowIncrement:
    def test_curve_is_one_over_level_plus_one(self):
        # Grow increment = 1 / (level + 1) for every level 1–9.
        for level in range(1, 10):
            assert grow_increment(level) == pytest.approx(1 / (level + 1), rel=1e-4)

    def test_decelerates_with_level(self):
        assert grow_increment(1) > grow_increment(5) > grow_increment(9)


class TestFactionWeight:
    def test_weight_equals_level(self):
        # Domain utilization is Σ level: each faction contributes its own level.
        for level in range(1, 11):
            assert faction_weight(level) == level

    def test_never_negative(self):
        assert faction_weight(0) == 0
        assert faction_weight(-3) == 0


class TestResolveContest:
    def test_returns_tuple_of_four(self):
        a = make_faction(2.0)
        d = make_faction(2.0)
        result = resolve_contest(a, d)
        assert len(result) == 4

    def test_outcome_is_valid_string(self):
        a = make_faction(2.0)
        d = make_faction(2.0)
        outcome, margin, atk, dfn = resolve_contest(a, d)
        assert outcome in ("decisive", "partial", "fail")

    def test_margin_matches_rolls(self):
        a = make_faction(2.0)
        d = make_faction(2.0)
        outcome, margin, atk, dfn = resolve_contest(a, d)
        assert margin == atk - dfn

    def test_leaderless_gets_penalty(self):
        """Leaderless faction rolls lower on average."""
        import random
        random.seed(42)
        totals_led = []
        totals_leaderless = []
        for _ in range(200):
            a_led = make_faction(3.0, "present")
            a_no = make_faction(3.0, "absent")
            d = make_faction(1.0, "present")
            _, _, atk_led, _ = resolve_contest(a_led, d)
            _, _, atk_no, _ = resolve_contest(a_no, d)
            totals_led.append(atk_led)
            totals_leaderless.append(atk_no)
        assert sum(totals_led) > sum(totals_leaderless)


class TestDomainCapResistance:
    def test_open_below_60(self):
        assert domain_cap_resistance(50, 100) == "open"

    def test_passive_at_70(self):
        assert domain_cap_resistance(70, 100) == "passive"

    def test_contested_at_90(self):
        assert domain_cap_resistance(90, 100) == "contested"

    def test_blocked_at_95(self):
        assert domain_cap_resistance(95, 100) == "blocked"

    def test_zero_cap_is_blocked(self):
        assert domain_cap_resistance(0, 0) == "blocked"
