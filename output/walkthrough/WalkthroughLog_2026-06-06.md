# Walkthrough Log — 2026-06-06

## Phase 1 — Baseline

### [1] Test suite
- **Area:** backend/tests
- **Finding:** `py -m pytest tests/ -q` → **316 passed in ~1.5s**
- **Action:** none (baseline)
- **Tests:** pass

### [2] Health scripts
- **Area:** tools/audit.py, tools/validate_state.py
- **Finding:**
  - audit.py: ran OK. WARNING — expects `engine/actions/unit.py` and `engine/actions/membership.py` which don't exist (stale path assumptions in the audit script). 155 entity fields / 24 classes, 19 actions (3 verified in code), 23 traits (0 verified), 7 formulas.
  - validate_state.py: PASS — 0 errors, 2 warnings (units.json is DB-only/runtime-generated; expected).
- **Action:** none yet; stale audit paths noted for Recommendations.
- **Tests:** n/a

### [3] Inspector proven-state baseline (background subagent — fresh eyes)
- **Area:** all specs in Planning/specs/ vs backend/tests
- **Finding:** **98/98 pytest-backed automated Done-when criteria PROVEN**, suite green, **zero failing or contradicted** criteria. game-ui's 6 automated items are frontend-only (no pytest/JS backing; 5 verified by static inspection, `npm run build` not run). Flagged stale spec text (Block refs in personality-system/llm-system/audience) and 4 specs with no acceptance criteria (special-factions, events, llm-system, treasury).
- **Action:** logged; drift routed to Phase 2 / Recommendations.
- **Tests:** pass (316)

## Phase 2 — Spec drift (surveyor)

Ran the **surveyor** skill. Full report: `output/surveys/Survey_2026-06-06.md`. Verdict: **6 findings** (Drift 4 · Untested 2). **All drift is stale spec text — the code is correct; the specs lag the demo redesign that removed `Block`.** Every drift fix is "fix the spec via architect" = Full-Path → routed to Recommendations, **not applied**.

### [4] Stale `Block` references in specs (DEFERRED — Full-Path)
- **Area:** personality-system_spec.md:49–66 (weight tables award Block); llm-system_spec.md:296 (`VALID_ACTIONS` lists Block + the constant no longer exists in code); audience_spec.md:249 ("Harm/Block") & :262 (Breach condition cites Block)
- **Finding:** Block was removed engine-wide; these are live (non-historical) spec references to a dead mechanic.
- **Action:** DEFERRED — Full-Path (architect owns specs). See Recommendations.
- **Tests:** n/a

### [5] `budget_allocation` "no spec" clause untested + contradicted (DEFERRED)
- **Area:** audience_spec criterion #81
- **Finding:** backend-source half is tested; the "no spec" half is untested and literally false (string survives in two specs' removal notes). Carried from 2026-06-02.
- **Action:** DEFERRED — Full-Path (reword criterion via architect, or add grep test after purge).
- **Tests:** n/a

## Phase 3 — Test coverage

### [6] No new Quick-Path tests warranted this pass
- **Area:** backend/tests
- **Finding:** Inspector confirmed all pytest-able automated criteria are already backed (316 tests). The two remaining gaps are not Quick-Path: (a) game-ui's frontend-only criteria need Playwright/JS, not pytest; (b) the `budget_allocation` "no spec" test would fail today because the literal still sits in spec text — must reconcile the spec (architect) before encoding it. Adding either now would be wrong.
- **Action:** none (no safe, passing test to add). Both routed to Recommendations.
- **Tests:** pass (316)

## Phase 4 — Documentation

### [7] Corrected stale "ahead of code" disclaimers in reference docs (APPLIED)
- **Area:** Planning/reference/data-models.md:9, formulas.md:5
- **Finding:** Both still warned the reference was "*ahead of code until the redesign build lands*". That build has landed (commits 28ffb87/39243b4/522389d + the actions/cycle redesign) and the inspector just verified the code matches — so the disclaimers were actively misleading (a reader would distrust current, as-built reference docs).
- **Action:** APPLIED — replaced the status note with "redesign build landed (2026-06-06), inspector-verified, now as-built." No model/formula *content* changed; status note only. Quick-Path.
- **Tests:** pass (316)

### [8] Fixed stale source path in formulas.md (APPLIED)
- **Area:** Planning/reference/formulas.md:4
- **Finding:** "Verified against `scr/engine/formulas.py`" — wrong path (typo + pre-restructure); actual file is `backend/engine/formulas.py`.
- **Action:** APPLIED — corrected the path. Quick-Path.
- **Tests:** pass (316)

### [9] CLAUDE.md file maps & spec index — checked, accurate
- **Area:** CLAUDE.md (root, backend, Planning)
- **Finding:** Backend dir map matches the engine tree; Planning spec index lists all 16 specs correctly; root file map current. No edits needed.
- **Action:** none.
- **Tests:** n/a

## Phase 5 — Tools

### [10] tools/audit.py stale expected-files (DEFERRED — tooling)
- **Area:** tools/audit.py
- **Finding:** Still warns `engine/actions/unit.py` and `engine/actions/membership.py` are missing — those were intentionally removed (decision 2026-05-25-remove-larp-units-multiplayer). Carried from 2026-06-02. Orphaned `__pycache__/*.pyc` for those deleted modules also linger but are gitignored (harmless; not the cause of the warning).
- **Action:** DEFERRED — walkthrough does not edit tooling unattended. See Recommendations.
- **Tests:** n/a

## Phase 6 — Recommendations
Compiled to `output/walkthrough/Recommendations_2026-06-06.md`.
