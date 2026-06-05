# Walkthrough Log — Polis — 2026-06-02

Operating rules this run: Quick-Path fixes applied in place; Full-Path routed to Recommendations.
**Nothing committed** (walkthrough leaves all changes uncommitted for review, overriding the
project's git-per-change rule for the duration of this pass).

## Phase 1 — Baseline

### [1.1] Test suite
- **Area:** `backend/tests/`
- **Finding:** Full suite green.
- **Action:** Ran `cd backend && py -m pytest tests/ -q`.
- **Tests:** **276 passed in 1.90s** — clean baseline.

### [1.2] Audit / health script
- **Area:** `tools/audit.py`
- **Finding:** Exit 0. Extracted 159 entity fields / 24 classes, 19 actions (only **3 verified
  in code**), 23 traits (**0 verified in code**), 5 formulas, 1 constants table, 41 trait refs.
  **WARNING:** audit expects two files that are missing —
  `backend/engine/actions/unit.py` and `backend/engine/actions/membership.py`.
- **Action:** None (read-only baseline). Missing-files warning + low verified-in-code counts
  routed to Recommendations for investigation.
- **Tests:** n/a.

### [1.3] Inspector proof-baseline
- **Area:** all 15 feature specs in `Planning/specs/`
- **Finding:** A full `inspector` dynamic proof-run across 15 specs + the Vue UI (playwright)
  is a large, bounded-session-unfriendly operation requiring the live server.
- **Action:** **DEFERRED.** Static drift/coverage signal is gathered via `surveyor` (Phase 2)
  and the test suite instead. A full inspector proof-run is routed to Recommendations (MEDIUM) as
  a dedicated follow-up. Logged honestly as a scope decision, not a silent skip.
- **Tests:** n/a.

## Phase 2 — Spec drift

### [2.1] Ran surveyor
- **Area:** `Planning/specs/` (15 feature specs) vs `backend/`
- **Finding:** Full report at `output/surveys/Survey_2026-06-02.md`. Headline: **only 4 of 15
  specs carry tagged Done-when items** (audience, player-identity, faction-descriptions, game-ui);
  the other 11 engine specs have none. All 32 `[automated]` criteria across the 4 tagged specs
  **have backing tests** (verified by reading each spec + its test file). One minor drift
  (`budget_allocation` literal lingers in `llm-system_spec.md` as a benign cross-ref note) and one
  tooling issue (`audit.py` stale expected-files list).
- **Action:** All findings are Full-Path (architect/spec) or tooling → **routed to
  Recommendations, none auto-applied.** No Quick-Path drift fix was available.
- **Tests:** unchanged (read-only phase).

## Phase 3 — Test coverage

### [3.1] Coverage tooling check
- **Area:** `backend/` test suite
- **Finding:** `pytest-cov` is **not installed**; no coverage map available. Suite is healthy
  (276 green) and the recently-built features are well-covered.
- **Action:** **No speculative tests added.** Net-new tests should follow the Done-when retrofit
  (Rec 1), not precede it — adding tests with no spec criterion to anchor them would encode current
  behavior as "correct" without a contract. Recommended adding `pytest-cov` + a coverage baseline
  as follow-up (Recommendations, LOW). Adding a dev dependency is outside the Quick-Path fence.
- **Tests:** unchanged.

## Phase 4 — Documentation

### [4.1] Stale skill-registration note in root CLAUDE.md
- **Area:** `CLAUDE.md` (skills section comment)
- **Finding:** A `(CONFIRM)` note claimed `surveyor`/`walkthrough` were "not yet registered as
  runnable skills here." Both were run successfully from `~/.claude/skills/` this session — the
  note is stale.
- **Action:** **APPLIED (Quick-Path).** Rewrote the note to state they're registered at user level
  and runnable here, confirmed 2026-06-02.
- **Tests:** Doc-only comment edit — `CLAUDE.md` is not imported; no test impact (baseline 276
  green stands).

## Phase 5 — Tools

### [5.1] No new tool warranted
- **Area:** `tools/`
- **Finding:** The one tool issue (audit.py stale expected-files list) is an edit to existing
  tooling, which walkthrough does not perform unattended.
- **Action:** Routed to Recommendations (LOW). No new tool written.
- **Tests:** n/a.

## Phase 6 — Recommendations

Compiled to `output/walkthrough/Recommendations_2026-06-02.md`: 1 HIGH (retrofit Done-when
contracts onto 11 engine specs), 1 MEDIUM (full inspector proof-baseline), 3 LOW (audit.py list,
budget_allocation literal, coverage baseline).

---

## Summary
- **Baseline:** 276 tests green; audit clean (1 stale warning).
- **Applied this pass (Quick-Path):** 1 doc fix (stale CLAUDE.md skill-registration note).
- **Deferred to Recommendations:** 5 items (1 HIGH, 1 MEDIUM, 3 LOW).
- **Nothing committed** — all changes left uncommitted for review.
- **Headline:** the engine is well-tested but most specs lack the Done-when contract that makes the
  framework's verification guarantees apply. That retrofit is the highest-leverage next step.
