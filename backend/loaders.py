"""
loaders.py — State loading for the faction simulation (v3).

Public API:
    load_state_from_json(data_dir) -> (WorldState, factions, domains)
    load_domains_from_json(path) -> Dict[str, Domain]
    load_factions_from_json(path) -> Dict[str, Faction]
    load_world_from_json(path) -> WorldState
    load_projects(path=None) -> Dict[str, Project]
"""
from __future__ import annotations
import json
import os
from typing import Dict, Optional, Tuple

from engine.models import (
    Faction, FactionTrait, FactionRelationship,
    Domain, DomainRelationship,
    WorldState, Leader,
    Project, ProjectEffect,
)
from engine.formulas import faction_weight

_DEFAULT_PROJECTS_PATH = os.path.join(os.path.dirname(__file__), "data", "projects.json")


# ── JSON Loaders ──────────────────────────────────────────────────────────────

def load_domains_from_json(path: str) -> Dict[str, Domain]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    result = {}
    for d in data:
        relationships = [
            DomainRelationship(domain_id=r["domain_id"], trait=r["trait"])
            for r in d.get("relationships", [])
        ]
        domain = Domain(
            id=d["id"],
            name=d["name"],
            cap=d["cap"],
            utilization=d.get("utilization", 0.0),
            drift=d.get("drift", 0.0),
            relationships=relationships,
        )
        result[domain.id] = domain
    return result


def load_factions_from_json(path: str) -> Dict[str, Faction]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    result = {}
    for fc in data:
        relationships = [
            FactionRelationship(faction_id=r["faction_id"], trait=r["trait"])
            for r in fc.get("relationships", [])
        ]
        raw_traits = fc.get("traits", [])
        traits = []
        for t in raw_traits:
            if isinstance(t, str):
                traits.append(FactionTrait(trait=t, intensity="moderate"))
            else:
                traits.append(FactionTrait(
                    trait=t["trait"],
                    intensity=t.get("intensity", "moderate"),
                    target_id=t.get("target_id"),
                ))

        # Support both new embedded leader and old leader_id string
        leader_data = fc.get("leader")
        if leader_data:
            leader = Leader(
                name=leader_data["name"],
                traits=leader_data.get("traits", []),
                status=leader_data.get("status", "present"),
                personality_notes=leader_data.get("personality_notes", []),
            )
        elif fc.get("leader_id"):
            leader = Leader(name=str(fc["leader_id"]).replace("_", " ").title())
        else:
            leader = Leader(name=f"Leader of {fc['name']}")
        faction = Faction(
            id=fc["id"],
            name=fc["name"],
            domain_primary=fc["domain_primary"],
            leader=leader,
            rating=fc.get("rating", 1.0),
            health=fc.get("health", 75),
            entrench=fc.get("entrench", 75),
            traits=traits,
            relationships=relationships,
            floor=int(fc.get("rating", 1.0)),
        )
        result[faction.id] = faction
    return result


def load_world_from_json(path: str) -> WorldState:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return WorldState(
        cycle=data.get("cycle", 0),
        chaos=data.get("chaos", {}),
        power_vacuums=data.get("power_vacuums", []),
    )


def _recalculate_utilization(
    factions: Dict[str, Faction],
    domains: Dict[str, Domain],
) -> None:
    for domain_id, domain in domains.items():
        domain.utilization = sum(
            faction_weight(f.floor)
            for f in factions.values()
            if f.domain_primary == domain_id
        )


# ── Top-Level Loader ──────────────────────────────────────────────────────────

def load_state_from_json(
    data_dir: str,
) -> Tuple[WorldState, Dict[str, Faction], Dict[str, Domain]]:
    """
    Load simulation state from a JSON data directory.

    Required files: domains.json, world_state.json
    Optional files: factions.json (generates 2 factions per domain if missing)

    Returns (world, factions, domains) ready to run.
    """
    domains = load_domains_from_json(os.path.join(data_dir, "domains.json"))
    world = load_world_from_json(os.path.join(data_dir, "world_state.json"))

    factions_path = os.path.join(data_dir, "factions.json")
    if os.path.exists(factions_path):
        factions = load_factions_from_json(factions_path)
    else:
        factions = _generate_factions_from_domains(domains)

    _recalculate_utilization(factions, domains)

    return world, factions, domains


def load_projects(path: Optional[str] = None) -> Dict[str, Project]:
    """Load projects from JSON. Returns dict keyed by project id."""
    path = path or _DEFAULT_PROJECTS_PATH
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    result = {}
    for d in data:
        effects = [
            ProjectEffect(
                target=e["target"],
                target_id=e["target_id"],
                field=e["field"],
                value=e["value"],
                condition=e.get("condition", "always"),
            )
            for e in d.get("effects", [])
        ]
        # Support both "domains" (list, current) and "domain" (str, legacy)
        raw = d.get("domains") or ([d["domain"]] if d.get("domain") else [])
        p = Project(
            id=d["id"],
            name=d["name"],
            domains=raw,
            build_cost=d.get("build_cost", 0),
            build_time=d.get("build_time", 1),
            faction_build_actions=d.get("faction_build_actions", 4),
            cycles_built=d.get("cycles_built", 0),
            category=d.get("category", "standard"),
            tax_level=d.get("tax_level", 0),
            status=d.get("status", "under_construction"),
            health=d.get("health", 0),
            effects=effects,
            maintenance_cost=d.get("maintenance_cost", 10),
            initiated_by=d.get("initiated_by", "mayor"),
        )
        result[p.id] = p
    return result


def _generate_factions_from_domains(domains: Dict[str, Domain]) -> Dict[str, Faction]:
    """Generate 2 baseline factions per domain when factions.json is missing."""
    result = {}
    for domain_id, domain in domains.items():
        for suffix, traits_data in [
            ("_order",   [FactionTrait("defensive", "moderate"), FactionTrait("conservative", "moderate")]),
            ("_society", [FactionTrait("ambitious", "moderate"), FactionTrait("opportunistic", "moderate")]),
        ]:
            fid = f"{domain_id}{suffix}"
            fname = f"The {domain.name} {'Order' if 'order' in suffix else 'Society'}"
            result[fid] = Faction(
                id=fid,
                name=fname,
                domain_primary=domain_id,
                leader=Leader(name=f"Leader of {fname}"),
                rating=2.0,
                health=75,
                entrench=75,
                traits=traits_data,
                relationships=[],
                floor=2,
            )
    return result
