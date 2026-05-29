# Blueprint: Audience — Mayor Confirmation + Debug
Spec: Planning/specs/audience_spec.md
Date: 2026-05-28

---

## Builder instructions
- Execute steps in order. Do not skip, reorder, or read ahead into the next slice.
- Check off each step when complete: [ ] → [x]
- One step = one logical concern. If a step can't be tested on its own, it's too small — merge it. If it touches more than one concern, split it.
- Deviation: if you do something differently than the step says, note it inline and keep going.
- Stuck: stop immediately. Do not try alternative approaches. Report exactly where and why.

**Scope note:** This blueprint covers only the v3 changes to the audience — the Mayor
Confirmation flow, the deal-status label, and the debug payload. The existing 5-step
negotiation, prompt building, parsing, and deal mechanics are unchanged except where a
step says so. Names to use exactly as in code: `begin_audience_step`,
`reply_audience_step`, `conclude_audience_step` (`engine/llm/audiences.py`);
`AudienceResult`; route handlers `audience_begin/reply/conclude` (`api/routes/mayor.py`);
schemas `AudienceConcludeResponse` etc. (`api/schemas.py`); `MEET_COOLDOWN`
(`engine/mayor/actions.py`); `_RESPONSE_PARSER`, `_MEMORY_WRITER`, `_create_deal`,
`_apply_mayor_terms`, `_apply_faction_terms` (already in `audiences.py`).

---

## Slice 1: Backend — defer deal creation to a finalize step
**Scope:** Concluding an audience no longer creates a deal when the faction accepts; a new finalize step creates or discards it on the Mayor's decision. Faction-decline still finalises inside conclude.

### Step 1: Extract a `finalize_audience` engine function
**Build:** In `engine/llm/audiences.py`, add `finalize_audience(*, state: dict, mayor_accepts: bool, faction, mayor, run_id, cycle, db) -> AudienceResult`. It reads the parsed result the conclude step stashed in `state["pending_parsed"]` (a `ParsedDeal`/parser result holding `accepted`, `mayor_terms`, `faction_terms`, `rep_cost_if_broken`, `memory_note`, `narrative`). Behaviour:
- If `mayor_accepts` is True: call the existing `_create_deal`, `_apply_mayor_terms`, `_apply_faction_terms`; set `deal_id`. Memory note = `parsed.memory_note or "deal reached"`.
- If `mayor_accepts` is False: create no deal, apply nothing; memory note = `parsed.memory_note or "mayor declined terms"`. `deal_id = None`.
- In both branches: write the memory note via `_MEMORY_WRITER.write_note(... note_type="audience" ...)`, and set the cooldown: `mayor.cooldowns[faction.id] = MEET_COOLDOWN` (import `MEET_COOLDOWN` from `engine.mayor.actions`).
- Return an `AudienceResult` carrying the existing step narratives (pull from `state`), `accepted=mayor_accepts and parsed.accepted`, `deal_id`, the final `memory_note`, and `parse_error=parsed.parse_error`.
**Test:** `cd backend && py -m pytest tests/test_llm.py -q`
**Done When:** Module imports and existing audience tests still pass; `finalize_audience` is callable.
**Stuck If:** `MEET_COOLDOWN` is not importable from `engine.mayor.actions` (find its real location and note the deviation).
- [x] Complete

### Step 2: Make `conclude_audience_step` stop committing on accept
**Build:** In `conclude_audience_step`, after `parsed = _RESPONSE_PARSER.parse(...)`:
- Stash the parsed result and raw text on the passed `state` dict: `state["pending_parsed"] = parsed`, `state["step5_raw"] = step5_text`, `state["mayor_closing"] = mayor_closing`.
- Remove the current unconditional `_create_deal`/`_apply_*`/`_MEMORY_WRITER` block from this function.
- If `not parsed.accepted` (faction declines): call `finalize_audience(state=state, mayor_accepts=False, ...)` to write the memory note + set cooldown, and return its `AudienceResult` (this is the terminal decline path — but set `accepted=False`). Add a flag to the returned result indicating it is already finalised (see Step 3 — add `finalized: bool` to `AudienceResult`, True here).
- If `parsed.accepted` (faction accepts): do NOT finalize. Return an `AudienceResult` with `accepted=True`, `finalized=False`, `deal_id=None`, narratives from state, and `parse_error=parsed.parse_error`. The route keeps the audience state for the finalize call.
**Test:** `cd backend && py -m pytest tests/test_llm.py -q`
**Done When:** A conclude with an **accepting** parsed deal leaves `mayor.deals` empty and returns `accepted=True, finalized=False`; a conclude with a **declining** deal writes a memory note, creates no deal, and returns `finalized=True`. (Encoded as committed tests in Step 6.)
**Stuck If:** Step 5 narrative shown to the player can no longer be separated from the raw `<deal>` text — note how `parsed.narrative` vs `step5_text` differ.
- [x] Complete

