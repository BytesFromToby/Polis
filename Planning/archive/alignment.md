# Alignment Log

Audit trail for the spec/reference restructure (Phase 2, started 2026-05-25).
This project has no git history, so this file *is* the undo record: whenever the
restructure **removes or replaces content**, the original is copied here first,
with its source and the reason. Structural moves (file relocations, retitles,
re-tiers) are logged too, so the before-state is always recoverable.

Read this top-down as a journal; newest entries at the bottom of each section.

---

## Structural moves & re-tiers

| Date | What | From → To | Notes |
|------|------|-----------|-------|
| 2026-05-25 | Archive legacy doc pile | `Planning/old_docs/` → `Planning/archive/old_docs/` (25 items) | Phase 1 |
| 2026-05-25 | Archive stray model doc | `Planning/twin-cities-modelold.md` → `Planning/archive/` | Phase 1 follow-up |
| 2026-05-25 | Pull reusable refs | `old_docs/` + loose `Planning/` → `Planning/reference/` (6 docs) | candidates; reconciled in Phase 2 |
| 2026-05-25 | Re-tier data-models | `specs/data-models_spec.md` → `reference/data-models.md` | not a feature spec (no Done-when); retitled; pointer in `audience_spec.md` updated. Still-bare inner refs to `special-factions_spec.md`/`events_spec.md` to fix in cross-ref pass |
| 2026-05-25 | Archive stale mechanics docs | `reference/{02_Constants_and_Scales, 03_Core_Formulas, 08_Domain_Relationships, City_Sim_Mechanics_Reference_v06}` → `archive/` | Pre-split monolith chapters + their superset (v06), substantially unit-era (units removed in code). Replaced by lean code-verified refs. `formulas.md` built from `engine/formulas.py`; `constants.md` + `domain-relationships.md` to be rebuilt from code next. Originals preserved in archive for mining. |

---

| 2026-05-25 | Archive content docs | `reference/{RiversPoint_Domains_Factions_v01.txt, projects_catalog.md}` → `archive/` | Duplicate the seed JSON (`scr/data/{domains,factions,projects}.json` = runtime truth). Archived to avoid drift. |
| 2026-05-25 | Archive dead unit data | `scr/data/units.json`, `scr/data/past_cities/TwinCities/` → `archive/` | Unit-era seed data (units removed in engine v3); TwinCities out of scope and not returning. |
| 2026-05-25 | Remove `units_json` column | code + DB migration (see `decisions/2026-05-25-remove-units-json-column.md`) | Dead duplicate of `factions_json`. 234 tests pass. Wider named-units feature left untouched pending decision. |
| 2026-05-25 | Remove LARP + units + multiplayer (backend) | deleted `phase.py`/`actions.py`/`members.py`; dropped `PlayerAction`+`CityMember` models, `City.mode`, `SimRun.larp_phase`/`phase_advanced_at`; cleaned `sim.py`/`city.py`/`schemas.py`/`state.py`; DB migration drops 2 tables + 3 columns | LARP spun into its own program. 234 tests pass. |
| 2026-05-25 | Remove LARP + units (frontend) | `BuilderView`/`DashboardView`/`HomeView` + `api.js`; deleted `UnitForm.vue`+`CharacterPopout.vue`; factions table now uses embedded `f.leader.name`, dropped unit-era `member_ids` column | `npm run build` clean. See `decisions/2026-05-25-remove-larp-units-multiplayer.md`. |
| 2026-05-25 | Reconcile architecture docs | rewrote `system-overview.md` v4 (faction-only, sequential-initiative, current files/routes); archived `engine-module-map.md` (100% unit-era, duplicates code+specs) → `archive/` | Cross-ref check done: fixed `data-models.md` inner refs to `../specs/`; historical decision/changelog refs to `data-models_spec.md` left as append-only record. No live broken refs. |
| 2026-05-25 | Merge CLEANUP → Features_Todo | `CLEANUP.md` removed; its one open decision (`unstable_stacks` reset vs decay) moved into `Features_Todo.md` "Open Decisions" | Parked-decisions and backlog were the same shelf. Content preserved, not lost. |
| 2026-05-25 | Add Planning steering doc | new `Planning/CLAUDE.md` (folder guide + spec index + tier pointers); removed `specs/README.md` (index absorbed) | One auto-loaded orientation doc per folder level; kept non-overlapping with root/scr CLAUDE.md. README content fully preserved in `Planning/CLAUDE.md`. |

### Decisions during reference rebuild (2026-05-25)

- **No `constants.md`.** Tuning constants are subsystem-local, each owned by its spec/module
  (`ACTION_COSTS`→mayor, `BASE_WEIGHTS`/`TRAIT_MODIFIERS`/`SKIP_CHANCE`→faction-behavior,
  `LEVERAGE_THRESHOLD`/`REMOVAL_THRESHOLD`→special-factions, `RATING_MAX`→`formulas.md`).
  A shared constants doc would duplicate code and drift — rejected on single-source-of-truth grounds.
- **No `domain-relationships.md`.** Relationship arrays live in `scr/data/domains.json` (runtime truth),
  mechanics in `engine/npc/behavior.py` (owned by `faction-behavior_spec`), and the `DomainRelationship`
  model in `data-models.md`. Nothing non-duplicative left for a reference doc.
- **Final reference tier:** `data-models.md` + `formulas.md` only.

---

## Removed / consolidated content

Each entry: **what was removed**, **where it came from**, **why**, then the verbatim text.
Nothing is deleted from the project until it is recorded here.

<!-- Template:
### YYYY-MM-DD — <short label>
- **From:** <file + section>
- **Why:** <superseded by / duplicated in / stale vs code>
- **Content:**
```
<verbatim removed text>
```
-->
