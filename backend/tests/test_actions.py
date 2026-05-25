"""
test_actions.py — Tests for v4 faction action resolvers.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from engine.actions import resolve_grow, resolve_harm, set_block, fire_block, resolve_protect, resolve_steal
from engine.models import Faction, Domain, Leader
from engine.formulas import RATING_MAX


def make_faction(fid="a", rating=2.0, entrench=75, health=75, domain="political") -> Faction:
    return Faction(
        id=fid, name=f"Faction {fid}", domain_primary=domain,
        rating=rating, health=health, entrench=entrench,
        leader=Leader(name="Test Leader"),
    )


def make_domain(cap=100, utilization=0.0) -> Domain:
    return Domain(id="political", name="Political", cap=cap, utilization=utilization)


class TestResolveGrow:
    def test_grows_rating(self):
        f = make_faction(rating=1.0)
        d = make_domain()
        old = f.rating
        resolve_grow(f, {"political": d})
        assert f.rating > old

    def test_blocked_at_max(self):
        f = make_faction(rating=RATING_MAX)
        d = make_domain()
        result = resolve_grow(f, {"political": d})
        assert result.outcome == "blocked"
        assert f.rating == RATING_MAX

    def test_blocked_when_domain_full(self):
        f = make_faction(rating=2.0)
        d = make_domain(cap=10, utilization=10)
        result = resolve_grow(f, {"political": d})
        assert result.outcome == "blocked"


class TestResolveProtect:
    def test_increases_entrench(self):
        f = make_faction(entrench=50)
        result = resolve_protect(f)
        assert f.entrench == 60
        assert result.outcome == "success"

    def test_capped_at_100(self):
        f = make_faction(entrench=95)
        resolve_protect(f)
        assert f.entrench == 100


class TestResolveHarm:
    def test_returns_valid_outcome(self):
        a = make_faction("a", rating=3.0, domain="political")
        d = make_faction("b", rating=2.0, domain="political")
        result = resolve_harm(a, d, {"a": a, "b": d})
        assert result.outcome in ("decisive", "partial", "fail")

    def test_blocked_across_domains(self):
        a = make_faction("a", rating=3.0, domain="political")
        d = make_faction("b", rating=2.0, domain="street")
        result = resolve_harm(a, d, {"a": a, "b": d})
        assert result.outcome == "blocked"

    def test_decisive_reduces_target(self):
        import random
        for seed in range(100):
            random.seed(seed)
            a = make_faction("a", rating=5.0, domain="political")
            d = make_faction("b", rating=1.0, entrench=50, domain="political")
            old_rating = d.rating
            old_entrench = d.entrench
            result = resolve_harm(a, d, {"a": a, "b": d})
            if result.outcome == "decisive":
                assert d.rating < old_rating or d.entrench < old_entrench
                return
        pytest.skip("Could not get decisive outcome in 100 seeds")


class TestSetAndFireBlock:
    def test_set_block_stores_target(self):
        a = make_faction("a")
        result = set_block(a, "b")
        assert a.active_block_target == "b"
        assert result.outcome == "no_op"
        assert result.target_id is None  # hidden from log

    def test_fire_block_consumes_trap(self):
        a = make_faction("a", rating=3.0)
        b = make_faction("b", rating=2.0)
        a.active_block_target = "b"
        fire_block(a, b)
        assert a.active_block_target == ""

    def test_fire_block_decisive_cancels(self):
        import random
        for seed in range(100):
            random.seed(seed)
            a = make_faction("a", rating=5.0)
            b = make_faction("b", rating=1.0)
            a.active_block_target = "b"
            result = fire_block(a, b)
            if result.outcome == "decisive":
                assert b.action_cancelled is True
                return
        pytest.skip("Could not get decisive outcome in 100 seeds")

    def test_fire_block_partial_downgrades(self):
        import random
        for seed in range(200):
            random.seed(seed)
            a = make_faction("a", rating=3.0)
            b = make_faction("b", rating=2.0)
            a.active_block_target = "b"
            result = fire_block(a, b)
            if result.outcome == "partial":
                assert b.action_downgraded is True
                return
        pytest.skip("Could not get partial outcome in 200 seeds")


class TestResolveSteal:
    def test_decisive_transfers_rating(self):
        import random
        for seed in range(100):
            random.seed(seed)
            a = make_faction("a", rating=3.0, domain="political")
            d = make_faction("b", rating=2.5, domain="political")
            old_a = a.rating
            old_d = d.rating
            result = resolve_steal(a, d)
            if result.outcome == "decisive":
                assert a.rating > old_a
                assert d.rating < old_d
                return
        pytest.skip("Could not get decisive outcome")

    def test_blocked_across_domains(self):
        a = make_faction("a", rating=3.0, domain="political")
        d = make_faction("b", rating=2.0, domain="street")
        result = resolve_steal(a, d)
        assert result.outcome == "blocked"
