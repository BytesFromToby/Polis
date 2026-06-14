# Blueprint: Treasury Demo Redesign (v3)
Spec: Planning/specs/treasury_spec.md
Date: 2026-06-07

---

## Builder instructions
- Execute steps in order. Do not skip, reorder, or read ahead into the next slice.
- Check off each step when complete: [ ] → [x]
- One step = one logical concern. If a step can't be tested on its own, it's too small — merge it. If it touches more than one concern, split it.
- Deviation: if you do something differently than the step says, note it inline and keep going.
- Stuck: stop immediately. Do not try alternative approaches. Report exactly where and why.
- Test command: `cd backend && py -m pytest tests/ -q`

---

## Slice 1: Income — base + Tax Offices
**Scope:** `process_treasury_step0` produces income = 20 + 20 × completed Tax Offices, with the per-domain auto-tax removed; expenditure (guard + maintenance) still behaves as before.

### Step 1: Add income constants
**Build:** In `engine/formulas.py`, add module constants `BASE_INCOME = 20` and `TAX_OFFICE_INCOME = 20` with a one-line comment (treasury_spec v3).
**Test:** `cd backend && py -c "from engine.formulas import BASE_INCOME, TAX_OFFICE_INCOME; print(BASE_INCOME, TAX_OFFICE_INCOME)"`
**Done When:** Prints `20 20`.
**Stuck If:** N/A.
- [x] Complete

