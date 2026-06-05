"""
test_break.py — Break resolution (demo redesign).

A faction reduced to 0 health never dies. It Breaks:
  - 75% → level −1 (rank drops to (level-1).0; reprieve, no change, at level 1)
  - 25% → leader dies and auto-regenerates
Health always resets to 75. `resolve_break(faction, rng=...)` takes an injectable
RNG so each branch can be forced.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
import pytest
from engine.models import Faction, Leader
from engine.cycle.resolution import resolve_break


def make_faction(fid="a", rating=5.0, health=0, leader_name="Orig") -> Faction:
    return Faction(
        id=fid, name=f"Faction {fid}", domain_primary="political",
        rating=rating, health=health, leader=Leader(name=leader_name),
    )


class StubRNG:
    """Force a branch: random() returns a fixed value; choice() returns a fixed index."""
    def __init__(self, value, choice_index=0):
        self._value = value
        self._choice_index = choice_index

    def random(self):
        return self._value

    def choice(self, seq):
        return seq[self._choice_index]


# rng.random() < 0.25 → leader-death branch; otherwise → level-drop branch.
LEVEL_DROP = StubRNG(0.90)
LEADER_DEATH = StubRNG(0.10)


class TestBreak:
    def test_resets_health_to_75(self):
        f = make_faction(health=0)
        result = resolve_break(f, rng=LEVEL_DROP)
        assert f.health == 75
        assert result.action == "Break"
        assert result.dramatic is True

    def test_faction_survives_break(self):
        f = make_faction(rating=4.0, health=0)
        resolve_break(f, rng=LEVEL_DROP)
        # Still a live faction with valid stats (never removed).
        assert f.health == 75
        assert f.rating >= 1.0

    def test_forced_level_drop(self):
        f = make_faction(rating=3.0, health=0)  # level 3
        resolve_break(f, rng=LEVEL_DROP)
        assert f.rating == 2.0
        assert f.level == 2

    def test_forced_leader_death_regenerates(self):
        f = make_faction(rating=5.0, health=0, leader_name="Orig")
        resolve_break(f, rng=LEADER_DEATH)
        assert f.leader.name != "Orig"          # new leader installed
        assert f.leader.status == "present"
        assert f.rating == 5.0                   # rank untouched on the leader branch

    def test_level_1_reprieve(self):
        f = make_faction(rating=1.0, health=0)  # level 1 — cannot drop further
        resolve_break(f, rng=LEVEL_DROP)
        assert f.level == 1
        assert f.rating == 1.0
        assert f.health == 75

    def test_split_is_roughly_75_25(self):
        random.seed(1234)
        leader_deaths = 0
        trials = 3000
        for _ in range(trials):
            f = make_faction(rating=5.0, health=0, leader_name="Orig")
            resolve_break(f)  # default rng = module random
            if f.leader.name != "Orig":
                leader_deaths += 1
        frac = leader_deaths / trials
        assert 0.21 < frac < 0.29
