# OverrideLLM slice 1 — the deterministic provider

**Date:** 2026-06-22

## What

Added the `"override"` LLM provider (`OverrideLLMClient` in `engine/llm/client.py`) and a transient
`LLMConfig.override` field carrying the operator-supplied outcome. The client never calls a model or
the network; it counts assistant turns like the stub, and on the conclude turn synthesises
`narrative + <deal>` from the supplied `{accepted, mayor_terms, faction_terms, ...}`. The audience
flow and `ResponseParser` are unchanged. Spec: `override-llm_spec.md` (slice 1). 634 tests (+7).

## Why these choices

- **Synthesise the model's output, don't special-case the flow.** The override emits the exact
  string shape a real model would, so `audiences.py` and the parser need zero changes — the override
  is just another provider. Maximum reuse, minimum surface.
- **Outcome on the config, not a new flow param.** `LLMConfig.override` carries the outcome
  programmatically (tests + agent). It's transient (omitted from `to_json`/`from_env`) — an outcome
  is per-audience, not a persisted profile field.
- **Both-sides rule is inherited, not re-implemented.** An accepted override must supply both
  `mayor_terms` and `faction_terms`; the parser's existing fair-exchange validation rejects a
  one-sided deal — the override goes through the same gate as a real model (discovered in test, kept
  as correct behavior and documented).

## Consequences

- Any audience outcome (accept/reject, Rally, Agitate-abstain, …) can now be driven deterministically
  in tests and by the agent — no model, no flakiness — and the chosen deal's effects apply through
  the normal path (verified: a Rally outcome sets `faction.committed_action == "Rally"`).
- Slice 2 remains: wire the override outcome through the live audience API + the active-AI gate
  (`_get_llm_config`) and add the dev-mode audience-modal outcome chooser, so a human can hold an
  override audience in the running game.
