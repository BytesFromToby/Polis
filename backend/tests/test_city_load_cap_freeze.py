"""
test_city_load_cap_freeze.py — /city/load self-heals stale domain caps.

Regression for the "x/300" bug: official templates seeded before the projects-v6
freeze logic stored the placeholder authored cap (300) and no base_cap. The
_refrozen_domains_json helper re-derives base caps from the template's starting
factions at game start, so a stale template still yields the design's derived
cap = round(starting Σlevel × CAP_HEADROOM_MULT).
"""
from __future__ import annotations
import json

from api.routes.city import _refrozen_domains_json
from engine.models import Domain, Faction, Leader
from engine.formulas import base_cap_from_fill, faction_weight
from serializer import serialize_domain, serialize_faction


def _stale_template():
    """A template as old seeds stored it: placeholder authored cap, no base_cap."""
    domains = {
        "harbor": Domain(id="harbor", name="Harbor", cap=300),
        "trade": Domain(id="trade", name="Trade", cap=300),
    }
    domains_json = json.dumps({did: serialize_domain(d) for did, d in domains.items()})
    # Strip base_cap to mimic a pre-freeze seed (serialize always writes it now).
    parsed = json.loads(domains_json)
    for d in parsed.values():
        d.pop("base_cap", None)
    domains_json = json.dumps(parsed)

    factions = {
        "a": Faction(id="a", name="A", domain_primary="harbor", rating=5.0,
                     leader=Leader(name="A")),
        "b": Faction(id="b", name="B", domain_primary="trade", rating=8.0,
                     leader=Leader(name="B")),
    }
    factions_json = json.dumps({fid: serialize_faction(f) for fid, f in factions.items()})
    return domains_json, factions_json


def test_refreeze_replaces_placeholder_cap_with_derived():
    domains_json, factions_json = _stale_template()
    result = json.loads(_refrozen_domains_json(domains_json, factions_json))

    expected_harbor = base_cap_from_fill(faction_weight(5))
    expected_trade = base_cap_from_fill(faction_weight(8))

    assert result["harbor"]["cap"] == expected_harbor
    assert result["harbor"]["base_cap"] == expected_harbor
    assert result["trade"]["cap"] == expected_trade
    assert result["trade"]["base_cap"] == expected_trade
    # The placeholder 300 is gone for every domain.
    assert all(d["cap"] != 300 for d in result.values())
