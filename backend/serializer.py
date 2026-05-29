"""
serializer.py — Symmetric serialize/deserialize for all core engine models (v5).

v3: Unit removed. Faction has embedded Leader, FactionTrait list, health.
v4: Mayor, Treasury, Project added.
v5: Project domain→domains list, faction_level. Faction active_block_target. WorldState initiative_order.

Public API:
    serialize_state(world, factions, domains, mayor, treasury, projects) -> dict
    deserialize_state(data) -> (WorldState, factions_dict, domains_dict, mayor, treasury, projects_dict)

    serialize_faction/domain/world_state/cycle_event
    serialize_mayor/treasury/project

    deserialize_* counterparts
"""
from __future__ import annotations
from typing import Dict, Optional, Tuple

from engine.models import (
    Faction, FactionTrait, Leader, FactionRelationship,
    Domain, DomainRelationship,
    WorldState, CycleEvent,
    Mayor, Treasury, Project, ProjectEffect,
    Deal, DealTerm,
)


# ── Sub-object serializers ────────────────────────────────────────────────────

def _ser_leader(leader: Leader) -> dict:
    return {
        "name": leader.name,
        "traits": list(leader.traits),
        "status": leader.status,
        "personality_notes": list(leader.personality_notes),
    }


def _des_leader(d: dict) -> Leader:
    return Leader(
        name=d["name"],
        traits=d.get("traits", []),
        status=d.get("status", "present"),
        personality_notes=d.get("personality_notes", []),
    )


def _ser_faction_trait(t: FactionTrait) -> dict:
    return {"trait": t.trait, "intensity": t.intensity, "target_id": t.target_id}


def _des_faction_trait(d) -> FactionTrait:
    if isinstance(d, str):
        # Backwards compat: plain string trait
        return FactionTrait(trait=d, intensity="moderate")
    return FactionTrait(
        trait=d["trait"],
        intensity=d.get("intensity", "moderate"),
        target_id=d.get("target_id"),
    )


def _ser_faction_relationship(rel: FactionRelationship) -> dict:
    return {"faction_id": rel.faction_id, "trait": rel.trait}


def _des_faction_relationship(d: dict) -> FactionRelationship:
    return FactionRelationship(faction_id=d["faction_id"], trait=d["trait"])


def _ser_domain_relationship(rel: DomainRelationship) -> dict:
    return {"domain_id": rel.domain_id, "trait": rel.trait}


def _des_domain_relationship(d: dict) -> DomainRelationship:
    return DomainRelationship(domain_id=d["domain_id"], trait=d["trait"])


# ── Core entity serializers ───────────────────────────────────────────────────

def serialize_faction(faction: Faction) -> dict:
    return {
        "id": faction.id,
        "name": faction.name,
        "domain_primary": faction.domain_primary,
        "rating": faction.rating,
        "health": faction.health,
        "floor": faction.floor,
        "entrench": faction.entrench,
        "leader": _ser_leader(faction.leader),
        "blurb": faction.blurb,
        "description": faction.description,
        "traits": [_ser_faction_trait(t) for t in faction.traits],
        "relationships": [_ser_faction_relationship(r) for r in faction.relationships],
        "active_block_target": faction.active_block_target,
        "unstable_stacks": faction.unstable_stacks,
        "committed_action": faction.committed_action,
        "committed_target": faction.committed_target,
        "committed_deal_id": faction.committed_deal_id,
        "committed_abstain_action": faction.committed_abstain_action,
        "committed_abstain_target": faction.committed_abstain_target,
    }


def deserialize_faction(d: dict) -> Faction:
    leader_data = d.get("leader")
    leader = _des_leader(leader_data) if leader_data else Leader(name=f"Leader of {d['name']}")
    return Faction(
        id=d["id"],
        name=d["name"],
        domain_primary=d["domain_primary"],
        leader=leader,
        rating=d.get("rating", 1.0),
        health=d.get("health", 75),
        floor=d.get("floor", int(d.get("rating", 1.0))),
        entrench=d.get("entrench", 75),
        traits=[_des_faction_trait(t) for t in d.get("traits", [])],
        relationships=[_des_faction_relationship(r) for r in d.get("relationships", [])],
        blurb=d.get("blurb", ""),
        description=d.get("description", ""),
        active_block_target=d.get("active_block_target", ""),
        unstable_stacks=d.get("unstable_stacks", 0),
        committed_action=d.get("committed_action", ""),
        committed_target=d.get("committed_target", ""),
        committed_deal_id=d.get("committed_deal_id", ""),
        committed_abstain_action=d.get("committed_abstain_action", ""),
        committed_abstain_target=d.get("committed_abstain_target", ""),
    )


