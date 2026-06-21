# Difficulty threading — making balance profiles bite (Slice 2)

**Date:** 2026-06-21

## What

`run_cycle` gained a `balance` argument (default `NORMAL`) threaded into the per-cycle dial
consumers — `process_treasury_step0`/`_calc_income`, `apply_needs` and the `scales` helpers it
calls (`piety_supply`/`piety_target`/`blame_factor`/`unrest_target`/`consumption_target`/
`production_efficiency`), and `process_moneylender`. The API resolves
`get_profile(session.difficulty)` and passes it at `/sim/step` and `/sim/run/{n}`. A difficulty
selector was added to the new-game builder modal. Spec: `specs/balance_spec.md` (Slice 2).

## Why these choices

- **Optional `balance` param defaulting to `NORMAL`, not a global.** Each consumer takes
  `balance=NORMAL` and reads `balance.<field>`. Existing callers and all tests omit it → get
  `NORMAL` → behavior is byte-identical (571 tests, 567 unchanged). A module-level "active
  profile" global was rejected: FastAPI runs sync endpoints in a threadpool, so two concurrent
  runs at different difficulties would race on a global. Explicit threading also matches house
  style (mayor, public, llm_config are all threaded).
- **Thread the per-cycle path only; defer the mayor-action dials.** `meet_cooldown` and
  `sabotage_gold` are consumed through a fixed-signature action-dispatch map *and* the separate
  audience route — threading them means touching both paths. They are low-frequency
  (player-triggered) and not central to per-cycle difficulty feel, so they stay on `NORMAL` for
  now and were removed from the `EASY`/`HARD` overrides to avoid advertising an inert lever.
- **Values left provisional.** `EASY`/`HARD` overrides are untuned starting points; tuning is
  deliberately separate from wiring.

## Consequences

- Difficulty now changes the core loop: gold income, unrest persistence, population growth, and
  how quickly debt triggers the removal coalition.
- The endgame thresholds (population floor-vs-death, election cadence) can now be added as
  difficulty-varying dials on this same threaded path.
- Remaining follow-ups: thread the mayor-action/audience dials; tune `EASY`/`HARD`; add a stored
  default-difficulty preference + wire the TitleView quick-start to it.
