# Inspect Report — Projects v6 (Base-Project Stack Model) · Final
Spec: Planning/specs/projects_spec.md
Blueprint: Planning/blueprints/projects_BP.md
Date: 2026-06-07
Run/demo command: `cd backend && py -m uvicorn api.server:app` → http://localhost:8000

Summary: 29 passed · 0 failed · (UI items below need human sign-off)
Criteria: projects_spec — **28 automated**; game-ui Projects Panel — 1 automated + 6 human-required.

All 28 projects_spec automated Done-when items are encoded by committed tests; the full set
runs green (98 passed across the projects-encoding files; full suite 341 passed). The game-ui
stack API contract test passes; the game-ui human-required UI items are evidenced via the live
play screen (screenshots below).

## Results — projects_spec (automated)
| Feature / Criterion | Status | Evidence (committed test) |
|---|---|---|
| Cap — cycle-0 base_cap = round(Σlevel×1.20), authored cap ignored | PASS | test_projects_cap.py::TestBaseCap |
| Cap — count 0 → cap == base_cap | PASS | test_projects_cap.py::test_empty_stack_cap_equals_base_cap |
| Cap — all-pristine → +count×2 | PASS | ::test_pristine_stack_adds_count_times_two |
| Cap — damaged top drops cap by 1 (21–50) / 2 (1–20) | PASS | ::test_damaged_top_drops_cap |
| Cap — building top contributes 0 | PASS | ::test_building_top_adds_zero |
| Cap — CAP_HEADROOM_MULT single constant | PASS | ::test_cap_headroom_constant |
| Build — faction success +build_step%, fail unchanged | PASS | test_projects.py::TestBuildModel::test_faction_success_adds_step / test_faction_fail_adds_nothing |
| Build — cross-domain → blocked | PASS | ::test_cross_domain_blocked |
| Build — Mayor buy charges 50g+1AP; shortfall no-op | PASS | ::test_mayor_buy_adds_step_and_charges / _insufficient_gold / _no_ap |
| Build — reaching 100% → completed | PASS | ::test_completion_at_100 |
| Build — build_step 10 → 10 actions | PASS | ::test_variable_build_step_takes_ten_actions |
| Build — no build_cost lump deducted | PASS | ::test_mayor_buy_adds_step_and_charges (flat 50 only); test_mayor_act TestBuildProject::test_initiates_when_empty (50 on break-ground) |
| Init — break ground sets count+1/building/progress 0 | PASS | test_project_initiation.py::TestInitiateHelper::test_break_ground_on_empty / _pristine_pool |
| Init — refused while in-flux (building/damaged) | PASS | ::test_refused_while_building / _damaged |
| Init — NPC near-cap initiates; not while in-flux | PASS | ::TestFactionInitiation (near_cap / below_threshold) |
| Init — Mayor initiates in faction-less domain | PASS | ::TestMayorInitiation::test_mayor_initiates_in_factionless_domain |
| Sabotage — resolves on top; pool below never targeted | PASS | test_projects.py::TestSabotageBase (top-only; building/damaged tops hit) |
| Sabotage — decisive −25 / partial −10 / fail 0 | PASS | ::test_decisive_minus_25 / _partial_minus_10 / _fail_no_damage |
| Sabotage — building top is a valid target | PASS | ::test_building_top_is_sabotageable |
| Sabotage — clamps at 0, count unchanged | PASS | ::test_clamps_at_zero_count_unchanged |
| Sabotage — hit at 0 → count−1, reveal pristine / empty | PASS | ::test_destroyed_only_on_hit_while_at_zero / _destroy_last_empties_stack |
| Sabotage — not domain-gated | PASS | ::test_not_domain_gated |
| Repair — damaged top +build_step%, 30g+1AP | PASS | test_projects.py::TestRepairStack::test_repair_adds_build_step |
| Repair — reaching 100 folds into pool | PASS | ::test_repair_to_100_folds_into_pool |
| Repair — refused on pristine/building | PASS | ::test_repair_refused_on_pristine / _building |
| Repair — lever repairs when damaged, builds otherwise | PASS | test_mayor_act.py::TestBuildProject::test_repairs_damaged_top / _adds_step_when_building |
| Maintenance — 2×(active base + active tax); building excluded | PASS | test_projects_cap.py::test_maintenance_formula_per_active_count / test_runner_counts_active_from_stacks_excluding_building |
| Maintenance — skipped when broke, no damage | PASS | test_projects_cap.py::test_maintenance_skipped_when_broke / test_projects.py::TestMaintenanceBase::test_maintenance_skipped_when_broke_no_damage |

## Results — game-ui Projects Panel
| Criterion | Status | Evidence |
|---|---|---|
| /projects returns one stack per domain w/ count, completed, progress | PASS (automated) | tests/test_projects_api.py — 2 passed |
| Header per domain, faction-panel order, "Other" fallback | needs-human | `spec_projects_final_01_panel.png` — 8 domain headers, order matches the faction panel |
| Collapsible, expanded on load | needs-human | `..._01_panel.png` — all groups expanded (carets ▾) |
| Empty stack → "No projects" placeholder | needs-human | `..._01_panel.png` — Temples/Military/Harbor/Trade/Guilds/Professions/Academy show "No projects" |
| Pooled `Name ×N` row for pristine instances | needs-human (partial) | derived view shown in modal ("Built: N standing"); a live pristine pool ≥2 was not captured — see Findings |
| Building top front shows build %; damaged shows health %, distinct; pristine no front | needs-human (partial) | `..._01_panel.png` — Estate building front at 30%; damaged-front not captured live (see Findings) |
| Click stack → read-only details modal w/ core fields | needs-human | `..._02_details.png` — Estate: Construction 30% bar, Built 0 standing, Top building 30%, Domain Aristocracy, Build step 25%/action, Initiated by Mayor |

## Deviations noted
See `output/deviations/Deviations_projects_2026-06-07.md`. Confirmed none contradict a spec
criterion. Notable: the builder found & fixed a real bug (`top_is_building()` treating an empty
stack as a build site) — now covered by tests; `repair_project`/`harm_project`/`project_cap_contribution`
retained for the legacy `Project` (tax_collection) path.

## Findings (not failures — evidence gaps for the human)
- The live capture seeds via the Mayor across banked-AP cycles; during those cycles NPC factions
  built **and** sabotaged the Aristocracy stack (visible in the event log: "The Tanners damages
  Estate (−10%)", multiple sabotage attempts), so the stack stayed at count 1 (building front) and
  a **pooled `Estate ×2` row** and a **damaged-front row** were not visually captured. Both
  rendering paths are exercised by the derived helpers (`poolCount`/`frontKind`) and unit tests,
  and the modal shows the pool/front derivation ("Built: 0 standing", "Top: building 30%"). The
  human may want to drive a quieter scenario to eyeball the pooled and damaged rows.

## Human sign-off
Review each, tick when verified:
- [ ] Header per domain in faction-panel order — `spec_projects_final_01_panel.png`
- [ ] Collapsible + expanded on load — `..._01_panel.png`
- [ ] "No projects" placeholder for empty stacks — `..._01_panel.png`
- [ ] Building front shows build % — `..._01_panel.png` (Estate 30%)
- [ ] Pooled `Name ×N` row — drive a quieter scenario to confirm visually (logic verified)
- [ ] Damaged-front distinct row — drive a scenario with a completed-then-damaged top (logic verified)
- [ ] Stack details modal core fields — `..._02_details.png`
