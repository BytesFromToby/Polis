# Walkthrough Recommendations — Polis — 2026-06-06

Everything below was found this pass but **not applied** — each is Full-Path or tooling, outside
the walkthrough's Quick-Path fence. Ordered by priority.

**State of the project this pass:** healthy. 316 tests green; inspector proved **98/98**
pytest-backed automated Done-when criteria; surveyor found **no code drift** — every drift is
*stale spec text* lagging the demo redesign. Two Quick-Path doc-accuracy fixes were applied (see
WalkthroughLog [7][8]). The prior HIGH item (retrofit Done-when onto untagged specs) has largely
progressed: actions, cycle-runner, mayor, and projects now carry tagged criteria (was 4 specs in
2026-06-02, now ~9).

## Priority: MEDIUM

### Purge stale `Block` references from three specs
- **Area:** `Planning/specs/personality-system_spec.md` (lines 49–66), `llm-system_spec.md` (line 296),
  `audience_spec.md` (lines 249, 262).
- **What:** `Block` was removed engine-wide in the redesign, but these specs still treat it as live:
  - personality-system weight tables award `Block` (`Harm+20,Steal+10,Block+5`; `Protect+25,Block+15`;
    `Protect+20,Block+20`; `distrusts X → Block+15`) and use the pre-redesign relational table.
  - llm-system `VALID_ACTIONS = {…,"Block"}` — and that constant no longer exists in code at all
    (prompt_builder.py:283 uses the string `"BuildProject, Protect, Grow"`). Section is self-marked
    superseded but the dead block remains.
  - audience: "biases their actions toward **Harm/Block**…" and the Faction-Breach condition
    "not cancelled by a **Block**…" (a now-meaningless condition).
- **Why:** These are the only spec↔code disagreements in the project. Code is correct; specs mislead.
  The historical removal notes (in actions/cycle-runner/faction-behavior/mayor specs) are fine — leave
  those; this is about the *live, normative* references above.
- **Effort:** small. **Path:** Full (architect — reconcile/delete; for personality-system, decide
  whether the weight table is still owned here or fully delegated to faction-behavior_spec).
- **Spec affected:** personality-system, llm-system, audience.

## Priority: LOW

### Reconcile the `budget_allocation` "no spec" clause
- **Area:** `audience_spec.md` criterion #81; the literal also survives in `llm-system_spec.md`.
- **What:** The criterion says `budget_allocation` appears in *no spec/reference/source*. The
  backend-source half is tested (`test_budget_allocation_not_a_live_term`); the "no spec" half is
  **untested and literally false** — the string sits in audience_spec and llm-system_spec (their own
  removal notes). Either reword the criterion to "no live use / no backend source," or purge the
  literal from spec text and add a repo-wide grep assertion. Carried from 2026-06-02.
- **Why:** Tiny correctness gap between a criterion's wording and reality; harmless today.
- **Effort:** small. **Path:** Full (architect).

### Add formal Done-when criteria to the four pre-convention specs
- **Area:** `special-factions_spec.md`, `events_spec.md`, `llm-system_spec.md`, `treasury_spec.md`.
- **What:** These predate the Done-when convention — they describe behavior in prose with no tagged
  `[automated]`/`[human-required]` acceptance criteria. They are well-covered by tests in practice
  (`test_special_factions.py`, `test_events*.py`, `test_llm*.py`, `test_mayor.py`), but neither
  surveyor nor inspector can verify them against criteria. Run **architect** to add Done-when items,
  mapping each `[automated]` one to the existing test that already covers it.
- **Why:** Closes the last gap in spec↔test traceability. Reduced scope vs. 2026-06-02 (then 11 specs;
  now 4) because actions/cycle-runner/mayor/projects have since been tagged.
- **Effort:** medium (4 specs; do a few at a time). **Path:** Full (architect).

### Back game-ui's frontend-only automated criteria with a JS/Playwright guard
- **Area:** `game-ui_spec.md` (6 `[automated]` items) + `frontend/`.
- **What:** The 6 automated items are frontend-only (api.js has no `commission`; no MeetWithFaction or
  `entrench` controls; faction-block format; modal 8-lever roster; header gold; `npm run build` exit 0).
  No JS/Playwright test encodes them — inspector verified 5 by static inspection and did not run the
  build. Add a lightweight Playwright check or a frontend grep guard so these are mechanically proven.
- **Why:** The only specced criteria with zero automated backing.
- **Effort:** medium. **Path:** Full. **Spec affected:** game-ui.

### Fix the stale expected-files list in `tools/audit.py`
- **Area:** `tools/audit.py`.
- **What:** Still warns `engine/actions/unit.py` and `engine/actions/membership.py` are missing —
  intentionally removed (decision `2026-05-25-remove-larp-units-multiplayer.md`). Drop them from the
  expected-file list. Also worth a glance: the audit reports only 3/19 actions and 0/23 traits
  "verified in code" — confirm that's a detector limitation, not real drift. Carried from 2026-06-02.
- **Why:** The warning flags an intended removal as a problem — noise that erodes trust in the audit.
- **Effort:** small. **Path:** tooling (walkthrough doesn't edit tools unattended).

### Establish a coverage baseline
- **Area:** `backend/` dev tooling.
- **What:** `pytest-cov` isn't installed, so there's no coverage map to target genuinely-uncovered
  paths. Add it as a dev dependency and capture a baseline. Carried from 2026-06-02.
- **Why:** Enables coverage-driven test work on later passes instead of guessing.
- **Effort:** small. **Path:** Full (adds a dependency).
