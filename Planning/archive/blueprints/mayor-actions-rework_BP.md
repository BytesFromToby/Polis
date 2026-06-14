# Blueprint: Mayor Actions Rework (mayor_spec v3)
Spec: Planning/specs/mayor_spec.md
Date: 2026-06-05

---

## Builder instructions
- Execute steps in order. Do not skip, reorder, or read ahead into the next slice.
- Check off each step when complete: [ ] → [x]
- One step = one logical concern. If a step can't be tested on its own, it's too small — merge it. If it touches more than one concern, split it.
- Deviation: if you do something differently than the step says, note it inline and keep going.
- Stuck: stop immediately. Do not try alternative approaches. Report exactly where and why.

### Context the builder needs
- **Faction model:** `rank` float 1.0–10.0 (clamped in `Faction.__post_init__`), `level = int(rank)`, `health` 0–100. See `reference/formulas.md` / `reference/data-models.md`.
- **Dispatch paths:** most actions run through `execute_mayor_actions` → `_ACTION_MAP` (the dispatcher spends the AP *before* calling the resolver, then passes `mayor, treasury, factions, domains`). Two actions are **special-cased** directly in `api/routes/mayor.py` because they need state the dispatcher doesn't pass: `BreakADeal` (0 AP) and `GrantTaxExemption`. **Build Project joins this special-cased group** (it needs the session `projects` dict).
- **Roster note:** the spec lists **8 levers**, but **Request an Audience** is dispatched through the audience subsystem (its own routes), *not* `VALID_MAYOR_ACTIONS`. So the dispatchable allowlist after this rework is **7 entries**: `MeetWithFaction, PubliclyEndorse, PubliclyCondemn, GrantTaxExemption, Sabotage, BuildProject, BreakADeal`.
- **Reuse, don't reinvent:** `engine/projects/processing.py` already has `mayor_build_base`, `mayor_buy_build_unit`, `repair_project`, `initiate_base_project`. Build Project composes these — do not rewrite build/repair math.
- `Mayor.spend(cost)` deducts AP and returns False if insufficient. `mayor.action_points += cost` refunds. `mayor.adjust_reputation(fid, delta)` clamps to ±50.

---

## Slice 1: Cut the seven removed actions
**Scope:** The seven cut actions (Turn a Blind Eye, Issue a Decree, Broker a Deal, Allocate Budget, Appoint an Official, Request a Report, Plant a Rumor) and the replaced Withhold Resources are gone from dispatch, allowlist, and tests; the suite is green; a roster-integrity test pins the remaining set.

### Step 1: Remove cut resolvers and map/cost entries
**Build:** In `engine/mayor/actions.py`, delete the resolver functions `_broker_a_deal`, `_allocate_budget`, `_withhold_resources`, `_issue_a_decree`, `_appoint_an_official`, `_turn_a_blind_eye`, `_request_a_report`, `_plant_a_rumor`. Remove their keys from `ACTION_COSTS` and from `_ACTION_MAP`. Remove any now-unused imports (`resolve_contest` if no remaining user; keep `random` only if still used). Leave `_meet_with_faction`, `_publicly_endorse`, `_publicly_condemn` intact.
**Test:** `py -c "import engine.mayor.actions"` imports clean; `grep -c "_growth_blocked\|_decree_active\|_uncontested" engine/mayor/actions.py` returns 0.
**Done When:** Module imports with no error and none of the three orphaned flags are set anywhere in `actions.py`.
**Stuck If:** A removed resolver is referenced by something other than `_ACTION_MAP`/`ACTION_COSTS` (e.g. imported elsewhere).
- [x] Complete

### Step 2: Remove cut actions from the API allowlist
**Build:** In `api/schemas.py`, edit `VALID_MAYOR_ACTIONS` to remove `BrokerADeal`, `AllocateBudget`, `WithholdResources`, `IssueADecree`, `AppointAnOfficial`, `TurnABlindEye`, `RequestAReport`, `PlantARumor`. Leave `MeetWithFaction, PubliclyEndorse, PubliclyCondemn, GrantTaxExemption, BreakADeal` (Sabotage and BuildProject are added in later slices).
**Test:** `py -c "from api.schemas import VALID_MAYOR_ACTIONS; print(sorted(VALID_MAYOR_ACTIONS))"`.
**Done When:** None of the eight removed names appear in `VALID_MAYOR_ACTIONS`.
**Stuck If:** A removed action has bespoke handling in `api/routes/mayor.py` beyond the generic `execute_mayor_actions` path (none expected — verify).
- [x] Complete

