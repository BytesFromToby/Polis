# Long-Term Goals
_Last updated: 2026-03-31_

---

## Where We Are Now

The simulation engine (Rivers Point) is a headless Python CLI. It runs faction and NPC behavior across a city, tracking influence, leadership, health decay, cascades, and collapse. It produces a narrative log and a system log. It is functional and tested but has no interface — a developer tool, not a user tool.

The engine is the foundation for everything below. All three phases share it. What changes between phases is the surface built on top of it.

---

## Phase 1 — Tabletop RPG GM Tool

**Goal:** A solo GM tool for running a living city as inspiration and backstory engine for a tabletop campaign.

**The problem it solves:** GMs running city-based campaigns carry the political landscape in their heads. Factions shift, NPCs rise and fall, but the GM has to manually track all of it between sessions. This tool runs that simulation automatically and hands the GM a readable account of what happened.

**Who uses it:** One person. The GM. No player-facing layer needed.

**Core features:**
- City builder — input domains, factions, and named NPCs through a simple interface
- Cycle runner — run one or more cycles and see what happened
- Narrative output — readable event summaries a GM can mine for plot hooks, not a dev log
- Save/load cities — persist a city between sessions
- Manual intervention — GM can adjust faction health, remove a unit, trigger an event before running a cycle

**What "done" looks like:** A GM can build a city in an evening, run it between sessions, and walk away with three things they didn't expect that make the next session richer.

**Interface:** Desktop app or well-packaged local web UI. Does not require a server. Single player, single city.

**Engine changes needed:**
- Narrative output quality — current log is functional but written for debugging, not storytelling
- Cycle summary report — a clean end-of-cycle digest, not a raw event stream
- City builder input layer — currently requires hand-editing JSON

---

## Phase 2 — LARP GM and Player Tool

**Goal:** A web portal for chronicle-level World of Darkness (or similar) LARP. GMs manage a living city. Players manage their own units and submit downtime actions. The cycle adjudicates everything and the GM controls what information reaches each player.

**The problem it solves:** WoD LARP GMs run complex political downtime between sessions — influence actions, faction maneuvering, NPC interactions — mostly in their heads or in spreadsheets. Players submit actions by email. Results are inconsistent, opaque, and labor-intensive for the GM.

**Who uses it:** Two roles — GM and Player. Multiple players per city. Potentially multiple cities running simultaneously.

**Core features:**

_GM side:_
- City builder and editor (carries forward from Phase 1)
- Cycle trigger — GM decides when to run a cycle
- Post-cycle review dashboard — see all events, decide what to release
- LARP action queue — review player LARP actions with mechanical context from the cycle
- Information control — mark events as visible to all, visible to specific players, or GM-only
- Player management — create player accounts, assign units

_Player side:_
- Unit dashboard — view your units, their domain ratings, faction standing
- Action submission — two types:
  - **Cycle Actions** — standard engine actions (Harm, Block, Support, Grow, etc.) that feed directly into the cycle
  - **LARP Actions** — narrative intent declarations ("I want to meet with the faction leader") that the cycle can mechanically affect but the GM adjudicates
- Results inbox — receive what the GM has released to you after a cycle

_LARP Action flow:_
1. Player submits a LARP action before the cycle runs
2. Cycle runs — mechanical effects (Block, Harm, etc.) can affect whether the action lands
3. GM reviews LARP action queue post-cycle, seeing the action alongside what happened to that player mechanically
4. GM decides outcome and releases result to player

**Infrastructure:**
- Web portal with login and role management (GM / Player)
- Multi-tenancy — each city is isolated, multiple cities can run simultaneously
- Engine runs as a backend service, cycle triggered by GM or on schedule
- Per-city cycle schedule (GM-controlled, not time-based — downtime aligns with game sessions)

**Engine changes needed:**
- Player action input layer — cycle must accept externally submitted actions alongside NPC behavior
- Permission layer on events — each result tagged with visibility
- Multi-city isolation

---

## Phase 3 — Video Game World Engine

**Goal:** The simulation engine as an embedded backend for a video game — running faction politics, NPC histories, and city dynamics beneath the surface. The player experiences the consequences without seeing the machinery.

**The problem it solves:** Living worlds in games are usually scripted or shallow. Factions follow fixed scripts, NPCs have no real history, and the political landscape doesn't change unless the player drives it. This engine makes the world move on its own.

**Reference points:** Dwarf Fortress (off-screen simulation), Kenshi (faction warfare and territory), Crusader Kings (character-driven political simulation). The engine already does a version of what those games do.

**Who uses it:** Game developers integrating the engine, and indirectly their players.

**Core features:**
- Stable, documented API — game queries the engine for state, submits player actions, advances cycles
- Performance at scale — more factions, more units, longer runs than current test scope
- Event hooks — game subscribes to engine events (faction collapses, leadership changes, cascades) and triggers in-game consequences
- Serialization — full save/load of engine state for game save systems
- Configurable ruleset — game can tune weights, thresholds, and action pools without touching engine internals

**Engine changes needed:**
- API layer (currently a CLI, needs to be callable as a library or service)
- Performance profiling and optimization
- Configuration system for ruleset customization
- Formal event subscription model

---

## Shared Engine Priorities (All Phases)

These engine improvements unblock all three phases:

1. **Action economy rework** — current `int()` truncation means most actions floor to zero. Fix proportional distribution so all actions fire at their intended frequency. _(Backlog item 4)_
2. **Narrative output quality** — events are logged for debugging. Rewrite narrative templates to be GM/player readable.
3. **Faction relationships** — Foe/Ally defined but never consumed. Should affect target selection and action weights. _(Backlog item 3)_
4. **City builder input** — currently hand-edited JSON. Needs at minimum a structured input format, eventually a UI.

---

## What Stays the Same

The simulation engine core does not change between phases. Factions, domains, units, actions, cascades, health decay, collapse — all of that is Phase 1 through Phase 3. The investment in the engine now pays forward across all three products.
