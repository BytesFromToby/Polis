# Fail states slice 2 — population collapse + latched warning

**Date:** 2026-06-21

## What

Added the second fail trigger. `engine/special/removal.py::process_population` (called in
`run_cycle` before the removal check) does two things: (1) **collapse** — population ≤
`pop_collapse` latches `world.game_over` with `end_cause="population_collapse"` on profiles where
`pop_floor_is_death` (normal/hard; easy keeps the floor non-lethal); (2) a **latched warning** with
hysteresis — on at ≤ `pop_warn_on` (1500), off only once population recovers above `pop_warn_off`
(1750) — that drains support each active cycle (`ThePublic.pop_warning` holds the latch). Spec:
`specs/fail-states_spec.md` (slice 2).

## Why these choices

- **Hysteresis, not a single threshold.** A 1500-on / 1750-off band stops the warning flapping when
  population hovers at the edge — a deliberate gap, per the proposal.
- **Difficulty gates death, not the warning.** `pop_floor_is_death` is the only behavioural fork:
  easy bottoms out at the floor and survives (the old self-balancing feel), normal/hard die. The
  warning fires on every profile so even an easy city feels the pressure.
- **The warning's support drain feeds the removal spiral.** Rather than the warning being inert
  flavour, draining support routes through the slice-1 machinery — a hollowing city compounds toward
  removal. One mechanic reinforcing another, no new terminal path.
- **Built the hysteresis *pattern*, not a generic event subtype.** The proposal floated a
  data-driven latched-event subtype in the event deck (so Weather/crises reuse it). That is
  speculative until a second consumer exists, so the latch lives in `process_population` as a clean,
  named pattern; generalising into `event_system` (and the Active-Events UI band) is deferred and
  noted. Avoids building a DSL for one user.

## Consequences

- A city can now die by emptying, with a visible, stable warning before it does.
- Population thresholds join the difficulty dials, so tuning the death/warning bands is one-file.
- Remaining: elections (slice 3, the demotion-vs-game-over branch + approval readout) and
  assassination/coup (slice 4); and — when Weather/crises arrive — generalising the latched warning
  into a reusable event-deck subtype surfaced in the Active Events band.
