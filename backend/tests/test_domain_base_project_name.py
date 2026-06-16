"""
tests/test_domain_base_project_name.py — Domain serialization exposes base_project_name
(game-ui_spec.md, Mayor Build Project action).

The Build Project dropdown lists each domain alongside its base-project name; that label
rides along on the serialized domain. Also confirms the extra key is harmless on the
snapshot round-trip (deserialize ignores unknown keys).
"""
from __future__ import annotations

from engine.models import Domain
from engine.projects import base_project_name
from serializer import serialize_domain, deserialize_domain


def test_serialize_domain_includes_base_project_name():
    d = Domain(id="port", name="Port", cap=10)
    out = serialize_domain(d)
    assert out["base_project_name"] == "Docks"
    assert out["base_project_name"] == base_project_name("port")


def test_unknown_domain_gets_derived_label():
    d = Domain(id="weird_thing", name="Weird", cap=1)
    assert serialize_domain(d)["base_project_name"] == "Weird Thing Works"


def test_round_trip_ignores_base_project_name():
    d = Domain(id="trade", name="Trade", cap=8, base_cap=4)
    restored = deserialize_domain(serialize_domain(d))
    assert restored.id == "trade"
    assert restored.name == "Trade"
    assert restored.cap == 8
    assert restored.base_cap == 4
