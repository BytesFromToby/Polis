"""Confidence — bands over the support axis + the faction posture modifier (public-needs_spec).

Confidence is NOT a new field: it is `support` (−50..+50) viewed in 5 bands. Constants imported.
"""
import engine.npc.behavior as behavior
from engine.models import Faction, Leader, ThePublic, WorldState
from engine.needs.bands import confidence_band
from serializer import serialize_the_public


def fac(fid="rival", dom="guilds"):
    return Faction(id=fid, name=fid.title(), domain_primary=dom, leader=Leader(name=fid), rating=2.0)


def captured_weights(support_or_none, monkeypatch):
    """Capture the weight dict for a faction with a public at the given support (or no public)."""
    captured = {}
    monkeypatch.setattr(behavior, "weighted_choice", lambda w: (captured.update(w), "Grow")[1])
    monkeypatch.setattr(behavior.random, "random", lambda: 0.99)
    f = fac()
    public = None if support_or_none is None else ThePublic(support=support_or_none)
    behavior.select_faction_action(f, {"rival": f}, {}, WorldState(), public=public)
    return captured


class TestBands:
    def test_boundaries(self):
        assert [confidence_band(s) for s in (-30, -29, -10, -9, 10, 11, 30, 31)] == \
            ["Hostile", "Suspicious", "Suspicious", "Neutral", "Neutral", "Favorable",
             "Favorable", "Beloved"]

    def test_extremes(self):
        assert confidence_band(-50) == "Hostile"
        assert confidence_band(50) == "Beloved"


class TestPosture:
    def test_hostile_emboldens(self, monkeypatch):
        base = captured_weights(0, monkeypatch)       # Neutral
        hostile = captured_weights(-40, monkeypatch)  # Hostile
        assert hostile["Harm"] == base["Harm"] + behavior.CONFIDENCE_EMBOLDEN_WEIGHT
        assert hostile["Steal"] == base["Steal"] + behavior.CONFIDENCE_EMBOLDEN_WEIGHT

    def test_suspicious_emboldens(self, monkeypatch):
        base = captured_weights(0, monkeypatch)
        susp = captured_weights(-20, monkeypatch)     # Suspicious
        assert susp["Harm"] == base["Harm"] + behavior.CONFIDENCE_EMBOLDEN_WEIGHT

    def test_beloved_damps(self, monkeypatch):
        base = captured_weights(0, monkeypatch)
        beloved = captured_weights(40, monkeypatch)   # Beloved
        assert beloved["Harm"] == base["Harm"] - behavior.CONFIDENCE_COOP_WEIGHT
        assert beloved["Steal"] == base["Steal"] - behavior.CONFIDENCE_COOP_WEIGHT

    def test_neutral_unchanged(self, monkeypatch):
        # Neutral band makes no confidence adjustment; compare to no-public baseline
        neutral = captured_weights(5, monkeypatch)
        no_public = captured_weights(None, monkeypatch)
        assert neutral["Harm"] == no_public["Harm"]
        assert neutral["Steal"] == no_public["Steal"]


class TestSerialization:
    def test_confidence_band_exposed_off_support(self):
        assert serialize_the_public(ThePublic(support=-40))["confidence_band"] == "Hostile"
        assert serialize_the_public(ThePublic(support=40))["confidence_band"] == "Beloved"
