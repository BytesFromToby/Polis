# Walkthrough Log — Polis — 2026-06-17

Autonomous maintenance pass. Quick-Path fixes applied inline; Full-Path → Recommendations.
Nothing committed.

## Phase 1 — Baseline

### [1] Test suite
- **Area:** `backend/tests/` (full suite)
- **Finding:** `cd backend && py -m pytest tests/ -q` → **550 passed** (0 fail).
- **Action:** none (baseline healthy).
- **Tests:** PASS (550).

### [2] Health scripts (`tools/`)
- **Area:** `tools/audit.py`, `tools/validate_state.py`, `tools/check_game_ui.py`
- **Finding:** `validate_state.py` → **PASS, 0 errors, 2 warnings** (both expected: `units.json`
  is DB-only/runtime, not a data file). `audit.py` → regenerated `AUDIT.md`, `audit.xlsx`, and
  CSVs cleanly (173 fields / 25 classes / 19 actions / 23 traits / 8 formulas). Note: only 3 of 19
  actions and 0 of 23 traits are "verified in code" by the audit's heuristic — a known limitation
  of the static scan, not a defect (the 4th–19th actions resolve via dispatch tables the heuristic
  doesn't follow).
- **Action:** none. (audit.py rewrote its generated artifacts in the working tree — left
  uncommitted per walkthrough rules; flagged in Recommendations as a possible .gitignore candidate.)
- **Tests:** PASS (unchanged).

### [3] Inspector — what is actually proven
- **Area:** all specs with `[automated]` Done-when items
- **Finding:** the four newest features (withhold, piety+unrest, consumption, confidence) carry
  fresh fresh-eyes inspector reports in `output/inspect/` (all PASS, consumption after a FAIL→fix).
  Spawned a fresh-eyes inspector subagent to audit the **older** specs' Done-when→test backing
  (the "what's proven" gap) — running in background; result recorded below when it returns.
- **Action:** Inspector subagent returned: **~95 PROVEN / 6 WEAK / 5 UNBACKED** across the older
  specs. Core-logic specs (actions, mayor, treasury, projects, audience, food-supply, events) are
  high-fidelity (forced-outcome tests). Nearly every gap is concentrated in `test_cycle.py` (a
  smoke-test stub) — 5 cycle-runner orchestration criteria unbacked/weak + 3 tautological tests.
  Full report: `output/walkthrough/InspectorAudit_2026-06-17.md`. Acted on in Phase 3.
- **Tests:** PASS (baseline 550).

## Phase 2 — Spec drift (surveyor)

### [4] Ran surveyor (static spec↔code)
- **Area:** core-logic specs in `Planning/specs/`
- **Finding:** 3 findings — (1) **Unimplemented + superseded:** special-factions "Role in Faction
  Politics" (disposition→faction effects) has no code, and is superseded by the Confidence posture
  modifier. (2) **Undocumented:** `Treasury.guard_paid_this_cycle` not in treasury_spec. (3)
  **Untested:** the cycle-runner orchestration cluster (same as the inspector audit). The four
  newest features' specs (withhold/piety+unrest/consumption/confidence) verified clean against code.
- **Action:** Findings (1) and (2) are Full-Path (spec/architect) → **Recommendations**. Finding
  (3)'s test gaps → Phase 3. Survey written to `output/surveys/Survey_2026-06-17.md`.
- **Tests:** unchanged (static pass).

## Phase 3 — Test coverage

### [5] Hardened the tautological cycle tests + added coverage  (Quick-Path)
- **Area:** `backend/tests/test_cycle.py`
- **Finding:** 3 tautological assertions (`faction_actions >= 0`, `isinstance(events, list)`,
  `utilization >= 0`) and unbacked Done-whens (Skip-exclusion, utilization = Σ level, no stale
  carryover).
- **Action (applied):**
  - `test_domain_utilization_recalculated` → now asserts **utilization == Σ level** (snapshotted
    pre-cycle, since the runner recomputes at the top from entering levels). Added
    `test_utilization_has_no_stale_carryover` (sole street faction removed → utilization 0).
  - `test_faction_actions_counted` → bounded `0..len(factions)` (was `>= 0`). Added
    `test_faction_actions_excludes_skip` (force all factions to Skip via `random()→0.0` → count 0)
    and `test_faction_actions_counts_actors_when_none_skip` (`random()→0.99` → ≥1).
  - The heavier orchestration tests (initiative re-roll needs an observability hook; treasury-order
    + build_actions-reset need a Mayor/Treasury/projects fixture) → **Recommendations**, not added
    fragile/unattended.
- **Tests:** PASS — `test_cycle.py` 9 passed; full suite **553 passed** (was 550).

## Phase 4 — Documentation  (Quick-Path)

### [6] Fixed two stale doc lines from the food-supply split
- **Area:** `backend/CLAUDE.md`, `Planning/CLAUDE.md`
- **Finding:** `backend/CLAUDE.md` still described `engine/needs/` as "harvest chain
  (public-needs_spec)" — stale after the chain moved to food-supply_spec and `scales.py` was added.
  `Planning/CLAUDE.md`'s public-needs index line still said "(piety/unrest scales pending)" — all
  seven scales now shipped.
- **Action (applied):** updated both lines to the as-built structure (needs = bands/drift/scales +
  the chain under food-supply; public-needs index lists all seven scales + the Guard lever + the
  production wire).
- **Tests:** N/A (docs).

## Phase 5 — Tools

### [7] Tool gap identified
- **Area:** `tools/`
- **Finding:** existing tools (audit, validate_state, check_game_ui) pass. No tool guards **resting
  band health** holistically — the gap that let the consumption Sodden-pin (inspector FAIL) and the
  piety-Zealous debt through.
- **Action:** DEFERRED — new tool file is Full-Path. Proposed `tools/resting_bands.py` in
  Recommendations (MEDIUM). Also noted: `audit.py` dirties the tree with generated artifacts (LOW).
- **Tests:** N/A.

## Phase 6 — Recommendations

### [8] Compiled prioritized recommendations + read deviation history
- **Area:** `output/deviations/` (26 build logs)
- **Finding:** deviation density is **healthy** — most builds 1–6 meaningful rows (real bugs caught,
  spec-corrections), not trivial-dense; only 3/26 mention any "stuck" (no chronic
  under-specification). Two recurring low-grade plan-quality patterns: foreman occasionally bakes a
  wrong numeric example/tuning literal (projects "6 0", piety "two sources", consumption PARITY —
  builder catches each against spec), and names the behavior entry point `decide_action` (×4) when
  it's `select_faction_action`.
- **Action:** wrote `output/walkthrough/Recommendations_2026-06-17.md` — 4 MEDIUM (special-factions
  reconcile, cycle-runner coverage, piety retune, resting-band tool) + 3 LOW (treasury doc, audit
  artifacts, foreman plan-quality). Nothing applied beyond the Quick-Path fixes logged above.

---

## Summary
- **Baseline → end:** 550 → **553 green**. No regressions.
- **Applied (Quick-Path):** hardened `test_cycle.py` (killed 2 of 3 tautologies, added 3 real
  tests); fixed 2 stale doc lines (`backend/CLAUDE.md`, `Planning/CLAUDE.md`).
- **Deferred → Recommendations:** 7 items (4 MEDIUM / 3 LOW). Highest-value: reconcile the
  superseded special-factions section, retune piety off its Zealous pin, and add a resting-band
  health tool (the consumption-FAIL defect class has no guard).
- **Nothing committed** — all changes left uncommitted for review.
