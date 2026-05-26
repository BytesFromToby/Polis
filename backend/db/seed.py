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
        city_name="Unnamed Polis",
        description="The default world. Faction and domain roster pending the "
                    "ancient-Greek re-theme; loaded from data/.",
        data_dir="data",
    ),
    _CityDef(
        city_name="Rivers Point",
        description="A river trading city of nine domains: guilds, docks, noble houses, "
                    "city watch, underworld, temple, commons, arcane, and registry.",
        data_dir="data/past_cities/Rivers_Point",
    ),
]


def seed_official_cities(db: Session, base_dir: str = ".") -> int:
    seeded = 0

    for city_def in _OFFICIAL_CITIES:
        existing = db.query(City).filter_by(
            city_name=city_def.city_name, is_official=True
        ).first()
        if existing:
            continue

        data_dir = os.path.join(base_dir, city_def.data_dir)

        try:
            world, factions, domains = load_state_from_json(data_dir)
        except FileNotFoundError as e:
            print(f"[seed] WARNING: Could not load '{city_def.city_name}': {e}")
            continue

        city = City(
            city_name=city_def.city_name,
            author="official",
            description=city_def.description,
            setting="DnD",
            details="",
            is_official=True,
            published=True,
            domains_json=json.dumps({did: serialize_domain(d) for did, d in domains.items()}),
            factions_json=json.dumps({fid: serialize_faction(f) for fid, f in factions.items()}),
            world_state_json=json.dumps(serialize_world_state(world)),
        )
        db.add(city)
        seeded += 1

    if seeded:
        db.commit()

    return seeded
