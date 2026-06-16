"""Tests for the Withhold action — resolver, chain ×0, anger-driven NPC weights, deal commitment.

Spec: actions_spec §Withhold, public-needs_spec (withhold + Withhold-matters),
faction-behavior_spec (Step 3 anger row). Constants imported, never copied.
"""
import os
import random

import engine.npc.behavior as behavior
from engine.actions import resolve_withhold
from engine.cycle.runner import run_cycle
from engine.models import Faction, Leader, Mayor, ThePublic, Treasury, WorldState, FactionTrait
from engine.needs.chain import chain_role_faction_ids, compute_chain
from loaders import load_chains, load_state_from_json

CHAINS = load_chains()
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def mk_faction(fid, domain, rating=2.0, traits=None):
    return Faction(id=fid, name=fid.title(), domain_primary=domain,
                   leader=Leader(name=f"L-{fid}"), rating=rating, traits=traits or [])


def mk_city():
    factions = {
        "estate0": mk_faction("estate0", "aristocracy", 4.0),
        "ovenmen": mk_faction("ovenmen", "guilds", 2.0),
        "winepressers": mk_faction("winepressers", "guilds", 2.0),
        "tidesworn": mk_faction("tidesworn", "temples", 3.0),
    }
    return factions, chain_role_faction_ids(CHAINS, factions)


def captured_weights(faction, factions, roles, public=None, mayor=None, monkeypatch=None):
    captured = {}

    def capture(weights):
        captured.update(weights)
        return "Grow"

    monkeypatch.setattr(behavior, "weighted_choice", capture)
    monkeypatch.setattr(behavior.random, "random", lambda: 0.99)  # never Skip
    behavior.select_faction_action(
        faction, factions, {}, WorldState(), public=public, chain_roles=roles, mayor=mayor,
    )
    return captured


class TestResolver:
    def test_sets_flag_no_rank_or_health_change(self):
        f = mk_faction("ovenmen", "guilds", rating=2.5)
        f.health = 60
        result = resolve_withhold(f)
        assert f.withholding is True
        assert f.rating == 2.5
        assert f.health == 60
        assert result.action == "Withhold"
        assert result.outcome == "success"


class TestChainZero:
    """A withholding faction contributes 0 — and Withhold beats Toil."""

    def _producers(self):
        # one aristocracy estate (domain producer) + the two processors
        return {
            "estate0": mk_faction("estate0", "aristocracy", 4.0),
            "ovenmen": mk_faction("ovenmen", "guilds", 3.0),
            "winepressers": mk_faction("winepressers", "guilds", 3.0),
        }

    def test_withholding_producer_yields_zero_harvest(self):
        f = self._producers()
        base = compute_chain(f, population=4000, chains=CHAINS).raw
        f["estate0"].withholding = True
        withheld = compute_chain(f, population=4000, chains=CHAINS).raw
        assert base > 0
        assert withheld == 0.0  # the only producer withheld → no raw at all

    def test_withholding_processor_drops_processed_units(self):
        f = self._producers()
        base = compute_chain(f, population=4000, chains=CHAINS)
        f["ovenmen"].withholding = True
        withheld = compute_chain(f, population=4000, chains=CHAINS)
        # raw is unchanged (producer still works) but bread capacity is gone → less bread
        assert withheld.raw == base.raw
        assert withheld.units.get("bread", 0.0) < base.units.get("bread", 0.0)

    def test_withhold_beats_toil(self):
        f = self._producers()
        f["estate0"].withholding = True
        f["estate0"].toiling = True  # both set — Withhold wins
        out = compute_chain(f, population=4000, chains=CHAINS)
        assert out.raw == 0.0


class TestWeights:
    def test_non_chain_faction_has_no_withhold(self, monkeypatch):
        factions, roles = mk_city()
        w = captured_weights(factions["tidesworn"], factions, roles, monkeypatch=monkeypatch)
        assert "Withhold" not in w

    def test_chain_faction_base_weight_zero_when_not_angry(self, monkeypatch):
        factions, roles = mk_city()
        mayor = Mayor()  # neutral reputation (0) ≥ threshold → no anger
        w = captured_weights(factions["ovenmen"], factions, roles, mayor=mayor,
                             monkeypatch=monkeypatch)
        assert w["Withhold"] == behavior.BASE_WEIGHTS["Withhold"] == 0.0

    def test_no_mayor_means_no_withhold_weight(self, monkeypatch):
        factions, roles = mk_city()
        w = captured_weights(factions["ovenmen"], factions, roles, mayor=None,
                             monkeypatch=monkeypatch)
        assert w.get("Withhold", 0.0) == 0.0

    def test_anger_lifts_withhold_off_zero(self, monkeypatch):
        factions, roles = mk_city()
        mayor = Mayor()
        mayor.set_reputation("ovenmen", behavior.WITHHOLD_ANGER_THRESHOLD)  # exactly at threshold
        w = captured_weights(factions["ovenmen"], factions, roles, mayor=mayor,
                             monkeypatch=monkeypatch)
        assert w["Withhold"] == behavior.WITHHOLD_ANGER_WEIGHT  # one step

    def test_deeper_hostility_scales_weight(self, monkeypatch):
        factions, roles = mk_city()
        mild = Mayor(); mild.set_reputation("ovenmen", behavior.WITHHOLD_ANGER_THRESHOLD)
        deep = Mayor(); deep.set_reputation("ovenmen", behavior.WITHHOLD_ANGER_THRESHOLD - 30)
        w_mild = captured_weights(factions["ovenmen"], factions, roles, mayor=mild,
                                  monkeypatch=monkeypatch)
        w_deep = captured_weights(factions["ovenmen"], factions, roles, mayor=deep,
                                  monkeypatch=monkeypatch)
        assert w_deep["Withhold"] > w_mild["Withhold"]


class TestCommitted:
    def test_committed_withhold_forces_plan_and_resolves(self):
        factions, roles = mk_city()
        f = factions["winepressers"]
        f.committed_action = "Withhold"
        plan = behavior.select_faction_action(f, factions, {}, WorldState(), chain_roles=roles)
        assert plan.action == "Withhold"
        assert plan.target_id is None
        resolve_withhold(f)
        assert f.withholding is True


class TestWithholdMatters:
    """Inverted Toil-matters: one high-level producer withholding deepens the trough, but
    source redundancy keeps the city Hungry-not-Starving from a single withholder."""

    def _run(self, action, seed=505):
        random.seed(seed)
        world, factions, domains = load_state_from_json(DATA_DIR)
        public = ThePublic()
        fed = []
        for c in range(30):
            if 10 <= c < 20:
                factions["netmenders"].committed_action = action
            elif c == 20:
                factions["netmenders"].committed_action = ""
            run_cycle(world, factions, domains, mayor=Mayor(), treasury=Treasury(),
                      public=public, chains=CHAINS)
            fed.append(public.fed)
        return fed

    def test_withhold_deepens_trough_but_not_starving(self):
        from engine.needs.bands import FED_BANDS, band_index, fed_band
        control = self._run("Protect")
        withheld = self._run("Withhold")
        # the strike drives a strictly lower minimum fed than acting normally
        assert min(withheld[10:20]) < min(control[10:20])
        # but one withheld source alone never Starves the city from full health
        starving = band_index("Starving", FED_BANDS)
        assert all(band_index(fed_band(v), FED_BANDS) > starving for v in withheld)
