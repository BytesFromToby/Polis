# Deviations — Projects Rework (v5)
Blueprint: Planning/blueprints/projects-rework_BP.md
Date: 2026-06-05

| Slice | Step | Deviation | Why |
|-------|------|-----------|-----|
| 3 | 1 | Base-project name catalog kept as a code constant `BASE_PROJECT_NAMES` (not as 8 templates in `data/projects.json`). | Blueprint allowed "and/or a constant". The constant is the engine source of truth for initiation; loading templates as instances would start the game with 8 under-construction projects, violating zero-start. |
| 3 | 2 | Also refined `_get_buildable_projects` to exclude *active* base projects. | A completed (active) base project isn't buildable; without this, factions would target a done Docks and waste the turn. |
| 3 | 3 | Provided engine entry `mayor_build_base(domain, projects, treasury, mayor)` (find-or-initiate then buy a unit); did **not** wire it to a player-facing MayorAction in the API/route dispatch. | The headless demo drives initiation via the near-cap faction path; the player-facing Mayor build button is API-layer work outside this slice's tests. |
| 4 | 1 | Verification only — no code change to `resolve_sabotage_project` (already category-agnostic). | Cap drop on destruction is handled by Slice 1's `project_cap_contribution` (destroyed → 0). |
| 4 | 2 | Verification only — no code change to maintenance. | The runner counts active projects without category filtering, so base projects are already included. |
| Final | 1 | `data/projects.json` emptied to `[]` (zero starting instances) rather than holding the 8 templates. | Catalog is the code constant; loading templates as instances would violate zero-start. No loader change needed. Old 45 entries recoverable via git. |
| Final | 3 | **Bug fix (smoke-discovered):** `run_cycle` used `projects or {}`, creating a throwaway empty dict so runtime-initiated base projects were discarded. Normalized to use the caller's dict. | Pre-existing pattern; harmless until projects could be created mid-cycle. Without the fix, no base project ever persisted. |
| Final | 3 | **Bug fix (smoke-discovered):** under-construction base projects (structural `health == 0`) were instantly destroyed by `SabotageProject`. Added a guard so a base project under construction is not a sabotage target (in `resolve_sabotage_project` and behavior targeting). | Base projects build via `build_progress`, not `health`; with health 0 they were trivially destroyable, so 21/22 died before completing. The blueprint's Slice-4 Step-1 note anticipated this interference. |
| Final | 1 | Updated existing test `test_theme_data.py::test_every_project_uses_a_greek_domain` to validate the code catalog `BASE_PROJECT_NAMES` (and tolerate an empty `projects.json`) instead of asserting `projects.json` is non-empty. | The test encoded the old assumption that projects live in `projects.json`; that file is now intentionally empty. |

## Outcome
- Full suite: **318 passed**. Headless `py main.py --cycles 10`: clean.
- Smoke over 15 cycles: 16 base projects initiated (12 active, 3 building, 1 destroyed-after-completion); all 8 domains' `cap` grew above `base_cap`.
- All 21 `[automated]` spec Done-when items backed by committed tests.
