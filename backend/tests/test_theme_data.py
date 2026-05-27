"""
test_theme_data.py — Pins the Greek theme seed data (theme-conversion spec, Feature: Greek seed data).
Verifies domains.json / factions.json structure, counts, ids, and that the loader accepts them.
"""
import sys, os, json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import loaders

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

EXPECTED_DOMAIN_IDS = {
    "aristocracy", "guilds", "trade", "professions",
    "temples", "military", "academy", "harbor",
}

EXPECTED_FACTION_COUNTS = {
    "aristocracy": 3, "guilds": 10, "trade": 5, "professions": 6,
    "temples": 5, "military": 4, "academy": 4, "harbor": 4,
}

FUNCTIONAL_TRAITS = {
    "aggressive", "defensive", "ambitious", "paranoid", "opportunistic",
    "expansionary", "conservative", "corrupt", "industrious", "destructive",
}
VALID_INTENSITIES = {"slight", "moderate", "strong", "very"}


def _load(name):
    with open(os.path.join(DATA_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def test_eight_domains_with_default_values():
    domains = _load("domains.json")
    assert len(domains) == 8
    assert {d["id"] for d in domains} == EXPECTED_DOMAIN_IDS
    for d in domains:
        assert d["cap"] == 300
        assert d["drift"] == 0.0
        rels = {r["domain_id"]: r["trait"] for r in d["relationships"]}
        # full row: one entry per domain
        assert set(rels) == EXPECTED_DOMAIN_IDS
        # self-entry is Foe, every other domain is Neutral
        assert rels[d["id"]] == "Foe"
        for other_id, trait in rels.items():
            if other_id != d["id"]:
                assert trait == "Neutral"


def test_forty_one_factions_assigned_to_real_domains():
    factions = _load("factions.json")
    assert len(factions) == 41
    counts = {}
    for f in factions:
        assert f["domain_primary"] in EXPECTED_DOMAIN_IDS
        counts[f["domain_primary"]] = counts.get(f["domain_primary"], 0) + 1
    assert counts == EXPECTED_FACTION_COUNTS


def test_every_faction_trait_is_functional():
    factions = _load("factions.json")
    for f in factions:
        assert f["traits"], f"{f['id']} has no traits"
        for t in f["traits"]:
            assert t["trait"] in FUNCTIONAL_TRAITS, f"{f['id']}: bad trait {t['trait']}"
            assert t["intensity"] in VALID_INTENSITIES, f"{f['id']}: bad intensity {t['intensity']}"


def test_loader_accepts_greek_data():
    world, factions, domains = loaders.load_state_from_json(DATA_DIR)
    assert len(domains) == 8
    assert len(factions) == 41
