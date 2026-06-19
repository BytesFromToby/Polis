"""Active events are serialized into the /state snapshot (game-ui_spec).

The Active Events panel reads `active_events` off the serialized state; the session holds the live
GameEvents but serialize_state previously omitted them (the v1 gap this closes).
"""
from engine.models import Domain, EventEffect, GameEvent, ThePublic, WorldState
from serializer import serialize_game_event, serialize_state


def mk_event(eid, name, effects, cycles=3, target="netmenders"):
    return GameEvent(id=eid, name=name, type="random", trigger="t", target_type="faction",
                     target_id=target, duration=cycles, cycles_remaining=cycles, status="active",
                     effects=effects)


def test_state_includes_active_events():
    storm = mk_event("great_storm", "The Great Storm",
                     [EventEffect(field="withhold", target_id="netmenders", value=0, label="x")])
    world = WorldState(cycle=4)
    data = serialize_state(world, {}, {}, public=ThePublic(), active_events=[storm])
    assert "active_events" in data
    ev = data["active_events"][0]
    assert ev["name"] == "The Great Storm"
    assert ev["cycles_remaining"] == 3
    assert ev["target_id"] == "netmenders"
    assert ev["kind"] == "disaster"


def test_no_active_events_key_when_empty():
    data = serialize_state(WorldState(cycle=1), {}, {}, public=ThePublic(), active_events=[])
    assert "active_events" not in data  # empty list → key omitted (panel shows the calm placeholder)


def test_event_kind_classification():
    disaster = mk_event("d", "D", [EventEffect(field="health", target_id="the_public", value=-5, label="x")])
    boon = mk_event("b", "B", [EventEffect(field="support", target_id="the_public", value=5, label="x")])
    neutral = mk_event("n", "N", [EventEffect(field="rating", target_id="f", value=0, label="x")])
    assert serialize_game_event(disaster)["kind"] == "disaster"
    assert serialize_game_event(boon)["kind"] == "boon"
    assert serialize_game_event(neutral)["kind"] == "neutral"
