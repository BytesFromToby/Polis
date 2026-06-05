"""
test_cap_and_fill.py — v3 stub. Unit-based capacity/fill tests removed.

Domain utilization tests for the faction-weight based system.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from engine.formulas import faction_weight


class TestFactionWeight:
    """Domain utilization is Σ level: each faction contributes its level (= int(rating))."""

    def test_level_1_contributes_1(self):
        assert faction_weight(1) == 1

    def test_level_2(self):
        assert faction_weight(2) == 2

    def test_level_5(self):
        assert faction_weight(5) == 5

    def test_never_negative(self):
        assert faction_weight(0) == 0
        assert faction_weight(-1) == 0
