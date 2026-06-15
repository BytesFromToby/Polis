"""Cycle integration for the Public-needs step (public-needs_spec — Cycle integration)."""
import json
import os
import random

from engine.cycle.runner import run_cycle
from engine.models import Mayor, Treasury, ThePublic, WorldState
from engine.needs.chain import compute_chain
from loaders import load_state_from_json, load_chains
from serializer import serialize_state, deserialize_state

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CHAINS = load_chains()


def fresh_city():
    world, factions, domains = load_state_from_json(DATA_DIR)
    return world, factions, domains


class TestNeedsStepRuns:
    def test_fed_moves_toward_chain_target(self):
        random.seed(7)
        world, factions, domains = fresh_city()
        public = ThePublic(fed=0, happy=0)
        target = compute_chain(factions, public.population, CHAINS).fed_target
        run_cycle(world, factions, domains, mayor=Mayor(), treasury=Treasury(),
                  public=public, chains=CHAINS)
        # fed started at 0, target is positive → it must have risen (by ≤ DRIFT_STEP)
        assert target > 0
        assert 0 < public.fed <= 10

    def test_without_public_nothing_breaks(self):
        random.seed(7)
        world, factions, domains = fresh_city()
        result = run_cycle(world, factions, domains, mayor=Mayor(), treasury=Treasury(),
                           chains=CHAINS)
        assert result.cycle == 0


class TestToilingReset:
    def test_flags_false_after_run_cycle(self):
        # Spec Done-when: Faction.toiling is always false for every faction after run_cycle returns.
        random.seed(42)
        world, factions, domains = fresh_city()
        for fid in ("eumelidai", "pyrrhidai", "skiadai"):
            factions[fid].committed_action = "Toil"
        run_cycle(world, factions, domains, mayor=Mayor(), treasury=Treasury(),
                  public=ThePublic(fed=50), chains=CHAINS)
        assert all(f.toiling is False for f in factions.values())

    def test_toil_boost_raises_fed_target(self):
        # The boost is real and drift-independent — proven at the source (fed_target), not the
        # drifted fed (which caps at DRIFT_STEP and hides the boost once the city is well-fed).
        world, factions, domains = fresh_city()
        base = compute_chain(factions, 20000, CHAINS).fed_target
        for fid in ("eumelidai", "pyrrhidai", "skiadai"):
            factions[fid].toiling = True
        boosted = compute_chain(factions, 20000, CHAINS).fed_target
        assert boosted > base


class TestSnapshotRoundTrip:
    def test_public_survives_serialize_state(self):
        world, factions, domains = fresh_city()
        public = ThePublic(support=5, health=77, population=23456, fed=41, happy=66)
        data = json.loads(json.dumps(serialize_state(world, factions, domains, public=public)))
        _, _, _, _, _, _, _, restored = deserialize_state(data)
        assert restored is not None
        assert (restored.support, restored.health, restored.population,
                restored.fed, restored.happy) == (5, 77, 23456, 41, 66)

    def test_snapshot_without_public_restores_none(self):
        world, factions, domains = fresh_city()
        data = serialize_state(world, factions, domains)
        *_, restored = deserialize_state(data)
        assert restored is None
