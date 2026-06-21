# Fail states slice 1 — terminal Mayor removal

**Date:** 2026-06-21

## What

Added a real end state. `engine/special/removal.py::process_mayor_removal` is a single resolution,
called late in `run_cycle`, that runs the removal spiral: a countdown on the Mayor
(`Mayor.removal_countdown`) starts when a trigger holds (Public reputation ≤ `removal_rep_threshold`
or debt > `removal_threshold`), decrements while it persists, clears if it lifts, and on elapse
latches `WorldState.game_over` with an `end_cause`. The API marks the `SimRun` `complete` +
`end_cause`; the frontend shows a reign-ended banner. Spec: `specs/fail-states_spec.md`.

## Why these choices

- **One resolution, many triggers — not scattered checks.** mayor_spec described removal but the
  code only emitted narrative, and the moneylender's `removal_countdown` was never even passed in
  `run_cycle` (dead). Unifying into one countdown + one terminal flag is the spine every later
  trigger (population, election, coup) plugs into.
- **Removal = game over, here.** The proposal's open "game over vs demotion" question is about the
  *election* trigger; the pre-elections removal spiral is unambiguously a defeat, so slice 1 makes
  it terminal with no demotion branch.
- **State on WorldState + Mayor, serialized.** `game_over`/`end_cause` are run-level (WorldState);
  the countdown is the Mayor's tenure (Mayor). Both serialize so a resumed run remembers.
- **`status="complete"` is the terminal marker.** It already existed and already excludes a run
  from "active", so a finished game naturally can't be stepped further — no new status value.
- **Left the moneylender countdown in place.** It's unwired/legacy but removing it would break an
  existing test; the new resolution supersedes it in the live cycle. Noted in the spec.

## Consequences

- A run can now end (and difficulty scales the grace window via the balance profiles).
- Deferred and noted: faction-coalition pressure + bankruptcy's distinct grace; population collapse
  + the latched warning event (slice 2); elections (slice 3); assassination (slice 4).
- The end screen is a one-line banner for now; a richer end-of-reign chronicle is future work.
