# Deviations — Audience (Mayor Confirmation + Debug)
Blueprint: Planning/blueprints/audience_BP.md
Date: 2026-05-28

| Slice | Step | Deviation | Why |
|-------|------|-----------|-----|
| 1 | 3 | `AudienceResult` field additions (`finalized`, `mayor_terms`, `faction_terms`) were applied during Step 1, not Step 3. | `finalize_audience` (Step 1) depends on those fields. Same change, earlier in sequence. `run_audience` left committing inline, as the blueprint permits. |
| 1 | 6 | Tests placed in a new file `tests/test_audience_finalize.py` rather than appended to `tests/test_llm.py`. | Isolation of the v3 confirmation flow. Accept path driven via `patch.object(audiences, "_call", ...)`; finalize paths build `pending_parsed` with `ResponseParser().parse(...)`, as suggested. |
| 2 | 2 | No `debug` field added to `AudienceResult`. The conclude route reads the debug payload straight from the `state` dict (`state["debug_conclude"]`). | `state` is in scope in the route and already holds the captured debug; same observable result, one fewer field to thread. |
| Final | 2 | Not a code deviation — a coverage flag for inspector. | With the default stub LLM the faction always declines, so the `await-confirm` Accept/Decline UI path cannot be driven without a live/accepting LLM. The confirm/finalize behaviour is covered by backend tests; the UI confirm path needs a live LLM or a temporary accepting stub for human-required evidence. |
