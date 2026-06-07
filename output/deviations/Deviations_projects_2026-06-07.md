# Deviations — Projects v6 (Base-Project Stack Model)
Blueprint: Planning/blueprints/projects_BP.md
Date: 2026-06-07

| Slice | Step | Deviation | Why |
|-------|------|-----------|-----|
| 1 | 1–2 | Added the `BaseProjectStack` dataclass and all derived helpers + `project_tier` in one edit. | Same class; both step checks verified. |
| 1 | 2 | Blueprint's inline hint said `expect 6 0`; spec-correct is `6 2` (a building top still has a pristine instance below contributing +2). | Foreman miscalculation in the example literal; code follows the spec, tests assert spec-correct values. |
| 2 | 2 | `main.py` (CLI) stack init deferred from Slice 2 to Slice 3. | `run_cycle` didn't consume `base_stacks` until Slice 3; initializing earlier would create state nothing read. Done in Slice 3. |
| 3 | 1 | Kept `project_cap_contribution` (formulas.py) rather than removing it. | Still imported by a legacy `test_projects.py` reference at the time; the stack path uses the new `stack_cap_contribution`. (The test import was later dropped; the legacy fn remains harmless for any `category=="base"` Project in old snapshots.) |
| 4–5 | all | Build (Slice 4) and sabotage/repair + dispatch (Slice 5) engine code were rewritten in one coherent pass, since `resolution._execute` dispatches both and both resolvers had to change signature together (project → stack). Tests were still written/organized per slice. | The action dispatch cannot be half-migrated; splitting the code edits would have left an un-runnable intermediate state. |
| 4 | 2 | Found and fixed a real bug: `top_is_building()`/`top_is_pristine()`/`top_is_damaged()` now require `count >= 1`. | The original `not completed` treated an **empty** stack (count 0) as a build site, so the Mayor "built" a count-0 stack and the NPC saw a phantom build site. Caught by the rewritten init/mayor-act tests. |
| 5 | 1 | Left the legacy `repair_project(project)` and `harm_project(project)` functions in place. | They serve the retained legacy `Project` (tax_collection) path and are still covered by legacy tests; the stack path uses `repair_stack` / `apply_sabotage_damage`. |
| 6 | 1 | `/projects/catalog` still returns `ProjectResponse` (legacy). | The catalog is the (now empty) legacy project catalog; only `/projects` (the live panel feed) moved to `BaseStackResponse`. |
| Final | Final | Live play-screen `[human-required]` UI evidence deferred to the inspector. | The inspector drives the UI and captures screenshots with fresh eyes; the builder's automated checks (full suite 341 passed, `npm run build` exit 0) are complete. |
