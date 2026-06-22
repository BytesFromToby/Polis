# OverrideLLM slice 2 — dev-mode override audience (live API + UI)

**Date:** 2026-06-22

## What

Wired the override provider through the live audience and added the dev-mode UI chooser. Gated by
the `POLIS_DEV_MODE` env var (surfaced as `SimStatusResponse.dev_mode`, helper `api.sessions.dev_mode`).
`/audience/begin` gains `override: bool` (dev-only: holds the audience with an override `LLMConfig`,
bypassing the profile active-AI gate); `/audience/conclude` gains `override_outcome: dict` (injected
into the override config so the conclusion synthesises that `<deal>`). `AudienceModal` shows an
"Override outcome (dev)" toggle + an accept/reject + term/duration/endorsement chooser; GameView
allows opening an audience in dev mode even on a stub run. Spec: `override-llm_spec.md` (slice 2).
638 backend tests (+4); verified end-to-end in the browser.

## Why these choices

- **Env-var dev gate, not a player setting.** `POLIS_DEV_MODE` keeps the override surface off for
  normal players entirely (UI control hidden + backend refuses override) while making it one toggle
  to enable for testing/GM. Surfaced to the frontend via the status payload so the UI knows.
- **Per-audience opt-in, not a run/profile mode.** Override is chosen at `begin` (a request flag),
  not baked into the run's profile — so a dev can hold an override audience on any run (even a stub
  one) without disturbing run setup or the profile machinery.
- **Inject the outcome at conclude, reuse the captured config.** The audience captures its
  `llm_config` at begin; conclude sets `cfg.override` on that same config before running, so the
  existing flow/parser produce the chosen deal with no special-casing.
- **Open the audience in dev mode on a stub run.** GameView's audience entry was `aiSet`-gated;
  relaxed to `aiSet || devMode` so the override audience is reachable without a configured model.

## Consequences

- A human (GM) or the agent can now drive any audience outcome deterministically in the running
  game — verified live: a chosen Rally↔endorsement deal sealed in the browser with no LLM.
- OverrideLLM is complete (slices 1+2). Useful next: deterministic end-to-end audience tests that
  force a deal and assert downstream effects (faction rallies, support moves) without a model.
