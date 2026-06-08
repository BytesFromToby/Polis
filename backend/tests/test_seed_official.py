"""
tests/test_seed_official.py — Pins the official-city seeding for the Greek theme
(theme-conversion spec, Features: Single official city; Clear old saved games).

Seeds into a fresh in-memory DB and asserts the only official city is the Greek "Polis",
carrying the eight Greek domains and 41 factions, with no legacy-theme ids present.
"""
from __future__ import annotations
import sys, os, json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db.models import Base, City
from db.seed import seed_official_cities

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EXPECTED_DOMAIN_IDS = {
    "aristocracy", "guilds", "trade", "professions",
    "temples", "military", "academy", "harbor",
}

LEGACY_DOMAIN_IDS = {
    # Twin Cities placeholder
    "traditional_media", "political", "street", "high_society", "bureaucracy",
    "university", "police", "finance", "legal", "health", "industry",
    "transportation", "religion", "underworld",
    # legacy medieval river-port set
    "docks", "noble_houses", "city_watch", "commons", "arcane", "registry", "temple",
}


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()


def test_seeds_single_official_polis(db):
    seeded = seed_official_cities(db, base_dir=BACKEND_DIR)
    assert seeded == 1
    official = db.query(City).filter_by(is_official=True).all()
    assert len(official) == 1
    assert official[0].city_name == "Polis"


def test_seeded_polis_has_greek_roster(db):
    seed_official_cities(db, base_dir=BACKEND_DIR)
    city = db.query(City).filter_by(is_official=True).one()
    domains = json.loads(city.domains_json)
    factions = json.loads(city.factions_json)
    # 8 Greek faction domains + the faction-less civic lane (treasury_spec v3).
    assert set(domains.keys()) == EXPECTED_DOMAIN_IDS | {"civic"}
    assert len(factions) == 41


def test_no_legacy_domain_ids_in_db(db):
    seed_official_cities(db, base_dir=BACKEND_DIR)
    for city in db.query(City).all():
        domains = json.loads(city.domains_json)
        assert not (set(domains.keys()) & LEGACY_DOMAIN_IDS), \
            f"legacy domain ids leaked into {city.city_name}"
