# Blueprint: Audience Requires an Active AI
Spec: Planning/specs/audience_spec.md
Date: 2026-06-07

Scope note: this blueprint covers ONLY the v5 "Active-AI Requirement" feature. The rest of
the audience spec is already built and must not be re-planned or modified beyond the single
gate added in Slice 1.

---

## Builder instructions
- Execute steps in order. Do not skip, reorder, or read ahead into the next slice.
- Check off each step when complete: [ ] → [x]
- One step = one logical concern. If a step can't be tested on its own, it's too small — merge it. If it touches more than one concern, split it.
- Deviation: if you do something differently than the step says, note it inline and keep going.
- Stuck: stop immediately. Do not try alternative approaches. Report exactly where and why.
- Test command: `cd backend && py -m pytest tests/ -q`
- Frontend build: `cd frontend && npm run build`

---

## Slice 1: Backend gate on /mayor/audience/begin
**Scope:** `POST /mayor/audience/begin` rejects with HTTP 400 and spends no AP when the run has no active AI (llm_profile_id unset, or set but not resolving to an existing profile); proceeds normally when a valid profile is set. Three committed pytest tests encode the three `[automated]` Done-when items.

### Step 1: Add the active-AI gate in audience_begin
**Build:** In `backend/api/routes/mayor.py`, in `audience_begin`, add a guard **before** the `mayor.spend(ACTION_COSTS.get("MeetWithFaction", 1))` call (and before the faction/cooldown checks is acceptable too, as long as it is before any AP spend). Reuse the existing `_get_llm_config(session, db)` helper:
```python
if _get_llm_config(session, db) is None:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="No active AI is set for this game. Set an AI to hold audiences.",
    )
```
`_get_llm_config` already returns `None` when `session.llm_profile_id` is falsy OR the profile id does not resolve to an existing `LLMProfile`, which is exactly the spec's definition of "no active AI". Do NOT change `_get_llm_config`, `begin_audience_step`, or `StubLLMClient`. The `llm_config=_get_llm_config(...)` argument passed to `begin_audience_step` later in the function stays as-is (it will now always be non-None at that point).
**Test:** `cd backend && py -m pytest tests/ -q` — existing suite still green (no regressions).
**Done When:** The guard is present before any `mayor.spend(...)` in `audience_begin`; full suite passes.
**Stuck If:** Removing the stub fallback path breaks an existing API-level audience test (there should be none — audience tests drive `begin_audience_step` at the engine layer).
- [x] Complete

### Step 2: Write the backend gate tests
**Build:** Create `backend/tests/test_audience_requires_ai.py`. Mirror the test-DB + user setup used by `tests/test_sim_llm_profile.py` / `tests/test_llm_profiles.py`. Drive the route by calling the `audience_begin` function directly (import from `api.routes.mayor`) with a hand-built in-memory session, rather than the full HTTP stack:
- Build a `SimSession` (from `api.sessions`) with `run_id`, a minimal `WorldState`, one `Faction` (with a `Leader`), a `Mayor(action_points=3)`, empty `domains`, and register it via `api.sessions.set_session(user_id, session)`.
- Construct a `User(user_id="u1")`-like current_user whose `user_id` matches, and obtain a real DB `Session` from the test DB fixture (needed for the profile lookup).
- Use `AudienceBeginRequest(faction_id=...)` for the request body and a fresh DB session per call.
- Cleanup: `api.sessions.clear_session(user_id)` between cases (or unique user_ids).

Three tests, one per `[automated]` Done-when item:
1. `test_begin_rejected_when_no_profile` — `session.llm_profile_id = None`; calling `audience_begin` raises `HTTPException` with `status_code == 400`; assert `session.mayor.action_points` is unchanged (still 3).
2. `test_begin_rejected_when_profile_missing` — `session.llm_profile_id = "does-not-exist"` (no matching `LLMProfile` row); raises `HTTPException` `status_code == 400`; `session.mayor.action_points` unchanged.
3. `test_begin_proceeds_with_valid_profile` — insert an `LLMProfile` row directly into the DB with `provider="stub"` (and required columns: name, model, etc. per the `LLMProfile` model); set `session.llm_profile_id` to that profile id. Calling `audience_begin` returns an `AudienceBeginResponse` (no exception), `session.mayor.action_points == 2` (one AP spent), and the response's step-1 text is non-empty (StubLLMClient output).
**Test:** `cd backend && py -m pytest tests/test_audience_requires_ai.py -q`
**Done When:** All three tests pass.
**Stuck If:** The valid-profile case attempts a real network call (means the profile's `provider` is not `"stub"` or `from_profile` isn't reading it) — fix the test profile to `provider="stub"`; do not monkeypatch the network.
- [x] Complete

