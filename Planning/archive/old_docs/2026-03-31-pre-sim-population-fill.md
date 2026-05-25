# Decision: Pre-Sim Population Fill

**Date:** 2026-03-31
**Status:** Accepted

---

## Context

Starting data files (`units.json`, `factions.json`) contain only named, hand-placed
characters — faction leaders and key figures. Each faction starts with only its leader
as a member.

This causes rapid leadership collapse: when a leader retires or leaves in the first few
cycles, the faction drops to zero members and immediately goes leaderless. There is no
bench to absorb the loss.

The engine already has a unit generator (`generate_unit_random`) that produces anonymous
background units during the run. Factions also have a capacity derived from their rating
(`get_faction_capacity`). A faction at rating 6.0 can hold 32 weight-units of members —
starting with 1 member is not a realistic baseline.

---

## Decision

Add a **pre-sim population fill** step that runs once at startup, after loading the JSON
data and before cycle 1.

The fill pass:
1. Uses the existing `generate_unit_random()` to create background units
2. Assigns them to factions by directly setting faction membership and a FactionSlot
3. Fills each faction to approximately **40% of capacity** by weight
4. Stops if capacity would be exceeded

Generated units are **ephemeral** — they exist only in memory for that run. The JSON
files are never written to. Every run starts fresh from the named characters only.

---

## Rationale

- Named characters (leaders) stay permanent and hand-crafted in the JSON
- Background population is treated the same as mid-run generated units — same function,
  same stat ranges, same randomness
- Starting at ~40% capacity gives factions a realistic bench without being over-full,
  leaving room for organic growth and recruitment during the run
- Keeps starting data files clean and human-readable

---

## Consequences

- Leadership loss no longer immediately collapses a faction
- Run-to-run variation in background population (unless seeded)
- Starting unit count will vary based on faction ratings and random seed
- No change to the JSON data format or the engine itself — change is isolated to main.py