### Step 3: Add `finalized` + proposed terms to `AudienceResult`
**Build:** Extend `AudienceResult.__init__` with `finalized: bool = True`, `mayor_terms: list = None`, `faction_terms: list = None` (store `[]` when None). Populate `mayor_terms`/`faction_terms` from the parsed result so the conclude response can show the Mayor what they're confirming. Keep `run_audience` (the all-in-one helper) working — it should set `finalized=True` and may keep committing inline (it is used by tests/CLI, not the stepwise flow); note this as an accepted deviation if you leave its behaviour as-is.
**Test:** `cd backend && py -m pytest tests/test_llm.py -q`
**Done When:** Existing `run_audience` stub-flow tests still pass; `AudienceResult` exposes `finalized`, `mayor_terms`, `faction_terms`.
**Stuck If:** A test asserts old `AudienceResult` positional args — update the call, note it.
- [x] Complete
  **Deviation:** The `AudienceResult` field additions (`finalized`, `mayor_terms`, `faction_terms`) were applied during Step 1 rather than here, because `finalize_audience` (Step 1) depends on them. Same change, earlier in the sequence. `run_audience` left committing inline as the blueprint allows.

### Step 4: Schemas for conclude + finalize
**Build:** In `api/schemas.py`:
- Add `proposed_mayor_terms: list[dict] = []`, `proposed_faction_terms: list[dict] = []`, and `finalized: bool = True` to `AudienceConcludeResponse`. Keep `deal_id`, `accepted`, `memory_note`, `parse_error`, `action_points`.
- Add `AudienceFinalizeRequest(BaseModel)` with `mayor_accepts: bool`.
- Add `AudienceFinalizeResponse(BaseModel)` with `accepted: bool`, `deal_id: Optional[str] = None`, `memory_note: str = ""`, `action_points: int`.
**Test:** `cd backend && py -c "import api.schemas"` (and the suite in Step 6).
**Done When:** Schemas import without error.
**Stuck If:** n/a.
- [x] Complete

### Step 5: Route — conclude keeps state on accept; add finalize endpoint
**Build:** In `api/routes/mayor.py`:
- `audience_conclude`: stop unconditionally clearing `session.audience_state` and stop setting the cooldown here (the engine now owns cooldown). After calling `conclude_audience_step`: if `result.finalized` (faction declined) → clear `session.audience_state`. If not finalised (faction accepted) → keep `session.audience_state` (it now holds `pending_parsed`). Return `AudienceConcludeResponse` including `finalized`, and `proposed_mayor_terms`/`proposed_faction_terms` built from `result.mayor_terms`/`faction_terms` via the existing `_term_to_dict` shape.
- Add `POST /mayor/audience/finalize` handler `audience_finalize(user_id, req: AudienceFinalizeRequest, ...)`: requires `session.audience_state` with a `pending_parsed` (else 400 "No audience awaiting confirmation"); resolves `faction` from `state["faction_id"]`; calls `finalize_audience(state=state, mayor_accepts=req.mayor_accepts, faction=faction, mayor=session.mayor, run_id=session.run_id, cycle=session.world.cycle, db=db)`; clears `session.audience_state`; returns `AudienceFinalizeResponse` with `action_points=session.mayor.action_points`.
**Test:** `cd backend && py -m pytest tests/ -q`
**Done When:** Full suite passes; the new endpoint is registered (check `app.routes` or hit it in a TestClient if one exists).
**Stuck If:** `session.world.cycle` / `session.run_id` access differs from the existing conclude handler — mirror exactly what conclude already does.
- [x] Complete