def serialize_domain(domain: Domain) -> dict:
    return {
        "id": domain.id,
        "name": domain.name,
        "cap": domain.cap,
        "utilization": domain.utilization,
        "drift": domain.drift,
        "relationships": [_ser_domain_relationship(r) for r in domain.relationships],
    }


def deserialize_domain(d: dict) -> Domain:
    return Domain(
        id=d["id"],
        name=d["name"],
        cap=d["cap"],
        utilization=d.get("utilization", 0.0),
        drift=d.get("drift", 0.0),
        relationships=[_des_domain_relationship(r) for r in d.get("relationships", [])],
    )


def serialize_world_state(world: WorldState) -> dict:
    return {
        "cycle": world.cycle,
        "chaos": dict(world.chaos),
        "power_vacuums": list(world.power_vacuums),
        # initiative_order is cycle-only; not persisted
    }


def deserialize_world_state(d: dict) -> WorldState:
    return WorldState(
        cycle=d.get("cycle", 0),
        chaos=d.get("chaos", {}),
        power_vacuums=d.get("power_vacuums", []),
    )


def serialize_cycle_event(event: CycleEvent) -> dict:
    return {
        "cycle": event.cycle,
        "actor_id": event.actor_id,
        "action": event.action,
        "target_id": event.target_id,
        "domain": event.domain,
        "narrative": event.narrative,
        "dramatic": event.dramatic,
    }


def deserialize_cycle_event(d: dict) -> CycleEvent:
    return CycleEvent(
        cycle=d["cycle"],
        actor_id=d["actor_id"],
        action=d["action"],
        target_id=d.get("target_id"),
        domain=d.get("domain"),
        narrative=d.get("narrative", ""),
        dramatic=d.get("dramatic", 0),
    )


# ── Project serializers ───────────────────────────────────────────────────────

def _ser_project_effect(e: ProjectEffect) -> dict:
    return {
        "target": e.target,
        "target_id": e.target_id,
        "field": e.field,
        "value": e.value,
        "condition": e.condition,
    }


def _des_project_effect(d: dict) -> ProjectEffect:
    return ProjectEffect(
        target=d["target"],
        target_id=d["target_id"],
        field=d["field"],
        value=d["value"],
        condition=d.get("condition", "always"),
    )


def serialize_project(p: Project) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "domains": list(p.domains),
        "build_cost": p.build_cost,
        "build_time": p.build_time,
        "faction_build_actions": p.faction_build_actions,
        "cycles_built": p.cycles_built,
        "category": p.category,
        "tax_level": p.tax_level,
        "faction_level": p.faction_level,
        "status": p.status,
        "health": p.health,
        "effects": [_ser_project_effect(e) for e in p.effects],
        "maintenance_cost": p.maintenance_cost,
        "initiated_by": p.initiated_by,
        # build_actions_this_cycle is cycle-only; not persisted
    }


def deserialize_project(d: dict) -> Project:
    # Backwards compat: old snapshots may have domain (str) instead of domains (list)
    if "domains" in d:
        domains = d["domains"]
    elif "domain" in d:
        domains = [d["domain"]]
    else:
        domains = []
    return Project(
        id=d["id"],
        name=d["name"],
        domains=domains,
        build_cost=d.get("build_cost", 0),
        build_time=d.get("build_time", 1),
        faction_build_actions=d.get("faction_build_actions", 4),
        cycles_built=d.get("cycles_built", 0),
        category=d.get("category", "standard"),
        tax_level=d.get("tax_level", 0),
        faction_level=d.get("faction_level", False),
        status=d.get("status", "under_construction"),
        health=d.get("health", 0),
        effects=[_des_project_effect(e) for e in d.get("effects", [])],
        maintenance_cost=d.get("maintenance_cost", 10),
        initiated_by=d.get("initiated_by", "mayor"),
    )


# ── Treasury serializers ──────────────────────────────────────────────────────

def serialize_treasury(t: Treasury) -> dict:
    return {
        "gold": t.gold,
        "domain_tax_rates": dict(t.domain_tax_rates),
        "debt": t.debt,
        "debt_rate": t.debt_rate,
        "invested": t.invested,
        "invest_cycles_remaining": t.invest_cycles_remaining,
        "invest_return_rate": t.invest_return_rate,
        "income_this_cycle": t.income_this_cycle,
        "expenditure_this_cycle": t.expenditure_this_cycle,
    }


