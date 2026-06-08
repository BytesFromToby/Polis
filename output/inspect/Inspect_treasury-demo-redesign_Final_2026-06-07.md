# Inspection Report — Treasury Demo Redesign (final sign-off)

**Feature:** Treasury Demo Redesign (v3)
**Spec:** `Planning/specs/treasury_spec.md` (v3)
**Blueprint:** `Planning/blueprints/treasury-demo-redesign_BP.md`
**Inspector:** fresh-eyes review (did not build)
**Date:** 2026-06-07

## Verdict summary

| Result | Count |
|--------|-------|
| PASS (automated) | 13 |
| FAIL | 0 |
| needs-human | 2 |

- 13 `[automated]` Done-when items: **all PASS**.
- 2 `[human-required]` Done-when items: **needs-human** (verified by static inspection; person must click to confirm).

## Test evidence

Targeted run:
`cd backend && py -m pytest tests/test_treasury_income.py tests/test_civic_domain.py tests/test_treasury_insolvency.py -v`
→ **13 passed in 0.05s**.

Full suite: `cd backend && py -m pytest tests/ -q` → **358 passed in 1.03s**.

Spot-checks:
- `from engine.formulas import BASE_INCOME, TAX_OFFICE_INCOME` → `20 20`
- `base_project_name('civic')` → `'Tax Office'`
- `load_state_from_json('data')` → `civic in d: True | cap: 12 | base_cap: 12 | util: 0`

---

## Income — base + Tax Offices

**DW1.** With no Tax Offices built, one `process_treasury_step0` adds exactly +20 income, regardless of factions/domains. `[automated]` — **PASS**
Test: `test_treasury_income.py::test_no_tax_offices_income_is_base` asserts `income_this_cycle == 20` with empty base_stacks. Impl: `_calc_income` (treasury.py:195-200) returns `BASE_INCOME + TAX_OFFICE_INCOME * office_count` with `office_count = 0` when no civic stack.

**DW2.** With N completed Tax Offices in the civic stack, income == 20 + 20×N. `[automated]` — **PASS**
Test: `test_income_scales_with_completed_offices` (count=3 → 80).

**DW3.** A civic stack whose top is still building contributes 0 — income = 20 + 20×active_count, not counting the building top. `[automated]` — **PASS**
Test: `test_building_top_not_counted` (count=3, completed=False → 60). Impl uses `civic.active_count()` (treasury.py:199).

**DW4.** A domain full of factions at default rate contributes 0 — income depends only on base + Tax Offices. `[automated]` — **PASS**
Test: `test_factions_generate_no_income` (two factions across trade/guilds, no offices → 20). Impl: `_calc_income` ignores factions/domains entirely; the old `_calc_tax_income` auto-tax is gone.

---

## Tax Office lever — the civic domain

**DW5.** `base_project_name("civic")` returns "Tax Office". `[automated]` — **PASS**
Test: `test_civic_domain.py::test_civic_base_project_name`. Impl: `BASE_PROJECT_NAMES` includes `"civic": "Tax Office"` (engine/projects/processing.py).

**DW6.** After loading data, civic exists with its authored cap (not overwritten to 0 by the freeze) and utilization 0. `[automated]` — **PASS**
Test: `test_civic_loads_with_authored_cap` (cap==12, utilization==0). Impl: `data/domains.json:131-136` authors civic cap 12; `loaders.py::_freeze_base_caps` (loaders.py:149-160) skips faction-less domains (`utilization == 0` → `base_cap = cap`, no fill-derived override).

**DW7.** Building a Tax Office via `mayor_build_base("civic", ...)` succeeds at standard cost (50 gold + 1 AP to break ground) and grows the civic stack. `[automated]` — **PASS**
Test: `test_tax_office_builds_at_standard_cost` (gold −50, AP −1, count≥1, then active_count()==1 on completion).

**DW8.** Civic cap unchanged by building Tax Offices, and no influence domain's cap changes when one is built. `[automated]` — **PASS**
Test: `test_tax_office_does_not_move_caps` (civic.cap==12 and guilds.cap unchanged after `run_cycle`). Impl: runner cap recompute (engine/cycle/runner.py:85-89) sets `domain.cap = domain.base_cap` for faction-less domains (no `stack_cap_contribution`).

