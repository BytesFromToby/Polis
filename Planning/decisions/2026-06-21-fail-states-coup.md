# Fail states slice 4 — assassination / coup

**Date:** 2026-06-21

## What

Added the third removal road. `engine/special/removal.py::process_coup` (called in `run_cycle` after
the removal check) forms a plot when Σ per-faction Mayor reputation falls below `coup_rep_threshold`
and rolls each cycle for an assassination (`end_cause="assassinated"`). The City Guard defends — each
guard level cuts the chance by `coup_guard_protection`. Off on easy; sooner and harder on hard.
Spec: `specs/fail-states_spec.md` (slice 4).

## Why these choices

- **A risk roll, not a countdown.** The proposal frames the coup as a fightable risk: the player can
  recover faction standing to dissolve the plot, or rely on a strong City Guard. A per-cycle roll
  (rather than a fixed countdown) gives that agency — non-deterministic but not arbitrary, and
  distinct in feel from the removal spiral (the people/creditors) vs the great houses (the elite).
- **Folded into the removal family, not a parallel system.** It lives in `removal.py` beside the
  other terminal resolutions and reuses the same `game_over`/`end_cause` machinery.
- **The City Guard defends.** Reuses the existing guard (which suppresses unrest) as the lever
  against the elite — one unit, two jobs, no new entity.
- **Stateless.** The plot reforms each cycle from current standing, so there's no persisted plot
  state to serialize — recovering reputation simply ends the threat next cycle.
- **`rng` injectable.** `process_coup(..., rng=...)` mirrors the treasury insolvency helper so the
  roll is deterministically testable.
- **Difficulty gates it.** Easy turns the conspiracy off (matches the endgame difficulty table);
  hard lowers the threshold and raises the chance.

## Consequences

- The endgame's three fail roads are complete: removal spiral (people/debt), population collapse,
  and the coup (the great houses) — plus the election's win/lose pole.
- `coup_rep_threshold` is a raw sum, so its feel depends on faction count; flagged as a tuning dial
  (a per-faction-average form is the obvious refinement if rosters vary widely).
- Remaining endgame follow-ups: titles in the audience prompt, "support me in the election" deal
  term, forecast panel, per-difficulty election tuning.
