# Walkthrough Recommendations — Polis — 2026-06-02

Everything below was found this pass but **not applied** — each is Full-Path or tooling, outside
the walkthrough's Quick-Path fence. Ordered by priority.

## Priority: HIGH

### Retrofit `Done when:` contracts onto the 11 untagged engine specs
- **Area:** `Planning/specs/` — cycle-runner, actions, faction-behavior, personality-system,
  mayor, treasury, projects, special-factions, events, llm-system, llm-profiles.
- **What:** Only 4 of 15 feature specs (audience, player-identity, faction-descriptions, game-ui)
  carry tagged `[automated]`/`[human-required]` Done-when items. The other 11 — the older,
  pre-Plumbline-alignment specs — describe behavior in prose with **no acceptance criteria**.
  Run **architect** per spec to add Done-when items, mapping each `[automated]` one to an
  existing test where the suite already covers it (much of this engine is tested — 276 tests —
  it's just not traceable to spec criteria).
- **Why:** Without tagged criteria, neither `surveyor` (test-backing) nor `inspector` (proof) can
  verify these specs. It's the gap that makes the rest of the framework's guarantees not apply to
  most of the engine. Highest-leverage maintenance action for the project.
- **Effort:** large (spread across 11 specs — do a few at a time).
- **Path:** Full (architect). **Spec affected:** the 11 listed.

## Priority: MEDIUM

### Run a full `inspector` proof-baseline
- **Area:** all feature specs + the Vue UI.
- **What:** Tests pass, but no dynamic Done-when *proof* was run this walkthrough — a full
  inspector pass across 15 specs + the live server + playwright UI is its own focused effort.
- **Why:** "Tests green" ≠ "Done-when proven," especially for the `[human-required]` UI criteria
  in game-ui (16) and the audience/faction-descriptions UI items. Sequence it **after** the HIGH
  retrofit so inspector has tagged criteria to verify.
- **Effort:** medium–large. **Path:** Full.

## Priority: LOW

### Fix the stale expected-files list in `tools/audit.py`
- **Area:** `tools/audit.py`.
- **What:** The audit warns that `engine/actions/unit.py` and `engine/actions/membership.py` are
  missing. Those action files were **intentionally removed** (decision
  `2026-05-25-remove-larp-units-multiplayer.md`). Drop them from the audit's expected-file list.
- **Why:** The warning flags an intended removal as a problem — noise that erodes trust in the
  audit. Also: the audit reports only 3/19 actions and 0/23 traits "verified in code" — worth a
  glance to confirm that's a detector limitation, not real drift.
- **Effort:** small. **Path:** tooling (walkthrough doesn't edit tools unattended).

### Resolve the `budget_allocation` literal in `llm-system_spec.md`
- **Area:** `Planning/specs/llm-system_spec.md:227`; `audience_spec.md` Valid-Deal-Terms Done-when 1.
- **What:** The audience criterion says `budget_allocation` should appear in **no spec**. It's
  gone from all backend source and the prompt, but survives as a benign "…no `budget_allocation`…"
  cross-reference note in llm-system_spec. Either reword that note, or relax the criterion to
  "no live use." Also: that criterion's "no spec/reference/source" half has **no backing test** —
  add a repo-wide grep assertion if the strict form is intended.
- **Why:** Tiny correctness gap between the criterion's literal wording and reality; harmless today.
- **Effort:** small. **Path:** Full (touches a spec) — reconcile via architect.

### Establish a coverage baseline
- **Area:** `backend/` dev tooling.
- **What:** `pytest-cov` isn't installed, so there's no coverage map. Add it as a dev dependency
  and capture a baseline so future walkthroughs can target genuinely-uncovered paths instead of
  guessing.
- **Why:** Enables coverage-driven test work (Phase 3) on later passes.
- **Effort:** small. **Path:** Full (adds a dependency).
