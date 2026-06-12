"""Tests for the Toil action — resolver, NPC weights, deal commitment (actions_spec v5.1)."""
import engine.npc.behavior as behavior
from engine.actions import resolve_toil
from engine.models import Faction, Leader, ThePublic, WorldState, FactionTrait
from engine.needs.chain import chain_role_faction_ids
from loaders import load_chains


CHAINS = load_chains()


def mk_faction(fid, domain, rating=2.0, traits=None):
    return Faction(id=fid, name=fid.title(), domain_primary=domain,
                   leader=Leader(name=f"L-{fid}"), rating=rating,
                   traits=traits or [])


def mk_city():
    factions = {
        "estate0": mk_faction("estate0", "aristocracy", 4.0),
        "ovenmen": mk_faction("ovenmen", "guilds", 2.0),
        "winepressers": mk_faction("winepressers", "guilds", 2.0),
        "tidesworn": mk_faction("tidesworn", "temples", 3.0),
    }
    return factions, chain_role_faction_ids(CHAINS, factions)


def captured_weights(faction, factions, roles, public=None, monkeypatch=None):
    """Run select_faction_action with weighted_choice patched to capture the dict."""
    captured = {}

    def capture(weights):
        captured.update(weights)
        return "Grow"

    monkeypatch.setattr(behavior, "weighted_choice", capture)
    monkeypatch.setattr(behavior.random, "random", lambda: 0.99)  # never Skip
    behavior.select_faction_action(
        faction, factions, {}, WorldState(),
        public=public, chain_roles=roles,
    )
    return captured


class TestResolver:
    def test_sets_flag_no_rank_or_health_change(self):
        f = mk_faction("ovenmen", "guilds", rating=2.5)
        f.health = 60
        result = resolve_toil(f)
        assert f.toiling is True
        assert f.rating == 2.5
        assert f.health == 60
        assert result.action == "Toil"


class TestWeights:
    def test_non_chain_faction_has_no_toil(self, monkeypatch):
        factions, roles = mk_city()
        w = captured_weights(factions["tidesworn"], factions, roles, monkeypatch=monkeypatch)
        assert "Toil" not in w

    def test_chain_faction_base_weight(self, monkeypatch):
        factions, roles = mk_city()
        w = captured_weights(factions["ovenmen"], factions, roles, monkeypatch=monkeypatch)
        assert w["Toil"] == behavior.BASE_WEIGHTS["Toil"]

    def test_hungry_public_boosts_toil(self, monkeypatch):
        factions, roles = mk_city()
        public = ThePublic(fed=30)  # Hungry
        w = captured_weights(factions["ovenmen"], factions, roles, public=public,
                             monkeypatch=monkeypatch)
        assert w["Toil"] == behavior.BASE_WEIGHTS["Toil"] + 25

    def test_fed_public_no_boost(self, monkeypatch):
        factions, roles = mk_city()
        public = ThePublic(fed=60)  # Fed
        w = captured_weights(factions["ovenmen"], factions, roles, public=public,
                             monkeypatch=monkeypatch)
        assert w["Toil"] == behavior.BASE_WEIGHTS["Toil"]

    def test_industrious_adds_ten(self, monkeypatch):
        factions, roles = mk_city()
        factions["ovenmen"].traits = [FactionTrait("industrious", "moderate")]
        w = captured_weights(factions["ovenmen"], factions, roles, monkeypatch=monkeypatch)
        assert w["Toil"] == behavior.BASE_WEIGHTS["Toil"] + 10


class TestCommitted:
    def test_committed_toil_forces_plan(self):
        factions, roles = mk_city()
        f = factions["winepressers"]
        f.committed_action = "Toil"
        plan = behavior.select_faction_action(f, factions, {}, WorldState(),
                                              chain_roles=roles)
        assert plan.action == "Toil"
        assert plan.target_id is None
