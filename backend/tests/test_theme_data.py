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
    # treasury_spec v3 adds the faction-less `civic` ("Public Treasury") lane alongside
    # the 8 Greek faction domains; it has its own properties and is checked separately.
    greek = [d for d in domains if d["id"] in EXPECTED_DOMAIN_IDS]
    assert {d["id"] for d in greek} == EXPECTED_DOMAIN_IDS
    for d in greek:
        assert d["cap"] == 300
        assert d["drift"] == 0.0
        rels = {r["domain_id"]: r["trait"] for r in d["relationships"]}
        # full row: one entry per Greek domain
        assert set(rels) == EXPECTED_DOMAIN_IDS
        # self-entry is Foe, every other domain is Neutral
        assert rels[d["id"]] == "Foe"
        for other_id, trait in rels.items():
            if other_id != d["id"]:
                assert trait == "Neutral"

    # The civic lane: faction-less, authored cap 12, no relationships.
    civic = next(d for d in domains if d["id"] == "civic")
    assert civic["name"] == "Public Treasury"
    assert civic["cap"] == 12
    assert civic["relationships"] == []


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
    # 8 Greek faction domains + the faction-less civic lane (treasury_spec v3).
    assert EXPECTED_DOMAIN_IDS <= set(domains)
    assert "civic" in domains
    assert len(factions) == 41


def test_every_project_uses_a_greek_domain():
    """Base projects are runtime-initiated from the code catalog (projects.json starts
    empty); the catalog must cover exactly the 8 Greek domains and name no legacy one.
    Any pre-loaded projects (e.g. future tax_collection) must also be Greek-domained."""
    from engine.projects import BASE_PROJECT_NAMES
    # 8 Greek domains + civic ("Tax Office") lane (treasury_spec v3).
    assert set(BASE_PROJECT_NAMES) == EXPECTED_DOMAIN_IDS | {"civic"}

    for p in _load("projects.json"):
        for dom in p["domains"]:
            assert dom in EXPECTED_DOMAIN_IDS, f"{p['id']}: legacy domain {dom!r}"
        for eff in p.get("effects", []):
            if eff.get("target") == "domain":
                assert eff["target_id"] in EXPECTED_DOMAIN_IDS, \
                    f"{p['id']}: effect targets legacy domain {eff['target_id']!r}"


def test_no_legacy_domain_prefixes_in_project_ids():
    """Project ids carry no cut/renamed legacy-domain prefix (docks_, noble_houses_, etc.)."""
    legacy_prefixes = (
        "docks_", "noble_houses_", "city_watch_", "underworld_",
        "temple_", "commons_", "arcane_", "registry_",
    )
    projects = _load("projects.json")
    for p in projects:
        assert not p["id"].startswith(legacy_prefixes), f"legacy id prefix: {p['id']}"
