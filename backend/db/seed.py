"""
db/seed.py — Seed official city templates into the DB at server startup.

Reads JSON data directories from SEED_CITIES and inserts them as
is_official=True City rows if they don't already exist (keyed by city_name).
"""
from __future__ import annotations
import json
import os
from typing import NamedTuple

from sqlalchemy.orm import Session

from db.models import City
from loaders import load_state_from_json
from serializer import serialize_faction, serialize_domain, serialize_world_state


class _CityDef(NamedTuple):
    city_name: str
    description: str
    data_dir: str


_OFFICIAL_CITIES: list[_CityDef] = [
    _CityDef(
        city_name="Polis",
        description="An ancient-Greek city-state of six domains: aristocracy, guilds, the "
                    "port, the professions, temples, and military (plus the civic treasury).",
        data_dir="data",
    ),
]

# Domain ids cut/renamed by the roster restructure — an official template carrying any of
# these is stale and gets refreshed in place.
_STALE_DOMAIN_MARKERS = {"trade", "academy", "harbor"}


def _is_stale(city: City) -> bool:
    try:
        return bool(set(json.loads(city.domains_json)) & _STALE_DOMAIN_MARKERS)
    except (ValueError, TypeError):
        return False


def seed_official_cities(db: Session, base_dir: str = ".") -> int:
    seeded = 0

    for city_def in _OFFICIAL_CITIES:
        existing = db.query(City).filter_by(
            city_name=city_def.city_name, is_official=True
        ).first()
        # A current official template is left alone; a stale one (old roster) is refreshed in
        # place below. User-created cities (is_official=False) are never touched.
        if existing and not _is_stale(existing):
            continue

        data_dir = os.path.join(base_dir, city_def.data_dir)

        try:
            world, factions, domains = load_state_from_json(data_dir)
        except FileNotFoundError as e:
            print(f"[seed] WARNING: Could not load '{city_def.city_name}': {e}")
            continue

        domains_json = json.dumps({did: serialize_domain(d) for did, d in domains.items()})
        factions_json = json.dumps({fid: serialize_faction(f) for fid, f in factions.items()})
        world_state_json = json.dumps(serialize_world_state(world))

        if existing:  # stale official template → refresh in place (keeps its id; FK-safe)
            existing.domains_json = domains_json
            existing.factions_json = factions_json
            existing.world_state_json = world_state_json
            existing.description = city_def.description
        else:
            db.add(City(
                city_name=city_def.city_name,
                author="official",
                description=city_def.description,
                setting="Greek",
                details="",
                is_official=True,
                published=True,
                domains_json=domains_json,
                factions_json=factions_json,
                world_state_json=world_state_json,
            ))
        seeded += 1

    if seeded:
        db.commit()

    return seeded