def deserialize_treasury(d: dict) -> Treasury:
    return Treasury(
        gold=d.get("gold", 500),
        domain_tax_rates=d.get("domain_tax_rates", {}),
        debt=d.get("debt", 0),
        debt_rate=d.get("debt_rate", 0.05),
        invested=d.get("invested", 0),
        invest_cycles_remaining=d.get("invest_cycles_remaining", 0),
        invest_return_rate=d.get("invest_return_rate", 0.0),
        income_this_cycle=d.get("income_this_cycle", 0),
        expenditure_this_cycle=d.get("expenditure_this_cycle", 0),
    )


# ── Deal serializers ─────────────────────────────────────────────────────────

def _ser_deal_term(t: DealTerm) -> dict:
    return {"type": t.type, "action": t.action, "target_id": t.target_id, "duration": t.duration}


def _des_deal_term(d: dict) -> DealTerm:
    return DealTerm(
        type=d["type"],
        action=d.get("action", ""),
        target_id=d.get("target_id", ""),
        duration=d.get("duration", 0),
    )


def serialize_deal(deal: Deal) -> dict:
    return {
        "id": deal.id,
        "faction_id": deal.faction_id,
        "mayor_terms": [_ser_deal_term(t) for t in deal.mayor_terms],
        "faction_terms": [_ser_deal_term(t) for t in deal.faction_terms],
        "cycles_remaining": deal.cycles_remaining,
        "total_duration": deal.total_duration,
        "status": deal.status,
        "rep_cost_if_broken": deal.rep_cost_if_broken,
        "cycle_created": deal.cycle_created,
        "suspension_streak": deal.suspension_streak,
    }


def deserialize_deal(d: dict) -> Deal:
    return Deal(
        id=d["id"],
        faction_id=d["faction_id"],
        mayor_terms=[_des_deal_term(t) for t in d.get("mayor_terms", [])],
        faction_terms=[_des_deal_term(t) for t in d.get("faction_terms", [])],
        cycles_remaining=d.get("cycles_remaining", 0),
        total_duration=d.get("total_duration", 0),
        status=d.get("status", "active"),
        rep_cost_if_broken=d.get("rep_cost_if_broken", 20),
        cycle_created=d.get("cycle_created", 0),
        suspension_streak=d.get("suspension_streak", 0),
    )


# ── Mayor serializers ─────────────────────────────────────────────────────────

def serialize_mayor(m: Mayor) -> dict:
    return {
        "action_points": m.action_points,
        "action_cap": m.action_cap,
        "reputation": dict(m.reputation),
        "committed_actions": list(m.committed_actions),
        "cooldowns": dict(m.cooldowns),
        "exemptions": dict(m.exemptions),
        "deals": {did: serialize_deal(d) for did, d in m.deals.items()},
    }


def deserialize_mayor(d: dict) -> Mayor:
    return Mayor(
        action_points=d.get("action_points", 0),
        action_cap=d.get("action_cap", 6),
        reputation=d.get("reputation", {}),
        committed_actions=d.get("committed_actions", []),
        cooldowns=d.get("cooldowns", {}),
        exemptions=d.get("exemptions", {}),
        deals={did: deserialize_deal(v) for did, v in d.get("deals", {}).items()},
    )


# ── Full state snapshot ───────────────────────────────────────────────────────

def serialize_state(
    world: WorldState,
    factions: Dict[str, Faction],
    domains: Dict[str, Domain],
    mayor: Optional[Mayor] = None,
    treasury: Optional[Treasury] = None,
    projects: Optional[Dict[str, Project]] = None,
) -> dict:
    data = {
        "world": serialize_world_state(world),
        "factions": {fid: serialize_faction(f) for fid, f in factions.items()},
        "domains": {did: serialize_domain(d) for did, d in domains.items()},
    }
    if mayor is not None:
        data["mayor"] = serialize_mayor(mayor)
    if treasury is not None:
        data["treasury"] = serialize_treasury(treasury)
    if projects is not None:
        data["projects"] = {pid: serialize_project(p) for pid, p in projects.items()}
    return data


def deserialize_state(
    data: dict,
) -> Tuple[WorldState, Dict[str, Faction], Dict[str, Domain], Optional[Mayor], Optional[Treasury], Dict[str, Project]]:
    world = deserialize_world_state(data["world"])
    factions = {fid: deserialize_faction(f) for fid, f in data.get("factions", {}).items()}
    domains = {did: deserialize_domain(d) for did, d in data.get("domains", {}).items()}
    mayor = deserialize_mayor(data["mayor"]) if "mayor" in data else None
    treasury = deserialize_treasury(data["treasury"]) if "treasury" in data else None
    projects = {pid: deserialize_project(p) for pid, p in data.get("projects", {}).items()}
    return world, factions, domains, mayor, treasury, projects
