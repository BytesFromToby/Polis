# Inspection Report — Audience Requires an Active AI (final sign-off)

- **Feature:** Active-AI Requirement (audience_spec v5)
- **Spec:** `Planning/specs/audience_spec.md` § "Active-AI Requirement" (lines 52–79)
- **Blueprint:** `Planning/blueprints/audience-requires-active-ai_BP.md`
- **Date:** 2026-06-07
- **Inspector:** fresh-eyes pass (did not build this feature)

## Summary

| Verdict | Count |
|---|---|
| PASS | 3 |
| FAIL | 0 |
| needs-human | 3 |

- Automated tests: `tests/test_audience_requires_ai.py` — **3 passed**.
- Full suite: `tests/` — **345 passed**.
- Frontend: `npm run build` — **succeeded**.
- Backend guard confirmed in `audience_begin` and sits **before** any `mayor.spend(...)`.

---

## Automated Done-when items

### 1. PASS — unset `llm_profile_id` → HTTP 400, no AP spent
Spec (line 74): `POST /mayor/audience/begin` on a run whose `llm_profile_id` is unset returns HTTP 400 and leaves `mayor.action_points` unchanged.

Encoded by `test_begin_rejected_when_no_profile`
(`backend/tests/test_audience_requires_ai.py:69`) — builds a session with `profile_id=None`,
asserts `HTTPException.status_code == 400` and `session.mayor.action_points == 3` (unchanged).

```
tests/test_audience_requires_ai.py::test_begin_rejected_when_no_profile PASSED [ 33%]
```

### 2. PASS — set-but-unresolvable `llm_profile_id` → HTTP 400, no AP spent
Spec (line 75): set but does not resolve to an existing `LLMProfile` → HTTP 400, spends no AP.

Encoded by `test_begin_rejected_when_profile_missing`
(`backend/tests/test_audience_requires_ai.py:83`) — `profile_id="does-not-exist"`, asserts
`status_code == 400` and `action_points == 3`.

```
tests/test_audience_requires_ai.py::test_begin_rejected_when_profile_missing PASSED [ 66%]
```

### 3. PASS — valid active profile → proceeds, 1 AP spent, Step-1 opening
Spec (line 76): with a valid active `llm_profile_id` → spends 1 AP, returns the Step-1 opening.

Encoded by `test_begin_proceeds_with_valid_profile`
(`backend/tests/test_audience_requires_ai.py:97`) — inserts a `provider="stub"` `LLMProfile`,
sets the session profile id, asserts `resp.action_points == 2`, `session.mayor.action_points == 2`
(one spent from 3), and `resp.step1_narrative.strip()` is non-empty.

```
tests/test_audience_requires_ai.py::test_begin_proceeds_with_valid_profile PASSED [100%]
============================== 3 passed in 0.49s ==============================
```

### Backend guard verification (manual code check)
`backend/api/routes/mayor.py:400` — guard `if _get_llm_config(session, db) is None: raise HTTPException(400, ...)`
appears at line 400; the first AP-spending call `mayor.spend(...)` is at line 415. The guard is
therefore **before** any AP spend. `_get_llm_config` returns `None` for unset/unresolvable profile,
matching the spec's "no active AI" definition.

### Full suite
```
345 passed in 1.03s
```

---

## Human-required Done-when items (needs-human)

Static code inspection confirms the wiring exists; these were NOT graded, since driving the
authenticated Vue UI headlessly is out of scope. A human should confirm by clicking.

### 4. needs-human — no AI → both entry points open the warning, open nothing else
Spec (line 77).

Static evidence in `frontend/src/views/GameView.vue`:
- `aiSet()` computed → `return !!this.llmProfileId` (line 302–304).
- `llmProfileId` captured in `refresh()`: `this.llmProfileId = status.llm_profile_id || null` (line 401).
- `openAudience(factionId)`: `if (!this.aiSet) { this.showAiWarning = true; return }` before `audienceFactionId` is set (line 487).
- `openStandaloneAudience()`: `if (!this.aiSet) { this.showAiWarning = true; return }` before `showAudiencePicker` is set (line 491).
- Entry points: faction card `@click="openAudience(f.id)"` (line 59); centre `@click="openStandaloneAudience"` (line 76).

**Human check:** With no active AI set, click **Request Audience ▸** and a faction card's
**Audience ▸**; each should show the warning modal and NOT open the faction picker or AudienceModal.

### 5. needs-human — warning modal shows Open Settings (→ LLMSettings) and Close
Spec (line 78).

Static evidence in `frontend/src/views/GameView.vue` (lines 212–224):
- Modal `v-if="showAiWarning"`, title "Audience unavailable", body "No active AI is set for this game. Set an AI to hold audiences."
- **Open Settings** button → `@click="showAiWarning = false; showSettings = true"` (line 220) — `showSettings` opens the `LLMSettings` panel.
- **Close** buttons → `@click="showAiWarning = false"` (lines 216, 221).

**Human check:** With the modal open, click **Open Settings** → the LLMSettings panel opens;
reopen the modal and click **Close** → it dismisses with no audience started.

### 6. needs-human — valid AI → both entry points start the audience, no warning
Spec (line 79).

Static evidence: with `aiSet === true`, the early-return guards in `openAudience` /
`openStandaloneAudience` are skipped, so `audienceFactionId` / `showAudiencePicker` are set as
before (lines 487–492). Backend `audience_begin` proceeds (covered by automated item 3).

**Human check:** With a valid active AI selected in Settings, click both entry points; each
should start the audience flow with no warning modal.

### Frontend build
```
> polis@0.3.0 build  (vite v8.0.3)
✓ 47 modules transformed.
✓ built in 166ms
```

---

## Verdict

3 automated PASS, 0 FAIL, 3 needs-human (UI items verified by static inspection only; require a
human click-through). No source or spec files were modified during inspection.

Signed: Inspector — 2026-06-07