### Step 6: Committed tests for the confirmation flow
**Build:** In `tests/test_llm.py` (or a new `tests/test_audience_finalize.py`), add tests encoding the spec's automated Done-when items. Build the `pending_parsed` by calling `_RESPONSE_PARSER.parse(accept_text, faction, mayor)` (reuse the accepting `<deal>` JSON pattern already in the parser tests) and put it on a `state` dict, OR drive `conclude_audience_step` with a client/config that returns accepting text. Cover:
- conclude with an accepting deal → `mayor.deals` is empty, result `accepted=True, finalized=False`.
- `finalize_audience(mayor_accepts=True)` → exactly one `Deal` in `mayor.deals`, mayor terms applied, faction `committed_action`/`committed_target` set.
- `finalize_audience(mayor_accepts=False)` → no deal, no terms applied, but `faction.id` present in `mayor.cooldowns`.
- conclude with a **declining** deal → no deal, a memory note row written, `finalized=True`, `faction.id` in `mayor.cooldowns`.
- a memory note is written in every finalised branch (accept-confirmed, accept-declined, faction-declined).
**Test:** `cd backend && py -m pytest tests/ -q`
**Done When:** All five tests pass.
**Stuck If:** You cannot get a stub/parsed accept without a live LLM — note it; the parser-built `pending_parsed` path needs no LLM.
- [x] Complete
  **Deviation:** Tests written in a new file `tests/test_audience_finalize.py` (not appended to `test_llm.py`) for isolation. The conclude-accept path is driven by `patch.object(audiences, "_call", ...)`; the finalize paths use `ResponseParser().parse(...)` to build `pending_parsed`, as the blueprint suggested.

### Step 7: `api.js` finalize method + conclude shape
**Build:** In `frontend/src/api.js`, add to `mayor`: `audienceFinalize: (userId, mayor_accepts) => post(\`/users/${userId}/mayor/audience/finalize\`, { mayor_accepts })`. No other change — `audienceConclude` already returns the (now-extended) conclude payload.
**Test:** `cd frontend && npm run build`
**Done When:** Build succeeds; `mayor.audienceFinalize` exists.
**Stuck If:** n/a.
- [x] Complete

---
⛔ End of Slice 1. Run **inspector** on this slice before continuing.

---

## Slice 2: Backend — debug payload per step
**Scope:** Every audience step returns the exact request sent to the LLM (system + messages) and the raw response text, surfaced to the client.

### Step 1: Capture request + raw response in each step function
**Build:** In `engine/llm/audiences.py`, have each step expose its debug data:
- `begin_audience_step` returns (in its state dict, already returned) the `system` and `messages` (messages after the step-1 assistant turn is appended) and `step1_narrative` (raw). Add a `debug` builder: a helper `_debug(system, messages, raw_response) -> dict` returning `{"system": system, "messages": messages, "raw_response": raw_response}`. Stash the per-step debug on the state: `state["debug_begin"]`, set in begin.
- `reply_audience_step`: stash `state["debug_reply"] = _debug(system, messages_used, step3_text)` where `messages_used` is the message list sent to `_call` (i.e. including the mayor_opening user turn, before the assistant reply is appended).
- `conclude_audience_step`: stash `state["debug_conclude"] = _debug(system, messages_used, step5_text)` where `step5_text` is the **raw unparsed** LLM text (with the `<deal>` block intact) and `messages_used` includes the mayor_closing turn.
Use copies so later mutation of `messages` does not change captured debug.
**Test:** `cd backend && py -m pytest tests/test_llm.py -q`
**Done When:** Each step stashes a debug dict with `system`, `messages`, `raw_response`; conclude's `raw_response` contains `<deal>`.
**Stuck If:** The stub client output for step 5 does not contain `<deal>` — confirm via the existing stub tests.
- [x] Complete

### Step 2: Surface debug in schemas + responses
**Build:** In `api/schemas.py`, add `class AudienceDebug(BaseModel)` with `system: str`, `messages: list[dict]`, `raw_response: str`. Add an optional `debug: Optional[AudienceDebug] = None` to `AudienceBeginResponse`, `AudienceReplyResponse`, and `AudienceConcludeResponse`. In `api/routes/mayor.py`, populate each response's `debug` from the corresponding `state["debug_*"]` (begin from `state["debug_begin"]`, reply from `state["debug_reply"]`, conclude from `state["debug_conclude"]`). `AudienceResult` should carry the conclude debug so the route can read it (add a `debug: dict | None = None` field to `AudienceResult` set in conclude).
**Test:** `cd backend && py -m pytest tests/ -q`
**Done When:** Full suite passes; responses include a `debug` object.
**Stuck If:** Pydantic rejects `list[dict]` for messages — use `list[dict]` with `from __future__ import annotations` already present, or `List[dict]`.
- [x] Complete
  **Deviation:** Did not add a `debug` field to `AudienceResult`. The route reads the conclude debug straight from the `state` dict (`state["debug_conclude"]`), which is in scope and already holds it. Same observable result; one fewer field to thread.

