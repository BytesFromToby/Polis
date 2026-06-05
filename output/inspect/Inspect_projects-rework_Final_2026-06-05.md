# Inspect Report — Projects Rework · Final
Spec: Planning/specs/projects_spec.md (v5)
Blueprint: Planning/blueprints/projects-rework_BP.md
Date: 2026-06-05
Run/demo command: `cd backend && py -m pytest tests/ -q` · `cd backend && py main.py --cycles 10`

Summary: **21 passed · 0 failed · 0 need human sign-off**
(5 features; 21 [automated] Done-when items, all backed by committed tests)

Full suite: **318 passed**. Headless `py main.py --cycles 10`: exit 0, clean.

---

## Results

### Feature: Domain cap derivation
| Criterion | Status | Evidence |
|-----------|--------|----------|
| base_cap == round(initial Σlevel × 1.20); authored domains.json cap ignored | PASS | test_projects_cap.py::TestBaseCap::test_formula, ::test_freeze_ignores_authored_cap + **independent check on real data**: all 8 domains base_cap == round(fill×1.2), authored cap 300 ignored |
| Domain with no base projects: cap == base_cap every cycle | PASS | test_projects_cap.py::test_no_base_projects_cap_equals_base_cap |
| Intact +2 / damaged +1 / critical·under_construction·destroyed +0 | PASS | test_cap_contribution_by_tier[active-80-2, damaged-40-1, critical-10-0, under_construction-0-0, destroyed-0-0] |
| Cap re-derived each cycle (intact→damaged drops cap by 1) | PASS | test_cap_rederived_each_cycle |
| CAP_HEADROOM_MULT single named constant in formulas.py | PASS | test_cap_headroom_constant (monkeypatch → base_cap changes) |

### Feature: Build model (4 work units)
| Criterion | Status | Evidence |
|-----------|--------|----------|
| Faction success (roll ≥12, own domain) +1; fail +0 | PASS | TestBuildModel::test_faction_success_adds_one_unit, ::test_faction_fail_adds_nothing |
| Cross-domain build → blocked, +0 | PASS | ::test_cross_domain_blocked |
| Mayor buy ≥50g & ≥1AP → +1, deduct 50g+1AP | PASS | ::test_mayor_buy_adds_unit_and_charges |
| Mayor buy <50g or 0AP → +0, no deduction | PASS | ::test_mayor_buy_insufficient_gold_no_charge, ::test_mayor_buy_no_ap_no_charge |
| 3 AP + ≥150g → 3 units one turn | PASS | ::test_mayor_can_rush_three_units_one_turn |
| 4th unit → active, health 100, same resolution | PASS | ::test_completion_at_four_units |
| No build_cost deducted | PASS | ::test_no_build_cost_deducted (build_cost 999, only flat 50 charged) |

### Feature: Initiation
| Criterion | Status | Evidence |
|-----------|--------|----------|
| Initiating creates 1 under_construction instance, progress 0, domain name | PASS | test_project_initiation.py::TestInitiateHelper::test_creates_instance |
| ≤1 under_construction per domain (2nd refused) | PASS | ::test_second_initiation_in_same_domain_refused |
| NPC selects BuildProject-to-initiate when ≥0.85×cap none in progress; not when one in progress | PASS | TestEligibility (3) + TestFactionInitiation::test_faction_can_select_initiation_when_near_cap, ::test_faction_never_initiates_when_one_under_construction |
| Mayor can initiate in a faction-less domain | PASS | TestMayorInitiation::test_mayor_initiates_in_factionless_domain |

### Feature: Damage, defense & destruction
| Criterion | Status | Evidence |
|-----------|--------|----------|
| Decisive −25 / partial −10 / fail 0 on a base project | PASS | TestSabotageBase::test_decisive_minus_25, ::test_partial_minus_10, ::test_fail_no_damage |
| Health 0 → destroyed, contributes 0 to cap | PASS | ::test_destroyed_at_zero_and_no_cap |
| SabotageProject not domain-gated | PASS | ::test_not_domain_gated |

### Feature: Maintenance
| Criterion | Status | Evidence |
|-----------|--------|----------|
| Maintenance == 2 × active project count | PASS | TestMaintenanceBase::test_maintenance_is_two_times_active_count (delta −6 for 3) |
| Unaffordable → skipped, no project damage | PASS | ::test_maintenance_skipped_when_broke_no_damage |

### Independent end-to-end check (beyond unit tests)
- Real-data load: all 8 domains' base_cap correct, authored cap ignored. PASS.
- 15-cycle run: 16 base projects initiated (12 active, 3 building, 1 destroyed-after-completion); all 8 domains' cap grew above base_cap. The projects↔cap loop is live and self-driving.

---

## Deviations noted
| Step | Deviation | Impact |
|------|-----------|--------|
| Final/3 | Under-construction base projects guarded from Sabotage (`resolve_sabotage_project` + behavior targeting) | **Contradicts the spec's Damage *Input* prose** ("active/under-construction base project targeted by SabotageProject"). No Done-when item covers under-construction sabotage, so all 21 automated criteria still pass. The guard is a sound gameplay fix — base projects build via `build_progress`, not `health`, so an unbuilt site (health 0) would otherwise be one-shot destroyed (smoke showed 21/22 died). **Recommend reconciling the spec Input line** to "an active/damaged base project" via an architect touch. |
| Final/3 | `run_cycle` normalized to use the caller's `projects` dict (was `projects or {}`) | Bug fix; no criterion impact (enables persistence of runtime-initiated projects). |
| 3/3 | `mayor_build_base` provided as the engine entry; player-facing MayorAction/API dispatch deferred | Initiation Done-when (#107) is engine-level and passes via the committed test. Player-facing Mayor build button is out-of-scope API work. |
| Final/1 | `data/projects.json` emptied to `[]`; catalog is the `BASE_PROJECT_NAMES` code constant | No criterion impact; "start at zero base projects" honored. |

---

## Verdict
All 21 [automated] spec Done-when items pass via committed tests; independently re-verified cap derivation on real data and confirmed the projects↔cap loop runs end-to-end in a live sim. Suite 318-green, headless clean. **One spec-prose mismatch** (under-construction sabotage in the Damage Input line) should be reconciled by architect — it is a wording fix, not a code defect, and blocks nothing. Feature verified.
