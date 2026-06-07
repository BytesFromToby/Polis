# Decisions: Audience Requires an Active AI
Spec: Planning/specs/audience_spec.md
Date: 2026-06-07

- Gate the audience, not the whole sim — only the player-facing audience entry points
  require an active AI. The cycle sim and automated tests still run in stub mode. Rejected
  removing stub mode entirely because tests drive `begin_audience_step` with
  `LLMConfig(provider="stub")` and the non-audience sim never needs an LLM.
- "Active AI is set" = run `llm_profile_id` set AND resolves to an existing `LLMProfile`;
  no live connection test required. Chosen over a connectivity check because the user's
  intent is "an AI is selected," and requiring a live test would add latency and a new
  failure mode at audience-start. (Profiles can still be tested manually in `LLMSettings`.)
- Enforce in both UI and API. The UI gives the friendly warning + Open Settings shortcut;
  the API reject (HTTP 400, before AP spend) makes the rule testable and unbypassable.
  Rejected UI-only gating because it leaves the silent stub fallback reachable and gives
  no `[automated]` Done-when.
- Reject in `audience_begin` **before** `mayor.spend(AP)` so a blocked attempt wastes no
  action point.
- Warning UX: a small blocking modal (not disabled buttons or an inline banner), with an
  Open Settings button wiring to the existing in-game Settings panel (`showSettings`/
  `LLMSettings`), per the user's choice.