### Step 3: Committed tests for the debug payload
**Build:** Add tests asserting: `begin_audience_step` state contains `debug_begin` with non-empty `system`, a `messages` list, and a `raw_response`; after a full begin→reply→conclude with the stub, `debug_conclude["raw_response"]` contains `"<deal>"` and is distinct from the parsed narrative returned to the player.
**Test:** `cd backend && py -m pytest tests/ -q`
**Done When:** Tests pass.
**Stuck If:** n/a.
- [x] Complete

---
⛔ End of Slice 2. Run **inspector** on this slice before continuing.

---

## Final Slice: Frontend — confirm flow, deal-status label, debug controls
**Scope:** `AudienceModal` shows a per-step deal-status label, routes the conclusion through Mayor Accept/Decline (only when the faction accepts), and exposes always-present Show JSON / Debug controls. Plus full spec verification.

### Step 1: Per-step deal-status label
**Build:** In `frontend/src/components/AudienceModal.vue`, add a computed `dealStatus` returning a label from the current `step`: ≤1 → "No terms on the table yet"; 2–3 → "Negotiating"; ≥5 → verdict ("Faction accepts — your decision" when accepted/not yet finalised; "Faction declines" when declined; "Deal sealed"/"You declined" after finalize). Render it as a small status line beneath the latest faction turn.
**Test:** `cd frontend && npm run build`
**Done When:** Build succeeds; a status line renders and changes across steps. (Verified by inspector driving the UI.)
**Stuck If:** n/a.
- [x] Complete

### Step 2: Route conclusion through Mayor confirm
**Build:** Rework `submitClosing`/`done` handling. After `audienceConclude` resolves:
- If `res.finalized` (faction declined): show the terminal "No Deal" banner (existing), no confirm controls.
- If not finalised (faction accepted): set `phase = 'await-confirm'`; show the proposed terms (`res.proposed_mayor_terms`, `res.proposed_faction_terms`) and **Accept** / **Decline** buttons. On click, call `mayor.audienceFinalize(userId, true/false)`, then show the sealed/declined banner and the OK button. Emit `acted` with the finalize result so the parent refreshes AP. Keep the existing `parse_error` display.
**Test:** `cd frontend && npm run build`
**Done When:** Build succeeds. Accept/Decline appear only on faction-accept; faction-decline shows terminal outcome. (Inspector verifies with stub LLM, which declines by default — drive the accept path if a stub accept is available.)
**Stuck If:** The stub never returns an accepting deal, so the Accept path can't be exercised in the UI — note it; the accept path is covered by backend tests, and inspector records the decline path as evidence.
- [x] Complete
  **Deviation:** Not a code change — flagging for inspector: with the default stub LLM the faction always declines, so the `await-confirm` Accept/Decline UI cannot be driven without a live (or accepting) LLM. The confirm/finalize behaviour is covered by backend tests (`test_audience_finalize.py`); the UI confirm path will need a live LLM or a temporary accepting stub to capture human-required evidence.

### Step 3: Show JSON + Debug controls
**Build:** Accumulate the `debug` object from each response (`begin`, `reply`, `conclude`) into a `debugLog` array on the component. At the bottom of the modal, add two always-present, collapsed-by-default controls (e.g. `<details>`): **Show JSON** renders, per interaction, the request JSON (`system` + `messages`); **Debug** renders the full per-call history — each call's request (system + messages) and its `raw_response`. Replace/extend the existing "Raw JSON" `<details>` so it is not duplicated.
**Test:** `cd frontend && npm run build`
**Done When:** Build succeeds; both controls render collapsed and expand to their payloads. (Inspector verifies.)
**Stuck If:** n/a.
- [x] Complete

### Final Step: Verify spec Done when items
**Build:** No new code. Confirm all `audience_spec.md` **Done when:** items are met.
**Test:** Run `cd backend && py -m pytest tests/ -q` — the `[automated]` items (conclude-no-commit, finalize-true-creates, finalize-false-no-deal-but-cooldown, faction-decline-finalises, memory-note-every-branch, debug payload present, conclude raw includes `<deal>`) pass via their committed tests. For `[human-required]` items (Accept/Decline only on accept; per-step status label; Show JSON / Debug controls), rebuild the frontend and have inspector drive the audience and capture screenshots.
**Done When:** Every `[automated]` criterion passes via its committed test; every `[human-required]` criterion has captured evidence.
**Stuck If:** An automated criterion fails and the cause is not clear from the output.
- [x] Complete
  **Note:** All `[automated]` criteria pass (247 backend tests). `[human-required]` UI criteria (per-step status label, Accept/Decline only on accept, Show JSON / Debug controls) are left for **inspector** to drive and screenshot — builder does not run inspector.

---
⛔ Final slice complete. Run **inspector** for final sign-off.