### Step 3: Delete tests for the cut actions
**Build:** Remove tests that exercise the cut/inert actions:
- `tests/test_mayor.py`: `test_withhold_resources_sets_growth_blocked`, `test_appoint_official_to_leaderless`, `test_appoint_official_fails_if_already_has_leader`.
- `tests/test_mayor_act.py`: the `TestAuthorityActions` and `TestInformationActions` classes in full; and in `TestResourceActions` remove `test_allocate_budget_adds_drift`, `test_allocate_budget_requires_gold`, `test_withhold_blocks_growth`, `test_withhold_lowers_rep`; in `TestPoliticalActions` remove `test_broker_fails_without_rep`, `test_broker_can_succeed_with_rep`.
Keep all Meet/Endorse/Condemn, AP-spending, reputation, treasury, and exemption/deal tests.
**Test:** `py -m pytest tests/test_mayor.py tests/test_mayor_act.py -q`.
**Done When:** Both files pass with no collection errors and no reference to a removed resolver/flag.
**Stuck If:** A kept test depends on a removed helper.
- [x] Complete

### Step 4: Add the roster-integrity test
**Build:** In `tests/test_mayor_act.py`, add `class TestRosterIntegrity` with: (a) `test_valid_actions_is_exact_demo_set` asserting `VALID_MAYOR_ACTIONS == {"MeetWithFaction","PubliclyEndorse","PubliclyCondemn","GrantTaxExemption","Sabotage","BuildProject","BreakADeal"}`; (b) `test_removed_actions_absent` asserting each of the eight removed names is **not** in `VALID_MAYOR_ACTIONS` and **not** a key in `engine.mayor.actions._ACTION_MAP`. *(This test will FAIL until Slices 2–3 add Sabotage/BuildProject — that is expected; mark this step done when the test is written and its `test_removed_actions_absent` half passes. The exact-set half goes green at end of Slice 3.)*
**Test:** `py -m pytest tests/test_mayor_act.py::TestRosterIntegrity::test_removed_actions_absent -q`.
**Done When:** `test_removed_actions_absent` passes; `test_valid_actions_is_exact_demo_set` is written (may be red until Slice 3).
**Stuck If:** A removed name still resolves through any dispatch path.
- [x] Complete

### Step 5: Run the full suite
**Build:** No new code. Run the whole suite to confirm the removals broke nothing outside the mayor files.
**Test:** `py -m pytest tests/ -q`.
**Done When:** Suite is green except the intentionally-red `test_valid_actions_is_exact_demo_set` from Step 4 (note it as expected-red until Slice 3).
**Stuck If:** A non-mayor test fails referencing a removed action.
- [x] Complete

---
⛔ End of Slice 1. Run **inspector** on this slice before continuing.

---

## Slice 2: Sabotage
**Scope:** A working `Sabotage` action (1 AP + 50 gold, guaranteed) that erodes a target's fractional rank and halves its health, with overt reputation cost, level-1 targetable, and correct cost-refund behavior — all encoded in tests.

### Step 1: Implement the Sabotage resolver
**Build:** In `engine/mayor/actions.py`, add `_sabotage(ma, mayor, treasury, factions, domains)`:
- Resolve `target = factions.get(ma.target_id)`; if missing → `ActionResult(outcome="fail", ...)` and refund the AP (`mayor.action_points += ACTION_COSTS["Sabotage"]`).
- Gold guard: if `treasury.gold < 50` → refund AP, return `fail`, deduct nothing.
- Deduct: `treasury.gold -= 50; treasury.expenditure_this_cycle += 50`.
- Level: `target.rank -= 0.50 * (target.rank - int(target.rank))`.
- Health: `target.health = target.health - 0.50 * target.health` (keep as the model's type; if `health` is int, use `int(...)` consistent with the model — match the field's existing type).
- Reputation: `mayor.adjust_reputation(target.id, -10)`.
- No level-1 guard (do **not** skip level-1 targets).
- Return `ActionResult(action="Sabotage", actor_id="mayor", target_id=target.id, outcome="decisive", delta=-50.0, narrative=..., dramatic=True)`.
Add `"Sabotage": 1` to `ACTION_COSTS` and `"Sabotage": _sabotage` to `_ACTION_MAP`.
**Test:** `py -c "from engine.mayor.actions import _ACTION_MAP, ACTION_COSTS; print('Sabotage' in _ACTION_MAP, ACTION_COSTS['Sabotage'])"`.
**Done When:** `Sabotage` is in both `_ACTION_MAP` and `ACTION_COSTS` with AP cost 1.
**Stuck If:** `Faction.health` type makes a clean 50%-of-current reduction ambiguous (report the field type before guessing).
- [x] Complete

