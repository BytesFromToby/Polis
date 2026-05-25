"""
test_harm_block_steal.py — Edge case tests for Harm, Block (set/fire), Steal (v4).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from engine.models import Faction, Leader
from engine.actions import resolve_harm, set_block, fire_block, resolve_steal


def make_faction(fid="a", rating=2.0, domain="political") -> Faction:
    return Faction(id=fid, name=f"Faction {fid}", domain_primary=domain,
                   rating=rating, health=75, entrench=75,
                   leader=Leader(name="Test"))


class TestHarmActorResult:
    def test_actor_id_is_attacker(self):
        a = make_faction("atk", 3.0)
        d = make_faction("def", 2.0)
        result = resolve_harm(a, d, {"atk": a, "def": d})
        assert result.actor_id == "atk"

    def test_target_id_is_defender(self):
        a = make_faction("atk", 3.0)
        d = make_faction("def", 2.0)
        result = resolve_harm(a, d, {"atk": a, "def": d})
        assert result.target_id == "def"

    def test_cross_domain_blocked(self):
        a = make_faction("atk", 3.0, domain="political")
        d = make_faction("def", 2.0, domain="street")
        result = resolve_harm(a, d, {"atk": a, "def": d})
        assert result.outcome == "blocked"


class TestSetBlockActorResult:
    def test_set_block_hides_target(self):
        a = make_faction("blk", 3.0)
        result = set_block(a, "def")
        assert result.actor_id == "blk"
        assert result.target_id is None  # hidden from public log

    def test_fire_block_reveals_target(self):
        a = make_faction("blk", 3.0)
        d = make_faction("def", 2.0)
        a.active_block_target = "def"
        result = fire_block(a, d)
        assert result.actor_id == "blk"
        assert result.target_id == "def"


class TestStealActorResult:
    def test_actor_id_is_thief(self):
        a = make_faction("thf", 3.0)
        d = make_faction("vic", 2.0)
        result = resolve_steal(a, d)
        assert result.actor_id == "thf"

    def test_target_id_is_victim(self):
        a = make_faction("thf", 3.0)
        d = make_faction("vic", 2.0)
        result = resolve_steal(a, d)
        assert result.target_id == "vic"

    def test_cross_domain_blocked(self):
        a = make_faction("thf", 3.0, domain="political")
        d = make_faction("vic", 2.0, domain="street")
        result = resolve_steal(a, d)
        assert result.outcome == "blocked"
