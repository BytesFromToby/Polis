"""
test_cap_and_fill.py — v3 stub. Unit-based capacity/fill tests removed.

Domain utilization tests for the faction-weight based system.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from engine.formulas import faction_weight


class TestFactionWeight:
    """Domain utilization is sum of faction_weight(floor) for factions in domain."""

    def test_floor_1_zero(self):
        assert faction_weight(1) == 0

    def test_floor_2(self):
        assert faction_weight(2) == 2

    def test_floor_5(self):
        assert faction_weight(5) == 16

    def test_unknown_floor(self):
        assert faction_weight(99) == 0
