# Decisions: Audience Build-Target Info
Spec: Planning/specs/audience-build-target-info_spec.md
Date: 2026-06-08

- Informational/coherence fix, not an engine change. `_committed_plan` already builds the
  faction's own domain, so the build always *happens* — the bug is that the LLM, told nothing,
  agrees to build the wrong thing, so the deal terms (card/confirm/log) mismatch the outcome.
  Fix: make the LLM name the one project it can actually build.
- Prompt shows only the faction's OWN buildable (one line), never the full catalog. A faction
  can only build its own domain, so this is both correct and the bound on prompt creep — the
  global project count never reaches the prompt; only per-faction buildables do (today: one).
- Effect text lives in a single per-project `description` (BASE_PROJECT_DESCRIPTIONS +
  base_project_description), defaulting to the generic cap sentence (all v6 base projects do the
  same thing). Single source → prompt/UI/docs can't drift; ready for distinct effects later
  without touching the prompt code. Chosen over generating the sentence inline.
- Keep an explicit `target_id` = the domain id (vs dropping the target field). Today the only
  valid value is the faction's own domain id; keeping it explicit future-proofs for domains that
  later gain multiple distinct buildables, and keeps the deal card/log coherent.
- Engine targeting left as-is (own-domain enforced); no parser validation added — unnecessary
  since the engine already ignores a bad target and builds own-domain.
