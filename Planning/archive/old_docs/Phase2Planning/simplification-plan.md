# Simplification Plan — Phase 2 Rebuild
_2026-05-17_

The engine was built for human players managing units in a LARP. The new game has no human-managed units. Most of the complexity exists to create fair counterplay between humans. This document defines what gets cut, what gets changed, and what stays.

---

## Cut Entirely

### Units
- Remove the `Unit` model and everything that depends on it
- No individual NPC tracking, no named units, no unit actions
- The leader lives on the faction (see below)

### LARP / Influence Master system
- `influence-master_spec.md` is obsolete — delete
- Multi-tenancy, player accounts, `city_members` table, LARP mode — all gone
- The original purpose of the project is retired

### GM Tool UI
- `ui-gamemaster_spec.md` is obsolete — delete
- All GM screen designs, city builder UI, login/register flows — gone
- The interface will be redesigned from scratch for the mayor game

### API layer (current)
- `api_spec.md` was built around the GM/LARP flow — obsolete
- API will be rethought once core engine is stable

### Social Media domain
- Remove `sm_attention`, `sm_state`, all SM-specific logic
- Remove SM-specific unit traits (`Named`, `Anonymous`)
- Remove the `is_sm()` check and all SM branch logic throughout the engine
- Modern setting artifact — not relevant to the new city

### Spy gate system
- Remove `spy_gates` from units (units are gone anyway)
- Remove all Harm gates that required prior Expose
- Was a player-vs-player fairness mechanic — not needed for AI vs AI

### Obscure / Expose actions
- Remove both actions entirely
- Were built for information asymmetry between human players
- AI factions have no need for hidden action mechanics

### Three faction slots per unit
- Moot — units are gone
- Factions will be singular, self-contained entities

### Focus slots
- Remove `focus_1`, `focus_2`, inertia comparisons, decay mechanics
- AI personality traits replace this — behavior is driven by faction personality, not accumulated focus scores

### Multi-domain health penalty
- Remove — units are gone

---

## Changed

### Leader moves into Faction
- `Faction` gains a `leader` object (name, traits, personality notes)
- Leader is no longer a separate `Unit` — it is a named character embedded in the faction
- Leader traits influence faction behavior directly
- Leader can change — replacement is a faction event, not a unit action
- Leader health/status tracked on the faction (present, weakened, absent)

### Faction traits → Personality system
- Existing `faction.traits` list becomes the foundation for the new personality system
- Traits gain **intensity** (slight / moderate / strong / very)
- Traits can be **relational** — targeted at another faction ("distrusts The Traders Compact")
- Traits evolve over time based on events
- AI reads trait list each cycle to weight faction decisions
- Replace `FACTION_TRAIT_WEIGHTS` static table with AI-interpreted personality

### Action economy — simplify
- Remove exponential L1 budget system
- Remove action levels (L1–L5)
- Factions take one action per cycle, weighted by personality traits
- Action resolution: simple contest — faction rating vs target rating, d20 style
- Keep: Grow, Harm, Block, Protect, Steal, Recruit as core action set
- Cut: Obscure, Expose, Support Faction, Seek Leadership (replaced by faction events), Join, Leave, Kick

### Domains — trim
- Remove Social Media domain
- Remaining domains serve the medieval/fantasy city setting
- Review domain list against new city concept — reduce if needed

### WorldState — simplify
- Remove `sm_attention`, `sm_state`
- Keep: `cycle`, `chaos`, `power_vacuums`
- Add: city-level stats (safety, prosperity, public mood) — TBD specifics

---

## Keep

- `Faction` model core — id, name, domain_primary, rating, health, entrench
- `Domain` model — cap, utilization, drift, relationships
- `FactionRelationship` / `DomainRelationship` — inter-faction and inter-domain dispositions
- Cycle runner structure — declaration, resolution, end-of-cycle
- Cascade / event system — the engine's best feature
- Health decay and faction collapse mechanics
- Grow / Harm / Block / Protect / Steal as the core action vocabulary
- `CycleEvent` and narrative log output

---

## What This Unlocks

- Engine is small enough to reason about cleanly
- AI personality system has less noise to work through
- Faction is now a self-contained agent — leader + traits + rating + relationships
- Mayor layer can be added on top of a clean foundation
- Projects, treasury, events all have clear attachment points

---

## Files to Archive / Delete

| File | Action |
|------|--------|
| `Planning/specs/influence-master_spec.md` | Archive |
| `Planning/specs/ui-gamemaster_spec.md` | Archive |
| `Planning/specs/api_spec.md` | Archive — rewrite later |
| `Planning/specs/npc-behavior-engine_spec.md` | Rewrite — units gone, AI personality replaces |
| `Planning/specs/data-models_spec.md` | Rewrite — Unit removed, Faction expanded |
| `Planning/specs/actions_spec.md` | Rewrite — simplified action set |