---
⛔ End of Slice 1. Run **inspector** on this slice before continuing.

---

## Final Slice: Frontend warning modal + spec verification
**Scope:** Both audience entry points check for an active AI and open a blocking warning modal (with Open Settings + Close) when none is set; no picker/AudienceModal opens and no begin call fires. Then verify all spec Done-when items.

### Step 1: Capture the run's active-AI state in GameView
**Build:** In `frontend/src/views/GameView.vue`, store the run's profile id from `sim.status`. Add a data field `llmProfileId: null`, and in `refresh()` set `this.llmProfileId = status.llm_profile_id || null` (the `status` object already carries `llm_profile_id` — `SimStatusResponse.llm_profile_id`). Add a computed `aiSet()` returning `!!this.llmProfileId`.
**Test:** `cd frontend && npm run build` succeeds (no template/script errors).
**Done When:** `aiSet` reflects whether the current run has an active AI; build passes.
**Stuck If:** `sim.status` does not return `llm_profile_id` (it should — verify the field name).
- [x] Complete

### Step 2: Gate both audience entry points behind aiSet
**Build:** In `frontend/src/views/GameView.vue`, add a data flag `showAiWarning: false`. In both `openStandaloneAudience()` and `openAudience(factionId)`, at the top: `if (!this.aiSet) { this.showAiWarning = true; return }` so neither the standalone picker (`showAudiencePicker`) nor the pre-targeted `AudienceModal` (`audienceFactionId`) opens, and no begin request is made.
**Test:** `cd frontend && npm run build` succeeds.
**Done When:** With no active AI, calling either entry point sets `showAiWarning = true` and opens nothing else; with an active AI, behaviour is unchanged.
**Stuck If:** N/A.
- [x] Complete

### Step 3: Add the warning modal markup + actions
**Build:** In `frontend/src/views/GameView.vue`, add a blocking modal shown `v-if="showAiWarning"` using the existing `.modal-overlay` / `.card` pattern (mirror the faction-picker modal). Title "Audience unavailable"; body text "No active AI is set for this game. Set an AI to hold audiences." Two buttons:
- **Open Settings** → `@click="showAiWarning = false; showSettings = true"` (opens the existing `LLMSettings` panel).
- **Close** → `@click="showAiWarning = false"`.
Use existing button classes (`btn-primary` / `btn-subtle`, `btn-sm`) and ensure text uses `var(--text)` so it is readable on the dark modal.
**Test:** `cd frontend && npm run build` succeeds; manual: with no active AI, clicking Request Audience and a faction's Audience ▸ each shows the modal; Open Settings opens LLMSettings; Close dismisses.
**Done When:** The modal renders with both controls and wires to `showSettings` / dismissal as specified.
**Stuck If:** N/A.
- [x] Complete

### Final Step: Verify spec Done when items
**Build:** No new code. Confirm all `**Done when:**` items in the "Active-AI Requirement" section of `audience_spec.md` are met.
**Test:** `cd backend && py -m pytest tests/ -q` (the three committed tests from Slice 1 cover all `[automated]` items) and capture output. For the three `[human-required]` items, rebuild the frontend and capture evidence by driving the UI: (a) no-AI → Request Audience shows the warning and opens no picker; (b) no-AI → faction Audience ▸ shows the warning; (c) the modal's Open Settings opens LLMSettings and Close dismisses; (d) with a valid active AI set, both entry points start the audience with no warning.
**Done When:** Every `[automated]` criterion passes via its committed test; every `[human-required]` criterion has captured evidence (screenshots).
**Stuck If:** An automated criterion fails and the cause is not clear from the output.
- [x] Complete

---
⛔ Final slice complete. Run **inspector** for final sign-off.

INSPECTED 2026-06-07 — 3 PASS · 0 FAIL · 3 needs-human (see output/inspect/Inspect_audience-requires-active-ai_Final_2026-06-07.md)