### Step 2: Rewrite income to base + Tax Offices; thread base_stacks
**Build:** In `engine/mayor/treasury.py`:
- Add a `base_stacks: Dict[str, BaseProjectStack] | None = None` parameter to `process_treasury_step0` (default None → treat as empty).
- Replace the body of `_calc_tax_income` (or replace its call) so income = `BASE_INCOME + TAX_OFFICE_INCOME × civic_office_count`, where `civic_office_count = base_stacks["civic"].active_count()` if a `civic` stack exists else 0. Do NOT sum per-domain `treasury.get_rate(...)` income anymore (auto-tax removed). Keep the `TaxIncome` ActionResult/log.
- In `engine/cycle/runner.py`, pass `base_stacks=base_stacks` into the `process_treasury_step0(...)` call (~line 92).
**Test:** `cd backend && py -m pytest tests/ -q`
**Done When:** Full suite still runs (some existing treasury tests may need the income-model update in Step 3's test file; if an EXISTING test asserts old auto-tax income, note it as expected fallout and fix it in Step 3). No import/signature errors.
**Stuck If:** An existing test failure is about something other than the changed income model.
- [x] Complete
**Deviation:** 6 existing tests fail as expected income-model fallout (old auto-tax assertions + flat-base shifting "broke" scenarios): test_mayor.py TestTreasuryIncome::{test_income_added_to_gold, test_guard_payroll_skipped_if_broke, test_investment_matures}, TestMayorCycleIntegration::{test_treasury_income_applied_each_cycle, test_treasury_runs_without_player_action}, test_projects_cap.py::test_maintenance_skipped_when_broke. All confirmed income-model-related (not regressions); fixed in Step 3.

### Step 3: Income tests
**Build:** Create `backend/tests/test_treasury_income.py`. Build a `Treasury`, a `factions` dict with a few factions across domains, and `base_stacks` via helpers. Cover the four `[automated]` Income Done-when items:
1. No Tax Offices (no `civic` stack or count 0) → one `process_treasury_step0` raises income by exactly 20.
2. `civic` stack with N completed Tax Offices (count=N, completed, progress=100) → income == `20 + 20*N`.
3. `civic` stack whose top is building (completed=False) over a pristine pool of K → income counts only `active_count` (== K), i.e. `20 + 20*K`, not the building top.
4. A domain full of factions with a standard/default rate contributes 0 — income equals base+offices regardless of factions present.
Assert via `treasury.income_this_cycle` and/or gold delta. If any existing treasury test asserted the old auto-tax income, update it here to the v3 model.
**Test:** `cd backend && py -m pytest tests/test_treasury_income.py -q`
**Done When:** All four income tests pass; full suite green.
**Stuck If:** active_count semantics don't match (re-read `BaseProjectStack.active_count`).
- [x] Complete

### Step 4: Expenditure regression test
**Build:** In `backend/tests/test_treasury_income.py` (or a clearly-named test), add one test that with gold covering costs, guard payroll deducts 20 and maintenance deducts `2 × active_count` (build a couple of completed base stacks and assert `expenditure_this_cycle`).
**Test:** `cd backend && py -m pytest tests/test_treasury_income.py -q`
**Done When:** The expenditure test passes.
**Stuck If:** N/A.
- [x] Complete

---
⛔ End of Slice 1. Run **inspector** on this slice before continuing.

---

## Slice 2: Tax Office lever — the civic domain
**Scope:** A faction-less `civic` ("Public Treasury") domain exists with a buildable "Tax Office" stack; faction-less domains keep their authored cap and Tax Offices add no cap contribution.

### Step 1: Register the civic base-project name
**Build:** In `engine/projects/processing.py`, add `"civic": "Tax Office"` to `BASE_PROJECT_NAMES`.
**Test:** `cd backend && py -c "from engine.projects.processing import base_project_name; print(base_project_name('civic'))"`
**Done When:** Prints `Tax Office`.
**Stuck If:** N/A.
- [x] Complete

### Step 2: Add the civic domain to data
**Build:** In `backend/data/domains.json`, add a domain object: `{"id": "civic", "name": "Public Treasury", "cap": 12, "drift": 0.0, "relationships": []}`. No faction references it (do not touch factions.json).
**Test:** `cd backend && py -c "from loaders import load_state_from_json; w,f,d = load_state_from_json('data'); print('civic' in d, d['civic'].name, d['civic'].cap)"`
**Done When:** Prints `True Public Treasury 12` (cap stays 12 — see Step 3; before Step 3 it may print 0, which Step 3 fixes).
**Stuck If:** Loading civic raises, or breaks faction/domain processing elsewhere.
- [x] Complete

### Step 3: Faction-less domains keep authored cap
**Build:** In `loaders.py` `_freeze_base_caps`, skip domains with no factions — leave their authored `cap` and set `base_cap = cap` (do NOT derive base_cap from fill 0). Use the already-computed `domain.utilization == 0` as the faction-less signal (factions always have level ≥ 1, so utilization 0 ⇒ no factions), or pass factions if cleaner. In `engine/cycle/runner.py` cap recompute (~line 85), for a faction-less domain set `domain.cap = domain.base_cap` (no `stack_cap_contribution`), so building Tax Offices does not move the civic cap.
**Test:** `cd backend && py -c "from loaders import load_state_from_json; w,f,d=load_state_from_json('data'); print(d['civic'].cap, d['civic'].base_cap, d['civic'].utilization)"`
**Done When:** Prints `12 12 0.0`.
**Stuck If:** A faction-bearing domain's cap changes from its v6 value (the skip must apply only to faction-less domains).
- [x] Complete

### Step 4: Civic domain + cap tests
**Build:** Create `backend/tests/test_civic_domain.py`. Cover the four `[automated]` Tax Office Done-when items:
1. `base_project_name("civic") == "Tax Office"`.
2. After `load_state_from_json('data')`, `civic` exists, `cap == 12` (authored, not 0), `utilization == 0`.
3. Building via `mayor_build_base("civic", base_stacks, treasury, mayor)` (with `new_base_stacks(domains)`, a `Mayor` with AP and a `Treasury` with ≥50 gold) succeeds (breaks ground, deducts 50 gold + 1 AP) and the civic stack grows; completing it (repeat build steps) yields `active_count() == 1`.
4. Building/completing a Tax Office leaves `civic` cap == 12 after a `run_cycle` recompute, and an influence domain's cap is unchanged by the Tax Office build.
**Test:** `cd backend && py -m pytest tests/test_civic_domain.py -q`
**Done When:** All four pass.
**Stuck If:** `new_base_stacks` does not produce a `civic` stack (means civic isn't in the domains map).
- [x] Complete

---
⛔ End of Slice 2. Run **inspector** on this slice before continuing.

---

## Slice 3: Insolvency — clamp + damage; remove bankruptcy ladder
**Scope:** When expenditure can't be covered, gold clamps at 0 and the shortfall damages random non-civic base-project instances; the v2 bankruptcy ladder is gone.

### Step 1: Clamp at 0 + convert shortfall to damage
**Build:** In `engine/mayor/treasury.py` expenditure handling, replace any path that lets gold go negative / runs a bankruptcy ladder with: compute the cycle's required expenditure; if gold can't cover it, deduct what it can, set `gold = 0`, and compute `shortfall = required − paid`. Apply the shortfall as damage to RANDOM NON-CIVIC base stacks: repeatedly pick a random stack from `base_stacks` excluding `civic` (and excluding empty stacks), and call `apply_sabotage_damage(stack, amount)` from `engine.projects.processing`, consuming the shortfall ~1:1 as health points (e.g. apply in chunks until the shortfall is spent or no damageable non-civic instances remain). Log an insolvency `ActionResult`. Remove the 3-cycle bankruptcy-ladder logic. Use a seedable RNG or accept an injected `rng`/`random` for testability.
**Test:** `cd backend && py -m pytest tests/ -q`
**Done When:** Suite runs; no negative gold path remains; no bankruptcy-ladder code remains.
**Stuck If:** `apply_sabotage_damage`'s "destroy only when hit at 0 health" semantics make the shortfall hard to spend — re-read it (Slice context) and loop hits per instance; if still unclear, stop.
- [x] Complete

### Step 2: Insolvency tests
**Build:** Create `backend/tests/test_treasury_insolvency.py`. Cover the four `[automated]` Insolvency Done-when items:
1. Expenditure exceeds gold → after the step, `treasury.gold == 0` (never negative).
2. The shortfall damages non-civic stacks (total non-civic health or `active_count` drops) AND a `civic` Tax Office stack present is untouched (its count/progress unchanged).
3. A shortfall large enough destroys an instance → a non-civic stack's `active_count` is lower after, so a following expenditure cycle has lower maintenance.
4. On a deficit, none of the v2 bankruptcy-ladder effects fire (assert no guard-skip/projects-pause/−20 public-rep markers; simplest: the function no longer produces those ActionResults / no such code path).
Seed/inject RNG so target selection is deterministic.
**Test:** `cd backend && py -m pytest tests/test_treasury_insolvency.py -q`
**Done When:** All four pass.
**Stuck If:** RNG can't be controlled (add an injectable rng param).
- [x] Complete

---
⛔ End of Slice 3. Run **inspector** on this slice before continuing.

---

## Final Slice: Verification
**Scope:** Full spec verification; capture evidence for human-required items.

### Final Step: Verify spec Done when items
**Build:** No new code. Confirm all `**Done when:**` items across treasury_spec.md v3 are met.
**Test:** `cd backend && py -m pytest tests/ -q` (the committed tests from Slices 1–3 cover all 13 `[automated]` items) and capture output. For the 2 `[human-required]` items, rebuild the frontend (`cd frontend && npm run build`) and capture evidence by driving the UI: (a) Tax Offices appear under a "Public Treasury" group in the projects panel and `civic` is NOT a faction group in the faction panel; (b) the Mayor treasury panel exposes no invest/borrow/guard-surge/public-works controls and changing a domain tax rate has no income/rep effect.
**Done When:** Every `[automated]` criterion passes via its committed test; both `[human-required]` criteria have captured evidence.
**Stuck If:** An automated criterion fails and the cause is not clear from the output.
- [x] Complete

---
⛔ Final slice complete. Run **inspector** for final sign-off.

INSPECTED 2026-06-07 — 13 PASS · 0 FAIL · 2 needs-human (see output/inspect/Inspect_treasury-demo-redesign_Final_2026-06-07.md)
