# Phase 2 — Todo
_2026-05-17_

Work through in order. Specs before code. Each spec is the source of truth for the code that follows.

---

## Stage 1 — Archive Old Specs

- [x] Move `Planning/specs/influence-master_spec.md` to `Planning/old_docs/`
- [x] Move `Planning/specs/ui-gamemaster_spec.md` to `Planning/old_docs/`
- [x] Move `Planning/specs/api_spec.md` to `Planning/old_docs/`

---

## Stage 2 — Rewrite Specs

- [x] **Data models spec** — Unit removed, Leader embedded in Faction, FactionTrait with intensity, SM removed
- [x] **Actions spec** — 6 actions, simple d20 contest resolution, no budget system
- [x] **Faction behavior spec** — new spec replacing NPC behavior, personality-driven with trait evolution
- [x] **Cycle runner spec** — faction-only, 9 steps, SM steps removed
- [x] **City generation spec** — no units, leaders generated per faction, starting projects placeholder

---

## Stage 3 — Rewrite Engine Code

### Models
- [x] Delete `Unit` model and all sub-objects (`FactionSlot`, `FocusSlot`, `DomainRating`)
- [x] Remove `spy_gates`, `unstable_domains`, `focus_1`, `focus_2`, `edge`, `grit`, `is_npc` fields
- [x] Add `leader` object to `Faction` (name, traits, personality notes, status)
- [x] Add trait intensity to faction traits
- [x] Add relational traits to faction traits
- [x] Remove `sm_attention`, `sm_state` from `WorldState`
- [x] Remove Social Media from domain list (data file — handled in Data/Seeding step)

### Actions
- [x] Delete Obscure, Expose, Support Faction, Seek Leadership, Join, Leave, Kick resolvers
- [x] Rewrite action resolution — simple contest (faction rating vs target rating)
- [x] Remove exponential L1 budget system
- [x] Remove action level system
- [x] Keep and simplify: Grow, Harm, Block, Protect, Steal, Recruit

### Faction Behavior
- [x] Delete unit action selection logic (`select_npc_actions`)
- [x] Remove focus mechanics (`update_focus_scores`, `add_focus`)
- [x] Remove `TRAIT_WEIGHTS` unit trait table
- [x] Remove SM-specific trait logic (`Named`, `Anonymous`)
- [x] Rewrite `select_faction_action` — personality trait list drives action weights
- [x] Remove spy gate requirement from Harm target selection

### Cycle Runner
- [x] Remove unit declaration phase
- [x] Remove unit resolution phase
- [x] Remove multi-domain health penalty
- [x] Confirm faction declaration → resolution → end-of-cycle structure is clean
- [x] Update `CycleResult` — remove `unit_actions`, `retirements`, `new_units`

### Events / Cascades
- [x] Audit cascade system — remove any unit-specific cascade triggers
- [x] Keep faction collapse, leadership change, world chaos events
- [x] Update leadership change event — leader is now embedded in faction

### Data / Seeding
- [x] Remove `units.json` from city data
- [x] Update `factions.json` — add leader object and personality traits
- [x] Update `world_state.json` — remove SM fields
- [x] Update `domains.json` — remove Social Media entry

### Cleanup
- [x] Delete or archive `engine/npc/` module
- [x] Remove all SM branch logic (`is_sm()` checks) throughout engine
- [x] Remove `level_1_count` from Faction
- [x] Run tests, fix anything broken by removals

---

## Stage 4 — New Specs (Phase 2 Features)

These do not exist yet. Write specs before building.

- [x] **Mayor spec** — actions, action economy, treasury, reputation per faction
- [x] **Personality system spec** — trait intensity, relational traits, trait evolution rules
- [x] **Projects spec** — structure, build cost/time, effects, destruction, starting infrastructure
- [x] **Events spec** — scripted pressure sequences, random events, mayor-triggered events
- [x] **Treasury spec** — income (taxes), expenditure, moneylender, borrowing
- [x] **Special factions spec** — The Public, The Moneylender, External Threats

---

## Stage 5 — Build Phase 2 Features

Blocked until Stage 4 specs are written.

- [x] Personality system — trait intensity, relational traits, evolution
- [x] AI faction behavior — personality drives action selection
- [x] Mayor layer — actions, action economy, treasury, reputation
- [x] Projects — build, complete, destroy
- [x] Events — random, scripted, mayor-triggered
- [x] Special factions — Public, Moneylender, External Threats
- [ ] Visual layer — TBD spec

---

## Notes

- Do not start Stage 3 until Stage 2 specs are approved
- Do not start Stage 5 until Stage 4 specs are written
- API and UI are deferred — not in this todo
