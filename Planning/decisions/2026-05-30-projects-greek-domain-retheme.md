# Re-theme projects.json to the 8 Greek domains

Date: 2026-05-30
Trigger: Surveyor finding #1 (Survey_2026-05-29) — `projects.json` still used the pre-Greek
legacy domains, the most visible coherence gap (legacy names showed in the live Projects panel).

## What changed
`backend/data/projects.json` went from 50 projects across 10 legacy domains to **45 projects
across the 8 canonical Greek domains**. Mechanics (build cost/time, maintenance, effect values,
tax levels) are unchanged — this is flavor/labelling only.

Domain + id-prefix remap:
- `guilds` → guilds (unchanged)
- `docks` → harbor
- `noble_houses` → aristocracy
- `city_watch` → military
- `temple` → temples
- `commons` → **trade**
- `arcane` → academy
- `registry` → professions
- `underworld` → **cut (5 projects removed)**
- `tax_*` projects: id prefix kept (it names a function/category, not a legacy domain);
  their `domains` field moved `registry` → professions

## Why these choices (the non-obvious forks)
- **trade had no projects.** After the clean 7 remaps, `trade` — a core Greek domain — would
  have shown an empty Projects panel. The `commons` set (Public Market, Well, Common House,
  Tenement, Paving) is civic/agora-flavored and maps to trade better than anywhere else, so it
  fills trade rather than being cut. (User decision.)
- **underworld was cut, not remapped.** Its projects (Safe Houses, Fence's Depot, Gambling Den,
  smuggling Passage) have no clean Greek home; the domain itself was cut in the theme conversion,
  so its projects follow it out rather than being force-fit. Result: 50 → 45. (User decision.)
- **ids re-prefixed** (e.g. `docks_dry_dock` → `harbor_dry_dock`) so the JSON reads cleanly.
  Safe because no code, test, seed, or live save references a project id by its legacy prefix
  (verified by grep). In-progress saves snapshot their own project state, so they are unaffected.
- **tax_ ids kept** because `tax_` is a category prefix, not a legacy domain prefix — renaming
  them to `professions_tax_*` would be noise. Only their `domains` field moved to professions.

## Verification
- New guard tests in `tests/test_theme_data.py`:
  `test_every_project_uses_a_greek_domain` (every `domains` entry and every domain-targeting
  effect ∈ the 8 Greek domains) and `test_no_legacy_domain_prefixes_in_project_ids`.
- Full suite: 276 passed.
- No re-seed required: `load_projects()` reads `projects.json` fresh at sim start
  (`api/routes/sim.py`) and for the mayor catalog (`api/routes/mayor.py`); the seeded official
  city stores only domains/factions/world_state, not projects.

## Known residue (not in scope of the user's decision)
A few academy display names still read fantasy-magic rather than Greek-scholarly
(`Reagent Storeroom`, `Warding Workshop`, `Scribing Hall`). Only `Arcane Sanctum` →
`Scholars' Sanctum` was changed. The rest are left for an optional flavor pass.
