"""
test_actions.py — Tests for v5 faction action resolvers (demo redesign).

Action set: Grow · Protect · Aid · Harm · Steal. Block is gone; Harm/Aid/Protect
act on `health`, Grow/Steal act on `rank`. Contested outcomes (Harm/Steal) are
forced via monkeypatch so each tier is deterministic.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import engine.actions.faction as faction_mod
from engine.actions import resolve_grow, resolve_harm, resolve_protect, resolve_aid, resolve_steal
from engine.models import Faction, Domain, Leader
from engine.formulas import RATING_MAX, grow_increment


def make_faction(fid="a", rating=2.0, health=75, domain="political") -> Faction:
    return Faction(
        id=fid, name=f"Faction {fid}", domain_primary=domain,
        rating=rating, health=health,
        leader=Leader(name="Test Leader"),
    )


def make_domain(cap=100, utilization=0.0) -> Domain:
    return Domain(id="political", name="Political", cap=cap, utilization=utilization)


def force_contest(monkeypatch, outcome):
    """Force resolve_contest (as seen by faction.py) to a fixed outcome."""
    margin = {"decisive": 5, "partial": 2, "fail": -1}[outcome]
    monkeypatch.setattr(
        faction_mod, "resolve_contest",
        lambda atk, dfn, *a, **k: (outcome, margin, 15, 15 - margin),
    )


# ── GROW ──────────────────────────────────────────────────────────────────────

class TestResolveGrow:
    def test_grows_by_one_over_level_plus_one(self):
        f = make_faction(rating=2.0)  # level 2 → increment 1/3
        result = resolve_grow(f, {"political": make_domain()})
        assert result.delta == pytest.approx(grow_increment(2))
        assert f.rating == pytest.approx(2.0 + grow_increment(2), abs=1e-4)

    def test_crossing_integer_levels_up_dramatically(self):
        f = make_faction(rating=1.9)  # level 1 → increment 0.5 → 2.4 crosses to level 2
        assert f.level == 1
        result = resolve_grow(f, {"political": make_domain()})
        assert f.level == 2
        assert result.dramatic is True

    def test_blocked_at_max(self):
        f = make_faction(rating=RATING_MAX)
        result = resolve_grow(f, {"political": make_domain()})
        assert result.outcome == "blocked"
        assert f.rating == RATING_MAX

    def test_blocked_when_domain_full(self):
        f = make_faction(rating=2.0)
        result = resolve_grow(f, {"political": make_domain(cap=10, utilization=10)})
        assert result.outcome == "blocked"
        assert f.rating == 2.0  # no gain

    def test_rank_never_exceeds_10(self):
        f = make_faction(rating=9.95)  # level 9 → increment 0.1 → would be 10.05
        resolve_grow(f, {"political": make_domain()})
        assert f.rating == RATING_MAX
        assert f.rating <= 10.0


# ── PROTECT ─────────────────────────────────────────────────────────────────

class TestResolveProtect:
    def test_heals_self_50(self):
        f = make_faction(health=40)
        result = resolve_protect(f)
        assert f.health == 90
        assert result.outcome == "success"

    def test_capped_at_100(self):
        f = make_faction(health=70)
        resolve_protect(f)
        assert f.health == 100


# ── AID ──────────────────────────────────────────────────────────────────────

class TestResolveAid:
    def test_heals_target_25(self):
        actor = make_faction("a")
        target = make_faction("b", health=40)
        resolve_aid(actor, target)
        assert target.health == 65

    def test_capped_at_100(self):
        actor = make_faction("a")
        target = make_faction("b", health=90)
        resolve_aid(actor, target)
        assert target.health == 100

    def test_allowed_across_domains(self):
        actor = make_faction("a", domain="political")
        target = make_faction("b", health=40, domain="trade")
        result = resolve_aid(actor, target)
        assert target.health == 65
        assert result.outcome == "success"


# ── HARM ─────────────────────────────────────────────────────────────────────

class TestResolveHarm:
    def test_decisive_reduces_health_30(self, monkeypatch):
        force_contest(monkeypatch, "decisive")
        a = make_faction("a", rating=3.0)
        d = make_faction("b", rating=3.0, health=75)
        result = resolve_harm(a, d, {"a": a, "b": d})
        assert result.outcome == "decisive"
        assert d.health == 45

    def test_partial_reduces_health_15(self, monkeypatch):
        force_contest(monkeypatch, "partial")
        a = make_faction("a", rating=3.0)
        d = make_faction("b", rating=3.0, health=75)
        resolve_harm(a, d, {"a": a, "b": d})
        assert d.health == 60

    def test_fail_leaves_health_unchanged(self, monkeypatch):
        force_contest(monkeypatch, "fail")
        a = make_faction("a", rating=3.0)
        d = make_faction("b", rating=3.0, health=75)
        resolve_harm(a, d, {"a": a, "b": d})
        assert d.health == 75

    def test_health_floors_at_0(self, monkeypatch):
        force_contest(monkeypatch, "decisive")
        a = make_faction("a", rating=3.0)
        d = make_faction("b", rating=3.0, health=20)
        resolve_harm(a, d, {"a": a, "b": d})
        assert d.health == 0

    def test_cannot_target_level_1(self):
        a = make_faction("a", rating=3.0)
        d = make_faction("b", rating=1.0, health=75)  # level 1 — safe floor
        result = resolve_harm(a, d, {"a": a, "b": d})
        assert result.outcome == "blocked"
        assert d.health == 75

    def test_blocked_across_domains(self):
        a = make_faction("a", rating=3.0, domain="political")
        d = make_faction("b", rating=3.0, domain="street")
        result = resolve_harm(a, d, {"a": a, "b": d})
        assert result.outcome == "blocked"


# ── STEAL ────────────────────────────────────────────────────────────────────

class TestResolveSteal:
    def test_decisive_transfers_full_amount(self, monkeypatch):
        force_contest(monkeypatch, "decisive")
        a = make_faction("a", rating=3.0)   # level 3 → base 0.5/4 = 0.125
        d = make_faction("b", rating=4.0)
        resolve_steal(a, d)
        assert a.rating == pytest.approx(3.125)
        assert d.rating == pytest.approx(3.875)

    def test_partial_transfers_half(self, monkeypatch):
        force_contest(monkeypatch, "partial")
        a = make_faction("a", rating=3.0)   # base 0.125 → partial 0.0625
        d = make_faction("b", rating=4.0)
        resolve_steal(a, d)
        assert a.rating == pytest.approx(3.0625)
        assert d.rating == pytest.approx(3.9375)

    def test_fail_no_transfer(self, monkeypatch):
        force_contest(monkeypatch, "fail")
        a = make_faction("a", rating=3.0)
        d = make_faction("b", rating=4.0)
        resolve_steal(a, d)
        assert a.rating == 3.0
        assert d.rating == 4.0

    def test_actor_rank_never_exceeds_10(self, monkeypatch):
        force_contest(monkeypatch, "decisive")
        a = make_faction("a", rating=9.99)  # level 9 → base 0.05 → would be 10.04
        d = make_faction("b", rating=4.0)
        resolve_steal(a, d)
        assert a.rating == RATING_MAX

    def test_target_rank_never_below_1(self, monkeypatch):
        force_contest(monkeypatch, "decisive")
        a = make_faction("a", rating=2.0)
        d = make_faction("b", rating=2.0)
        resolve_steal(a, d)
        assert d.rating >= 1.0

    def test_cannot_target_level_1(self):
        a = make_faction("a", rating=3.0)
        d = make_faction("b", rating=1.0)  # level 1 — safe floor
        result = resolve_steal(a, d)
        assert result.outcome == "blocked"
        assert d.rating == 1.0

    def test_blocked_across_domains(self):
        a = make_faction("a", rating=3.0, domain="political")
        d = make_faction("b", rating=3.0, domain="street")
        result = resolve_steal(a, d)
        assert result.outcome == "blocked"
