"""
tests/test_faction_descriptions.py — Faction Descriptions feature (faction-descriptions_spec.md).

Slice 1: blurb + description exist on the model, are populated for all 41 factions in
data/factions.json (transcribed from theming.md), and survive the serializer, the loader,
and the official-city seed.
"""
from __future__ import annotations
import json
import os
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from engine.models import Faction, Leader
from serializer import serialize_faction, deserialize_faction
from loaders import load_state_from_json
from db.models import Base, City
from db.seed import seed_official_cities

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")


def _factions_json():
    with open(os.path.join(DATA_DIR, "factions.json"), encoding="utf-8") as f:
        return json.load(f)


# ── model defaults ──────────────────────────────────────────────────────────────

def test_model_defaults_empty():
    f = Faction(id="x", name="X", domain_primary="d", leader=Leader(name="L"))
    assert f.blurb == ""
    assert f.description == ""


# ── data: all 28 populated ───────────────────────────────────────────────────────

def test_all_factions_have_blurb_and_description():
    factions = _factions_json()
    assert len(factions) == 28
    for f in factions:
        assert f.get("blurb", "").strip(), f"{f['id']} missing blurb"
        assert f.get("description", "").strip(), f"{f['id']} missing description"


def test_spot_checks_match_theming():
    by_id = {f["id"]: f for f in _factions_json()}
    eu = by_id["eumelidai"]
    assert "well-flocked" in eu["blurb"]
    assert "senior clan" in eu["description"]
    # silverbench was cut in the roster restructure; spot-check a surviving (new) faction
    mh = by_id["merchant-houses"]
    assert "wholesale traders" in mh["blurb"]
    assert "lifeline" in mh["description"]


# ── serializer round-trip ─────────────────────────────────────────────────────────

def test_serializer_round_trips_descriptions():
    f = Faction(
        id="f1", name="The Guild", domain_primary="trade", leader=Leader(name="Elder Vane"),
        blurb="a short gloss", description="The full identity line.",
    )
    restored = deserialize_faction(serialize_faction(f))
    assert restored.blurb == "a short gloss"
    assert restored.description == "The full identity line."


# ── loader populates ──────────────────────────────────────────────────────────────

def test_loader_populates_descriptions():
    _world, factions, _domains = load_state_from_json(DATA_DIR)
    eu = factions["eumelidai"]
    assert eu.blurb.strip()
    assert "senior clan" in eu.description


# ── seed path carries the fields ─────────────────────────────────────────────────

def test_seed_official_city_carries_descriptions():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()
    try:
        seed_official_cities(db, base_dir=BACKEND_DIR)
        city = db.query(City).filter_by(is_official=True, city_name="Polis").one()
        factions = json.loads(city.factions_json)
        eu = factions["eumelidai"]
        assert eu.get("blurb", "").strip()
        assert "senior clan" in eu.get("description", "")
    finally:
        db.close()
        engine.dispose()


# ── prompt injection ──────────────────────────────────────────────────────────

def _build_prompt(description):
    from engine.llm.prompt_builder import PromptBuilder
    from engine.models import Mayor
    f = Faction(
        id="f1", name="The Guild", domain_primary="trade", leader=Leader(name="Elder Vane"),
        description=description,
    )
    m = Mayor()
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
    return PromptBuilder().build(
        faction=f, run_id="r", mayor=m, db=db, factions={"f1": f}, domains={},
    )


def test_description_present_in_prompt_when_set():
    prompt = _build_prompt("The senior clan: vast estates.")
    assert "The senior clan: vast estates." in prompt


def test_empty_description_omitted_cleanly():
    prompt = _build_prompt("")
    # No leftover description text, and no triple-newline artifact where it would sit.
    assert "The senior clan" not in prompt
    assert "\n\n\n" not in prompt


def _build_prompt_with_leader(personality_notes):
    from engine.llm.prompt_builder import PromptBuilder
    from engine.models import Mayor
    f = Faction(
        id="f1", name="The Guild", domain_primary="trade",
        leader=Leader(name="Elder Vane", personality_notes=personality_notes),
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
    return PromptBuilder().build(faction=f, run_id="r", mayor=Mayor(), db=db, factions={"f1": f}, domains={})


def test_leader_personality_in_prompt_when_set():
    prompt = _build_prompt_with_leader(["Venerable, immovable; sees every change as decay."])
    assert "Venerable, immovable; sees every change as decay." in prompt


def test_leader_personality_absent_when_empty():
    prompt = _build_prompt_with_leader([])
    # The "leader of" sentence is still present, with no trailing personality artifact.
    assert "leader of The Guild." in prompt
    assert "Venerable" not in prompt
