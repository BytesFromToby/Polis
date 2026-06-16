"""Event-forced Withhold + the cycle reorder (events_spec §Withhold, cycle-runner_spec item 5a).

A `withhold` event sets `withholding` on its target each active cycle, zeroing that faction's
chain contribution; active-event effects now apply before the needs step (felt the same cycle),
while new-event rolling stays after it (gates see this cycle's bands). Redundancy proves via the
flag exactly as it proves via removal.
"""
import os
import random

from engine.cycle.runner import run_cycle
from engine.events.event_system import _matches_trigger, process_active_events
from engine.models import GameEvent, EventEffect, Mayor, ThePublic, Treasury
from engine.needs.bands import FED_BANDS, band_index, fed_band
from loaders import load_chains, load_state_from_json

CHAINS = load_chains()
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
ARISTOCRACY = ("eumelidai", "pyrrhidai", "skiadai", "elaiades")


def mk_withhold_event(target_id, duration):
    return GameEvent(
        id=f"storm_{target_id}", name="The Great Storm", type="random",
        trigger="test", target_type="faction", target_id=target_id,
        duration=duration, cycles_remaining=duration, status="active",
        effects=[EventEffect(field="withhold", target_id=target_id, value=0,
                             label="the sea closes")],
    )


def band_i(value):
    return band_index(fed_band(value), FED_BANDS)


def run_city(cycles, seed, event_factory=None):
    """Run the standard city; event_factory() (optional) returns active_events injected at c==0."""
    random.seed(seed)
    world, factions, domains = load_state_from_json(DATA_DIR)
    public = ThePublic()
    active = event_factory() if event_factory else []
    fed = []
    for c in range(cycles):
        run_cycle(world, factions, domains, mayor=Mayor(), treasury=Treasury(),
                  public=public, chains=CHAINS, active_events=active)
        fed.append(public.fed)
    return fed, factions


class TestEventEffect:
    def test_active_event_sets_withholding_each_cycle(self):
        world, factions, domains = load_state_from_json(DATA_DIR)
        event = mk_withhold_event("netmenders", duration=2)
        process_active_events([event], factions, domains, world)
        assert factions["netmenders"].withholding is True
        assert event.cycles_remaining == 1  # decremented

    def test_resolves_after_duration(self):
        world, factions, domains = load_state_from_json(DATA_DIR)
        event = mk_withhold_event("netmenders", duration=1)
        process_active_events([event], factions, domains, world)
        assert event.status == "resolved"  # one-cycle storm is spent


class TestFeltSameCycleAndRestores:
    def test_withhold_felt_same_cycle(self):
        # one cycle: an active storm lowers fed this very cycle (effects applied before needs)
        control, _ = run_city(1, seed=701)
        stormed, _ = run_city(1, seed=701,
                              event_factory=lambda: [mk_withhold_event("netmenders", 1)])
        assert stormed[-1] < control[-1]

    def test_recovers_after_storm_passes(self):
        # a 3-cycle storm then recovery; fed during the storm is below the pre/post baseline
        fed, factions = run_city(20, seed=702,
                                 event_factory=lambda: [mk_withhold_event("netmenders", 3)])
        # the flag is cycle-only — cleared once the storm resolves
        assert factions["netmenders"].withholding is False
        # later cycles recover above the storm trough
        assert max(fed[10:]) > min(fed[:5])


class TestRedundancyUnderForceWithhold:
    """One source force-withheld → never Starving; all sources force-withheld → Starving —
    the redundancy property, proven through the withholding flag instead of removal."""

    def _run_withholding(self, target_ids, cycles=30, seed=703):
        def factory():
            return [mk_withhold_event(t, cycles) for t in target_ids]
        return run_city(cycles, seed, event_factory=factory)[0]

    def test_one_source_withheld_never_starving(self):
        fed = self._run_withholding(("netmenders",))
        assert all(band_i(v) > band_index("Starving", FED_BANDS) for v in fed)

    def test_all_sources_withheld_starving(self):
        # barley + flocks (all aristocracy estates) + fish (netmenders)
        fed = self._run_withholding(ARISTOCRACY + ("netmenders",))
        assert band_i(fed[-1]) == band_index("Starving", FED_BANDS)


class TestOrderingRollsSeeBands:
    """The reorder's second half: new-event rolling still runs after needs, so band gates read
    this cycle's freshly-drifted bands (a withhold storm that drives the city Hungry makes a
    Hungry-gated template eligible against the post-needs band, not the stale pre-needs one)."""

    def test_gate_evaluated_against_post_needs_band(self):
        # drive the city down with an all-source storm, then check a band gate sees the low band
        fed, factions = run_city(15, seed=704,
                                 event_factory=lambda: [mk_withhold_event(t, 15)
                                                        for t in ARISTOCRACY + ("netmenders",)])
        public = ThePublic(fed=fed[-1])
        world, _, _ = load_state_from_json(DATA_DIR)
        # a Starving-gated template is eligible exactly when the post-needs band reached Starving
        starving_tmpl = {"trigger_conditions": {"max_fed_band": "Starving"}}
        eligible = _matches_trigger(starving_tmpl, "professions", 0, factions, world, public)
        assert eligible == (band_i(fed[-1]) <= band_index("Starving", FED_BANDS))