### Step 2: Add Sabotage to the allowlist
**Build:** Add `"Sabotage"` to `VALID_MAYOR_ACTIONS` in `api/schemas.py`.
**Test:** `py -c "from api.schemas import VALID_MAYOR_ACTIONS; print('Sabotage' in VALID_MAYOR_ACTIONS)"`.
**Done When:** Prints `True`.
**Stuck If:** —
- [x] Complete

### Step 3: Test Sabotage damage + cost (the 7 automated Done-when items)
**Build:** In `tests/test_mayor_act.py` add `class TestSabotage` covering, via direct `execute_mayor_actions([MayorAction("Sabotage", target_id=...)], ...)` (or calling `_sabotage` with AP pre-spent — match the existing test style in the file):
- `test_cost_deducts_ap_and_gold`: success spends 1 AP and treasury −50.
- `test_insufficient_gold_refunds_ap_no_deduction`: treasury < 50 → fail, AP unchanged from start, gold unchanged.
- `test_rank_erodes_fractional_margin`: faction `rank=3.50` → `3.25`; faction `rank=3.00` → `3.00` (no change).
- `test_health_halved`: `health=100` → `50`; `health=50` → `25`.
- `test_single_sabotage_cannot_break_or_delevel`: starting `rank=3.50, health=40` → `level` unchanged (still 3) and `health > 0`.
- `test_reputation_minus_ten`: target rep == prior − 10.
- `test_level_one_target_allowed`: faction `rank=1.40, health=80` is sabotaged (not refused): returns non-fail, `health` reduced.
**Test:** `py -m pytest tests/test_mayor_act.py::TestSabotage -q`.
**Done When:** All seven pass.
**Stuck If:** The 50%-of-current health math and the model's `health` type disagree (e.g. rounding makes 50→25 land at 24/26).
- [x] Complete

### Step 4: Full suite
**Build:** None.
**Test:** `py -m pytest tests/ -q`.
**Done When:** Green except `test_valid_actions_is_exact_demo_set` (still expected-red until BuildProject lands).
**Stuck If:** Any non-Sabotage test regresses.
- [x] Complete

---
⛔ End of Slice 2. Run **inspector** on this slice before continuing.

---

## Slice 3: Build Project (context-aware) + retire old endpoint
**Scope:** One `BuildProject` action that initiates/funds/repairs a domain's base project depending on its state, wired into the API special-case path; the dead `/projects/commission` endpoint is removed; behavior encoded in tests.

### Step 1: Add the context-aware engine entry
**Build:** In `engine/projects/processing.py`, add `mayor_build_or_repair(domain_id, projects, treasury, mayor)`:
- Find an **active, damaged** base project in the domain: a `category=="base"` project with `domain_id in p.domains`, `status != "under_construction"`, `status != "destroyed"`, and `health < 100`. If found → `return repair_project(that, treasury, mayor)`.
- Otherwise → `return mayor_build_base(domain_id, projects, treasury, mayor)` (which finds-or-initiates an under-construction base project and funds a unit).
Export it from `engine/projects/__init__.py` alongside the existing entries.
**Test:** `py -c "from engine.projects import mayor_build_or_repair; print(callable(mayor_build_or_repair))"`.
**Done When:** Importable and callable.
**Stuck If:** Project status vocabulary for "active/damaged" differs from `health < 100` (check `_update_project_status`).
- [x] Complete

### Step 2: Wire BuildProject into the API and allowlist
**Build:** Add `"BuildProject"` to `VALID_MAYOR_ACTIONS` (`api/schemas.py`). In `api/routes/mayor.py`, add a special-case branch in `mayor_act` (mirroring `GrantTaxExemption`/`BreakADeal`) that, for `req.action == "BuildProject"`, calls `mayor_build_or_repair(req.target_id, session.projects or {}, treasury, mayor)`, persists `session.projects`, maps a `fail` result to HTTP 400, and returns a `MayorActResponse` with remaining AP. Do **not** add BuildProject to `_ACTION_MAP` (it is special-cased, like BreakADeal/GrantTaxExemption).
**Test:** `py -c "import api.routes.mayor"` imports clean; `py -c "from api.schemas import VALID_MAYOR_ACTIONS; print('BuildProject' in VALID_MAYOR_ACTIONS)"`.
**Done When:** Module imports and `BuildProject` is in the allowlist.
**Stuck If:** `session.projects` isn't available/persistable on the live session object.
- [x] Complete