**DW9.** Tax Offices appear under a "Public Treasury" group in the projects panel, and civic does not appear as a faction group. `[human-required]` — **needs-human**
Static inspection (GameView.vue):
- `projectsByDomain` (lines 356-380) iterates over all `snapshot.domains`, so civic → group named "Public Treasury" (its `domains.json` name) renders in the right Projects panel.
- `factionsByDomain` (lines 311-333) groups only over `Object.values(factions)` keyed by `domain_primary`; civic has no factions, so it is never a faction group.
A person should: start the UI, open the game view, and confirm (a) the right "Projects" panel shows a "Public Treasury" group with a Tax Office stack, and (b) the left "Factions" panel has no "Public Treasury" group.

---

## Expenditure (unchanged)

**DW10.** Guard payroll deducts 20/cycle and maintenance deducts 2 × active_count when gold covers them. `[automated]` — **PASS**
Test: `test_treasury_income.py::test_expenditure_guard_and_maintenance` (gold 500, active_project_count=3 → expenditure_this_cycle == 26). Impl: treasury.py:79-85.

---

## Insolvency — clamp + infrastructure damage

**DW11.** When expenditure exceeds available gold, gold ends the cycle at exactly 0 (never negative). `[automated]` — **PASS**
Test: `test_treasury_insolvency.py::test_gold_clamps_at_zero`. Impl: `paid = min(gold, required); gold -= paid`; on shortfall `gold = 0` (treasury.py:83-102).

**DW12.** An insolvency shortfall reduces total health/active_count across non-civic base stacks, and a civic Tax Office stack is never damaged. `[automated]` — **PASS**
Test: `test_shortfall_damages_noncivic_not_civic` (harbor.progress<100; civic count==1 & progress==100). Impl: `_apply_insolvency_damage` (treasury.py:118-145) filters `did != "civic"`.

**DW13.** A shortfall large enough to exceed an instance's remaining health destroys an instance, so next cycle's active_count (and maintenance) is lower. `[automated]` — **PASS**
Test: `test_large_shortfall_destroys_instance_lowering_maintenance` (active_count after < before). Impl: damage loop calls `apply_sabotage_damage`, destroying tops at 0 health.

**DW14.** No v2 bankruptcy-ladder effect (guard skip / projects-pause / −20 public-rep removal) fires on a deficit. `[automated]` — **PASS**
Test: `test_no_bankruptcy_ladder_effects` (no `outcome=="fail"` results; an `Insolvency` result present; public rep unchanged). Impl: ladder logic removed; only `Insolvency` ActionResult is emitted.

---

## Deferred to future

**DW15.** The demo exposes no invest, borrow, guard-surge, or public-works action, and adjusting a domain tax rate has no income or reputation effect. `[human-required]` — **needs-human**
Static inspection:
- `frontend/src/api.js:130-133` defines `borrow`, `invest`, `publicWorks`, `guardSurge` client methods — but a Grep of `frontend/src` finds **no `@click` or call site** invoking any of them. GameView.vue's only action surfaces are "Request Audience", "Actions ▸" (mayor modal), per-faction "Audience ▸", and project view/detail clicks. The lone `invest` reference in GameView (line 90) is a read-only display row gated on `treas.invested > 0` (a dormant field), not a control.
- Backend routes (`api/routes/mayor.py`) still expose `/treasury/borrow|invest|public-works|guard-surge` and the functions remain in `treasury.py`, but they are unreachable from the demo UI.
- Income path (`_calc_income`) ignores domain tax rates entirely; `apply_tax_effects` is the only consumer of `get_rate`, and no demo action sets a domain rate, so a rate change has no income/rep effect.
A person should: open the Mayor treasury/actions panel and confirm there are no invest/borrow/guard-surge/public-works buttons; optionally confirm changing a domain tax rate produces no income or reputation change.

---

## Notes / observations (non-blocking)

- The three committed test files (`test_treasury_income.py`, `test_civic_domain.py`, `test_treasury_insolvency.py`) are present and green but currently **untracked in git** (`git status` shows `??`). They should be committed so the suite is reproducible from a clean checkout. This does not affect any Done-when verdict.

---

**SIGNED — Inspector, 2026-06-07. 13 PASS · 0 FAIL · 2 needs-human.**
