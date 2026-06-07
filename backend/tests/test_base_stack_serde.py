"""
BaseProjectStack serialization round-trip (projects_spec v6, Storage).

A stack survives serialize→deserialize unchanged; a snapshot with no `base_stacks`
key deserializes to an empty mapping (older snapshots — caller re-inits per domain).
"""
from engine.models import WorldState
from serializer import (
    serialize_base_stack, deserialize_base_stack,
    serialize_state, deserialize_state,
)
from engine.projects import new_base_stacks


def test_base_stack_round_trip():
    from engine.models import BaseProjectStack
    s = BaseProjectStack(name="Estate", domains=["aristocracy"], count=3,
                         completed=True, progress=60, build_step=25, initiated_by="mayor")
    back = deserialize_base_stack(serialize_base_stack(s))
    assert (back.name, back.domains, back.count, back.completed,
            back.progress, back.build_step, back.initiated_by) == \
           ("Estate", ["aristocracy"], 3, True, 60, 25, "mayor")


def test_state_includes_base_stacks():
    world = WorldState(cycle=0)
    stacks = new_base_stacks({"aristocracy": 1, "harbor": 1})
    stacks["aristocracy"].count = 2
    stacks["aristocracy"].completed = True
    stacks["aristocracy"].progress = 100
    data = serialize_state(world, {}, {}, base_stacks=stacks)
    assert "base_stacks" in data
    _, _, _, _, _, _, restored = deserialize_state(data)
    assert restored["aristocracy"].count == 2
    assert restored["harbor"].count == 0


def test_missing_base_stacks_key_deserializes_empty():
    world = WorldState(cycle=0)
    data = serialize_state(world, {}, {})  # no base_stacks passed
    _, _, _, _, _, _, restored = deserialize_state(data)
    assert restored == {}
