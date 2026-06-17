"""The Public→production wire — the efficiency multiplier (public-needs_spec).

health Robust/Thriving lift food output; consumption Tipsy/Sodden cut it. 1.0 at Healthy+Tempered.
"""
from engine.models import Faction, Leader, ThePublic
from engine.needs.chain import compute_chain
from engine.needs.scales import (
    production_efficiency, HEALTH_OUTPUT, CONSUMPTION_OUTPUT, EFF_MIN, EFF_MAX,
)
from loaders import load_chains

CHAINS = load_chains()


def mk_city():
    def f(fid, dom, r):
        return Faction(id=fid, name=fid.title(), domain_primary=dom, leader=Leader(name=fid), rating=r)
    return {
        "estate0": f("estate0", "aristocracy", 4.0),
        "ovenmen": f("ovenmen", "guilds", 3.0),
        "winepressers": f("winepressers", "guilds", 3.0),
    }


class TestEfficiency:
    def test_neutral_is_one(self):
        p = ThePublic(health=50, consumption=50)  # Healthy + Tempered
        assert production_efficiency(p) == 1.0

    def test_thriving_lifts(self):
        p = ThePublic(health=90, consumption=50)  # Thriving + Tempered
        assert production_efficiency(p) == 1.0 + 2 * HEALTH_OUTPUT

    def test_robust_lifts_one_step(self):
        p = ThePublic(health=70, consumption=50)  # Robust
        assert production_efficiency(p) == 1.0 + HEALTH_OUTPUT

    def test_sodden_cuts(self):
        p = ThePublic(health=50, consumption=90)  # Healthy + Sodden
        assert production_efficiency(p) == 1.0 - 2 * CONSUMPTION_OUTPUT

    def test_tipsy_cuts_one_step(self):
        p = ThePublic(health=50, consumption=70)  # Tipsy
        assert production_efficiency(p) == 1.0 - CONSUMPTION_OUTPUT

    def test_clamped(self):
        # both extremes can't push past the clamp
        assert production_efficiency(ThePublic(health=100, consumption=50)) <= EFF_MAX
        assert production_efficiency(ThePublic(health=10, consumption=100)) >= EFF_MIN


class TestChainScaling:
    def test_higher_efficiency_more_food(self):
        f = mk_city()
        lo = compute_chain(f, 20000, CHAINS, efficiency=0.8)
        mid = compute_chain(f, 20000, CHAINS, efficiency=1.0)
        hi = compute_chain(f, 20000, CHAINS, efficiency=1.2)
        assert lo.fed_target < mid.fed_target < hi.fed_target
        assert lo.happy_target < mid.happy_target < hi.happy_target

    def test_efficiency_does_not_touch_raw_units_or_wine(self):
        f = mk_city()
        a = compute_chain(f, 20000, CHAINS, efficiency=1.0)
        b = compute_chain(f, 20000, CHAINS, efficiency=0.6)
        assert a.raw == b.raw
        assert a.units == b.units          # unit conservation untouched
        assert a.wine_happy == b.wine_happy  # consumption driver untouched

    def test_default_is_unwired(self):
        f = mk_city()
        assert compute_chain(f, 20000, CHAINS).fed_target == \
               compute_chain(f, 20000, CHAINS, efficiency=1.0).fed_target
