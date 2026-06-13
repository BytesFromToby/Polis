"""Public-need gates on event templates (events_spec v1.1 — Public-need gates)."""
import random

from engine.cycle.runner import run_cycle
from engine.events.event_system import _matches_trigger, roll_for_random_events
from engine.models import Mayor, ThePublic, Treasury, WorldState
from loaders import load_state_from_json, load_chains

CHAINS = load_chains()


def sentinel(conds):
    """No-effect template carrying only the given trigger conditions."""
    return {
        "id": "sentinel",
        "name": "Sentinel",
        "type": "random",
        "trigger_conditions": conds,
        "weight": 1,
        "template": {"target_type": "world", "target_id": "world", "duration": 1, "effects": []},
    }


def eligible(conds, public):
    return _matches_trigger(sentinel(conds), "guilds", 5.0, {}, WorldState(), public)


class TestFedGates:
    def test_max_fed_band_boundary(self):
        gate = {"max_fed_band": "Starving"}
        assert eligible(gate, ThePublic(fed=20))       # Starving
        assert not eligible(gate, ThePublic(fed=21))   # Hungry

    def test_min_fed_band_boundary(self):
        gate = {"min_fed_band": "Well fed"}
        assert eligible(gate, ThePublic(fed=76))
        assert not eligible(gate, ThePublic(fed=75))

    def test_one_sentinel_per_band(self):
        for fed, band in ((10, "Starving"), (30, "Hungry"), (60, "Fed"), (90, "Well fed")):
            gate = {"min_fed_band": band, "max_fed_band": band}
            assert eligible(gate, ThePublic(fed=fed))
            assert not eligible(gate, ThePublic(fed=(fed + 50) % 100))


class TestHappyGates:
    def test_max_happy_band(self):
        gate = {"max_happy_band": "Miserable"}
        assert eligible(gate, ThePublic(happy=15))
        assert not eligible(gate, ThePublic(happy=30))

    def test_min_happy_band(self):
        gate = {"min_happy_band": "Festive"}
        assert eligible(gate, ThePublic(happy=80))
        assert not eligible(gate, ThePublic(happy=70))


class TestSicklyGate:
    def test_boundary(self):
        gate = {"sickly": True}
        assert eligible(gate, ThePublic(health=39))
        assert not eligible(gate, ThePublic(health=40))


class TestNoPublic:
    def test_need_gated_template_ineligible_without_public(self):
        assert not eligible({"max_fed_band": "Starving"}, None)

    def test_ungated_template_unaffected(self):
        assert eligible({}, None)


class TestSameCycleGating:
    def test_starving_gate_opens_same_cycle(self, monkeypatch):
        """A cycle that starves the city unlocks a Starving-gated event that same cycle:
        the needs step (item 5b) runs before the event roll."""
        world, factions, domains = load_state_from_json("data")
        world.chaos = {"guilds": 5.0}
        # Huge population + fed just above the drift gap → this cycle's drift lands in Starving.
        public = ThePublic(fed=22, population=500000)
        deck = [sentinel({"max_fed_band": "Starving"})]
        active = []

        monkeypatch.setattr(random, "random", lambda: 0.0)       # roll always passes
        monkeypatch.setattr(random, "choices", lambda c, weights, k: [c[0]])

        run_cycle(world, factions, domains, mayor=Mayor(), treasury=Treasury(),
                  public=public, chains=CHAINS, event_deck=deck, active_events=active)

        assert public.fed <= 20  # the city starved this cycle
        assert any(e.id == "sentinel" for e in active)
