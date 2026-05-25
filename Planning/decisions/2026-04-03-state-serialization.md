# Decision: State Serialization Layer

**Date:** 2026-04-03
**Status:** Accepted

## Context

The engine runs entirely in Python dataclasses. The API needs to return state to the Vue frontend as JSON, and SQLite needs to store full cycle snapshots. No serialization utility exists yet.

## Decision

Add `scr/serializer.py` — a single module with symmetric serialize/deserialize functions for every core model.

### Scope
- Serialize: `Unit`, `Faction`, `Domain`, `WorldState`, `CycleEvent`
- Top-level: `serialize_state()` / `deserialize_state()` for full snapshots
- Cycle-only fields are excluded from serialization (reset each cycle anyway)

### Persistent fields serialized per model

**Unit:** id, name, traits, edge, grit, health, is_leader, is_npc, domains, faction_1/2/3, focus_1/2, spy_gates, unstable_domains

**Faction:** id, name, domain_primary, rating, floor, entrench, leadership_need, leader_id, member_ids, level_1_count, traits, relationships, unstable_stacks

**Domain:** id, name, cap, utilization, drift, relationships

**WorldState:** cycle, chaos, power_vacuums, sm_attention, sm_state

**CycleEvent:** all fields (cycle, actor_id, action, target_id, domain, domain_targeted, points, narrative, dramatic)

### Excluded (cycle-only)
Unit: action_taken, supported_faction, obscure_levels, cycle_protect_level
Faction: leaderless_proxy_id, action_taken

## Rationale

A dedicated serializer module keeps the engine models clean (no to_dict methods) and gives the API and DB layers a single authoritative source for how state is encoded. Symmetric functions mean any state snapshot can round-trip without loss.

## Consequences

- API routes can call `serialize_state()` and return the result directly
- SQLite cycle snapshots store the output of `serialize_state()`
- Restoring a sim from a snapshot calls `deserialize_state()`
