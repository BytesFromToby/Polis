# Walkthrough Log — Polis — 2026-06-17 (PM, second run)

Second maintenance pass the same day, covering what shipped since the morning run: the four Public
scales (piety/unrest/consumption/confidence), the public-needs ↔ food-supply spec split, and the
Geometric-pottery UI. The morning run (`*_2026-06-17.md`) covered the older specs; this pass focuses
on the new work. Quick-Path fixes applied; Full-Path → Recommendations (`*_pm.md`). Nothing committed.

## Phase 1 — Baseline
- **Backend suite:** `py -m pytest tests/ -q` → **556 passed**.  Tree clean (only local `.claude/launch.json`).
- **Frontend:** `npm run build` → exit 0.  `tools/validate_state.py` → PASS, 0 errors.
- **Inspector (subagent, scoped to the new specs):** 47 PROVEN / 4 WEAK / 3 UNBACKED across 54
  `[automated]` items. Core logic (scales, wire, food chains, event gates + flagships) densely +
  faithfully backed; no tautologies (the consumption-PARITY one was already remediated). Report:
  `output/walkthrough/InspectorAudit_2026-06-17_pm.md`.

## Phase 2 — Spec drift
- **Drift is low on the new work** — every scale constant in the specs is present in code; the UI
  has no `commission`/`entrench`; the game-ui spec matches what was built (just built spec-first +
  inspected).
- **[applied, Quick-Path] Dead code from the dropped Standing/World:** removed five orphaned
  helpers in `GameView.vue` — `world()`, `chaosDisplay()`, `topReputation()`, `repColor()`, and
  `needBandColor()` (the last superseded by `bandClass()` in the Mayor-panel rebuild). All confirmed
  unused (1 self-ref each). `npm run build` exit 0 after; no dangling refs. *(This was logged as a
  deferred deviation in `Deviations_pottery-ui`; now cleaned.)*
- **[deferred] special-factions "The Public's Role in Faction Politics"** — still unimplemented in
  `behavior.py` (0 refs) and now superseded by the Confidence posture modifier. Carried from the AM
  run; → Recommendations (architect).

## Phase 3 — Test coverage
- **[applied, Quick-Path] `test_piety.py::test_target_clamped_at_100`** — the audit flagged the
  piety_target top clamp as untested (the parity test lands exactly on 100). Added a test with
  supply far above parity-demand asserting it clamps to 100, not overflow. Suite **557 green**.
- **[deferred] W2/W4 clamp edges** — the unrest `[0,100]` and production-wire `[EFF_MIN,EFF_MAX]`
  clamps are **unreachable by real inputs** (max unrest pressure 80 < 100; max efficiency 1.10 <
  1.25). Their tests are smoke-only by necessity; not forcing artificial coverage. → Recommendations
  (decide: keep the defensive clamps or drop them).

## Phase 4 — Documentation
- **[applied] `architecture.md`** — the `engine/needs/` listing omitted `scales.py` (the new
  seven-scale drivers + production wire); added it to both the tree and the directory table.
- Verified `data-models.md` is **not** stale on ThePublic — it intentionally defers the entity to
  `special-factions_spec.md` (which carries the piety/unrest/consumption fields). No change.

## Phase 5 — Tools
- No new tool. The resting-band health tool (proposed in the AM run) remains the best gap — the
  consumption-Sodden FAIL and the open piety-Zealous debt are the same defect class with no guard.
  Carried to Recommendations.

## Phase 6 — Recommendations
- Read the deviation history (now 27 builds incl. piety-unrest/consumption/confidence/pottery-ui).
  The morning's plan-quality read holds and is **reinforced**: the foreman's *baked numeric tuning
  literals* keep being slightly wrong (consumption `CONSUMPTION_PARITY` mis-measure → the only
  inspector FAIL of the month). Healthy otherwise (deviations meaningful, few stucks).
- `output/walkthrough/Recommendations_2026-06-17_pm.md` written.

## Summary
- **557 backend green** (556 → 557); frontend builds clean. No regressions.
- **Applied (Quick-Path):** removed 5 dead helpers in `GameView.vue`; added the piety clamp test;
  fixed `architecture.md`'s `needs/` listing.
- **Deferred → Recommendations (PM):** the frontend has **no test runner** (3 game-ui `[automated]`
  items unbacked), plus the still-open AM items (special-factions reconcile, piety-Zealous retune,
  resting-band tool, treasury `guard_paid` doc, cycle-runner orchestration tests).
- Nothing committed.