### Step 3: Retire the old /projects/commission endpoint
**Build:** Remove the `commission_project` route (`@router.post("/projects/commission")`) and its now-unused imports/`CommissionProjectRequest` if nothing else uses them (`api/routes/mayor.py`, `api/schemas.py`). It used the retired catalog + `build_cost` model. Grep for callers/tests first.
**Test:** `grep -rn "projects/commission\|commission_project\|CommissionProjectRequest" api/ tests/` returns nothing live; `py -c "import api.routes.mayor"` clean.
**Done When:** No live reference to the commission endpoint remains; module imports.
**Stuck If:** A test or the frontend contract depends on `/projects/commission` (report it — frontend is a separate later pass, so a test dependency is the only blocker here).
- [x] Complete

### Step 4: Test Build Project (the 5 automated Done-when items)
**Build:** In `tests/test_mayor_act.py` add `class TestBuildProject` calling `mayor_build_or_repair` directly with a constructed `projects` dict / `Treasury` / `Mayor`:
- `test_initiates_when_none_under_construction`: empty domain → a new base project exists with `status=="under_construction"`, `build_progress==1`; treasury −50, AP −1.
- `test_adds_unit_when_under_construction`: existing under-construction project at `build_progress==1` → `build_progress==2`; treasury −50, AP −1.
- `test_fourth_unit_completes`: project at `build_progress==3` → after build `status=="active"`, `health==100`.
- `test_repairs_active_damaged`: active base project at `health==60` → `health==85`; treasury −30, AP −1.
- `test_insufficient_funds_refunds`: AP 0 → fail, nothing changed; and treasury < cost → fail, AP refunded, nothing changed.
**Test:** `py -m pytest tests/test_mayor_act.py::TestBuildProject -q`.
**Done When:** All five pass.
**Stuck If:** `initiate_base_project` requires catalog data not present in a unit-test fixture (check `BASE_PROJECT_NAMES`).
- [x] Complete

### Step 5: Close the roster-integrity test
**Build:** None — Sabotage and BuildProject now exist, so `TestRosterIntegrity::test_valid_actions_is_exact_demo_set` should go green.
**Test:** `py -m pytest tests/test_mayor_act.py::TestRosterIntegrity -q`.
**Done When:** Both roster-integrity tests pass.
**Stuck If:** The exact-set assertion fails — diff the actual `VALID_MAYOR_ACTIONS` against the expected 7.
- [x] Complete

---
⛔ End of Slice 3. Run **inspector** on this slice before continuing.

---

## Final Slice: Verification, treasury-runs check, full sweep
**Scope:** Edge cases, the treasury-passively-runs automated check, evidence for the two `[human-required]` items, and full spec verification.

### Step 1: Test that the treasury runs without a player action
**Build:** In `tests/test_mayor.py` (or `test_mayor_act.py`), add `test_treasury_runs_without_player_action`: run a few cycles via the runner (reuse the existing `TestMayorCycleIntegration` setup) with **no** mayor actions submitted and assert treasury gold changes across cycles from passive income/maintenance (i.e. the economy advances on its own). Encodes the "treasury runs but not surfaced" automated Done-when item.
**Test:** `py -m pytest tests/test_mayor.py -k treasury_runs_without_player_action -q`.
**Done When:** Test passes — gold differs from its starting value after N cycles with no mayor action.
**Stuck If:** The integration harness requires a mayor action to advance.
- [x] Complete

### Step 2: Headless smoke
**Build:** None.
**Test:** `py main.py --cycles 10`.
**Done When:** Exit 0, no traceback; output shows the sim running (factions/projects active).
**Stuck If:** A KeyError/AttributeError traces to a removed action or the Build/Sabotage wiring.
- [x] Complete

### Final Step: Verify spec Done when items
**Build:** No new code. Confirm all `**Done when:**` items in `mayor_spec.md` are met. The 15 `[automated]` items map to: Slice 1 Step 4 (roster ×2), Slice 2 Step 3 (Sabotage ×7), Slice 3 Step 4 (Build ×5), Final Step 1 (treasury ×1). The 2 `[human-required]` items (treasury not surfaced in demo UI; no stale entrench/Block/collapse normative refs) get evidence: grep the spec for stale terms, and note the demo action surface = the 8 levers (UI absence of treasury controls is verified in the frontend pass).
**Test:** `py -m pytest tests/ -q`. Capture output. `grep -n "entrench\|Block\|collapse" Planning/specs/mayor_spec.md` to confirm only historical notes remain.
**Done When:** Full suite green; every `[automated]` criterion passes via its committed test; both `[human-required]` items have captured evidence.
**Stuck If:** An automated criterion fails and the cause isn't clear from output.
- [x] Complete

---
⛔ Final slice complete. Run **inspector** for final sign-off.

✅ Inspector: PASS — 2026-06-05 21:35 (final sign-off; 1 criterion-wording flag on Done-when #202 — see report)
