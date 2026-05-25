"""
validate_state.py — Check data integrity of JSON state files.

Validates:
  - JSON files parse correctly
  - Faction member_ids reference existing unit IDs
  - Unit faction slots reference existing faction IDs
  - Leader IDs reference existing units that are members
  - Domain IDs referenced in units/factions exist in domains.json
  - Edge + grit = 20 for all units
  - Health in valid range (1-100)
  - Rating >= 1.0 for all domain ratings
  - Entrench in valid range (0.0-1.0 for units, 1-100 for factions)
  - No duplicate IDs

Usage:
    python city_sim_Project/tools/validate_state.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / "backend" / "data"

DOMAINS_JSON = DATA_DIR / "domains.json"
FACTIONS_JSON = DATA_DIR / "factions.json"
UNITS_JSON = DATA_DIR / "units.json"
WORLD_JSON = DATA_DIR / "world_state.json"


def _load_json(path: Path) -> Tuple[dict | list | None, str | None]:
    """Try to load a JSON file. Returns (data, error_message)."""
    if not path.exists():
        return None, f"File not found: {path}"
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f), None
    except json.JSONDecodeError as e:
        return None, f"JSON parse error in {path.name}: {e}"


class ValidationResult:
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []

    def error(self, msg: str):
        self.errors.append(msg)

    def warn(self, msg: str):
        self.warnings.append(msg)

    def log(self, msg: str):
        self.info.append(msg)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def validate() -> ValidationResult:
    r = ValidationResult()

    # Load files
    domains_data, err = _load_json(DOMAINS_JSON)
    if err:
        r.error(err)
    factions_data, err = _load_json(FACTIONS_JSON)
    if err:
        r.error(err)
    units_missing = False
    units_data, err = _load_json(UNITS_JSON)
    if err:
        r.warn(f"{err} (units may be DB-only or generated at runtime)")
        r.warn("Skipping unit-dependent cross-checks")
        units_data = []
        units_missing = True
    world_data, err = _load_json(WORLD_JSON)
    if err:
        r.error(err)

    if not r.ok:
        return r

    # Build ID sets
    domain_ids = set()
    if isinstance(domains_data, list):
        for d in domains_data:
            did = d.get("id", "")
            if did in domain_ids:
                r.error(f"Duplicate domain ID: {did}")
            domain_ids.add(did)
        r.log(f"Domains: {len(domain_ids)} loaded")
    elif isinstance(domains_data, dict):
        domain_ids = set(domains_data.keys())
        r.log(f"Domains: {len(domain_ids)} loaded (dict format)")

    unit_ids = set()
    units_list = units_data if isinstance(units_data, list) else list(units_data.values()) if isinstance(units_data, dict) else []
    for u in units_list:
        uid = u.get("id", "")
        if uid in unit_ids:
            r.error(f"Duplicate unit ID: {uid}")
        unit_ids.add(uid)
    r.log(f"Units: {len(unit_ids)} loaded")

    faction_ids = set()
    factions_list = factions_data if isinstance(factions_data, list) else list(factions_data.values()) if isinstance(factions_data, dict) else []
    for f in factions_list:
        fid = f.get("id", "")
        if fid in faction_ids:
            r.error(f"Duplicate faction ID: {fid}")
        faction_ids.add(fid)
    r.log(f"Factions: {len(faction_ids)} loaded")

    # Validate units
    for u in units_list:
        uid = u.get("id", "?")
        name = u.get("name", uid)

        # Edge + grit = 20
        edge = u.get("edge", 10)
        grit = u.get("grit", 10)
        if edge + grit != 20:
            r.error(f"Unit {name}: edge({edge}) + grit({grit}) = {edge+grit}, expected 20")

        # Health range
        health = u.get("health", 75)
        if not (1 <= health <= 100):
            r.error(f"Unit {name}: health={health} out of range [1,100]")

        # Domain ratings
        domains = u.get("domains", [])
        for dr in domains:
            did = dr.get("domain_id", "")
            if did and did not in domain_ids:
                r.error(f"Unit {name}: references unknown domain '{did}'")
            rating = dr.get("rating", 1.0)
            if rating < 1.0:
                r.error(f"Unit {name}: domain {did} rating={rating} < 1.0")
            entrench = dr.get("entrench", 0.0)
            if not (0.0 <= entrench <= 1.0):
                r.error(f"Unit {name}: domain {did} entrench={entrench} out of [0.0, 1.0]")

        # Faction slot references
        for slot_key in ["faction_1", "faction_2", "faction_3"]:
            slot = u.get(slot_key)
            if slot and isinstance(slot, dict):
                fid = slot.get("faction_id", "")
                if fid and fid not in faction_ids:
                    r.error(f"Unit {name}: {slot_key} references unknown faction '{fid}'")

        # Traits count
        traits = u.get("traits", [])
        if len(traits) > 5:
            r.warn(f"Unit {name}: has {len(traits)} traits (spec says 1-5)")

    # Validate factions
    for f in factions_list:
        fid = f.get("id", "?")
        fname = f.get("name", fid)

        # Domain primary exists
        dprimary = f.get("domain_primary", "")
        if dprimary and dprimary not in domain_ids:
            r.error(f"Faction {fname}: domain_primary '{dprimary}' not in domains")

        # Leader exists and is a member
        leader = f.get("leader_id")
        members = f.get("member_ids", [])
        if leader and not units_missing:
            if leader not in unit_ids:
                r.error(f"Faction {fname}: leader '{leader}' not in units")
            if leader not in members:
                r.warn(f"Faction {fname}: leader '{leader}' not in member_ids")

        # Members exist
        if not units_missing:
            for mid in members:
                if mid not in unit_ids:
                    r.error(f"Faction {fname}: member '{mid}' not in units")

        # Entrench range
        entrench = f.get("entrench", 75)
        if not (1 <= entrench <= 100):
            r.error(f"Faction {fname}: entrench={entrench} out of [1, 100]")

        # Rating
        rating = f.get("rating", 1.0)
        if rating < 1.0:
            r.error(f"Faction {fname}: rating={rating} < 1.0")

        # Leadership need
        ln = f.get("leadership_need", 0.0)
        if ln < 0 or ln > 20:
            r.warn(f"Faction {fname}: leadership_need={ln} out of [0, 20]")

    # Cross-check: unit faction slots should match faction member_ids
    unit_faction_map = {}
    for u in units_list:
        uid = u.get("id", "?")
        for slot_key in ["faction_1", "faction_2", "faction_3"]:
            slot = u.get(slot_key)
            if slot and isinstance(slot, dict):
                fid = slot.get("faction_id", "")
                if fid:
                    unit_faction_map.setdefault(uid, []).append(fid)

    for u in units_list:
        uid = u.get("id", "?")
        name = u.get("name", uid)
        for fid in unit_faction_map.get(uid, []):
            # Find the faction
            faction = next((f for f in factions_list if f.get("id") == fid), None)
            if faction and uid not in faction.get("member_ids", []):
                r.warn(f"Unit {name}: has faction slot for '{fid}' but not in that faction's member_ids")

    for f in factions_list:
        fid = f.get("id", "?")
        fname = f.get("name", fid)
        for mid in f.get("member_ids", []):
            if mid in unit_ids:
                member_factions = unit_faction_map.get(mid, [])
                if fid not in member_factions:
                    r.warn(f"Faction {fname}: lists member '{mid}' but unit has no faction slot for it")

    return r


def main():
    print("City Sim State Validator")
    print("=" * 40)
    print(f"Data dir: {DATA_DIR}\n")

    result = validate()

    for msg in result.info:
        print(f"  INFO: {msg}")

    if result.warnings:
        print(f"\nWarnings ({len(result.warnings)}):")
        for msg in result.warnings:
            print(f"  WARN: {msg}")

    if result.errors:
        print(f"\nErrors ({len(result.errors)}):")
        for msg in result.errors:
            print(f"  ERROR: {msg}")
    else:
        print("\nNo errors found.")

    print(f"\n{'PASS' if result.ok else 'FAIL'} — {len(result.errors)} errors, {len(result.warnings)} warnings")
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
