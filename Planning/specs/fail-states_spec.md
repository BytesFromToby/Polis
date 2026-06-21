# Fail-States Specification

**Version:** v2 (slices 1–2)
**Date:** 2026-06-21

The terminal "the Mayor loses office, the run ends" resolution and the triggers that feed it.
Turns Polis from a sandbox into a game. Designed in [endgame.md](../proposals/endgame.md); implements
the removal spiral that [mayor_spec](mayor_spec.md) ("Mayor Removal") described but never enforced.

---

## Architecture: one end-state, many triggers

A single resolution decides removal; multiple triggers feed one countdown on the Mayor. When the
countdown elapses the run ends — `WorldState.game_over` latches with a recorded `end_cause`.

```
TRIGGERS                                    COUNTDOWN (Mayor)          TERMINAL (WorldState)
- Public reputation ≤ removal_rep_threshold ─┐
- Treasury debt > removal_threshold ─────────┴─► removal_countdown ──► game_over = True
                                                 (grace → 0)            end_cause = "<reason>"
- Population ≤ pop_collapse (if lethal) ────────────────────────────► game_over = True (immediate)
                                                                       end_cause="population_collapse"
```

- Triggers evaluated each cycle by `engine/special/removal.py::process_mayor_removal`, called late
  in `run_cycle` (after the Public is processed, so reputation has settled).
- Countdown starts at `balance.removal_grace_cycles` when a trigger first holds, decrements each
  cycle it persists, and **clears the moment all triggers lift** (the player stabilised in time).
- On elapse: `game_over = True`, `end_cause` ∈ `{"public_revolt", "removal_coalition"}`.
- `game_over` latches — once set, the resolution is a no-op.

### Slice boundary

- **Slice 1 (shipped 2026-06-21):** the terminal state + the two removal triggers (Public
  reputation, debt coalition), wired into the live cycle and surfaced through the API and a frontend
  banner. Removal = **game over** (the pre-elections spiral is a defeat; the forgiving "demotion"
  path belongs to the election trigger, a later slice).
- **Slice 2 (shipped 2026-06-21):** **population collapse** — an immediate terminal when population
  ≤ `pop_collapse` on profiles where `pop_floor_is_death` (normal/hard; easy keeps it a floor and
  never dies). Plus a **latched low-population warning** with hysteresis (on ≤ `pop_warn_on` 1500,
  off only once population recovers above `pop_warn_off` 1750) that drains support each active
  cycle — which feeds the removal spiral, so a hollowing city compounds toward removal.
- **Deferred:** the 3+-hostile-factions coalition pressure (−2/cycle accelerant) and bankruptcy's
  distinct 3-cycle grace from mayor_spec; a **data-driven latched-event subtype in the event deck**
  (the hysteresis *pattern* is built in `process_population`; generalising it into `event_system`
  for the Active-Events UI band waits for a second consumer — Weather/crises); the **election
  verdict** (slice 3); **assassination/coup** (slice 4).
- **Superseded:** the unwired `removal_countdown` inside `special/moneylender.py` (never passed in
  `run_cycle`) — the new resolution is the live mechanism. The moneylender's "coalition possible"
  narrative remains as a warning.

---

## Data Model

- `WorldState.game_over: bool = False`, `WorldState.end_cause: str = ""` — serialized, so a resumed
  run remembers it ended.
- `Mayor.removal_countdown: Optional[int] = None` — cycles left before removal while a trigger
  holds; `None` = not in jeopardy. Serialized.
- `ThePublic.pop_warning: bool = False` — latched low-population warning state. Serialized.
- `SimRun.end_cause: str = ""` — DB record of why a finished run ended (forward-migrated). The run's
  `status` becomes `"complete"` on game over.

## Balance dials (engine/balance.py)

- `removal_rep_threshold: int = -30` — Public reputation at/below this is a removal trigger.
- `removal_grace_cycles: int = 5` — the countdown length (already existed; now drives the spiral).
- `pop_collapse: int = 1000` — population at/below this ends the run (when lethal).
- `pop_floor_is_death: bool = True` — normal/hard: hitting the floor is terminal; **easy: False**
  (the floor protects, the city can't die).
- `pop_warn_on: int = 1500` / `pop_warn_off: int = 1750` — hysteresis bounds for the warning latch.
- `pop_warn_support_drain: int = -1` — support lost per cycle while the warning is active.
  Dials vary by difficulty via the profiles (e.g. easy gives a longer grace and a non-lethal floor).

## API

- `/sim/step` and `/sim/run/{n}` mark `run.status="complete"` + `run.end_cause` when
  `world.game_over` is set this step; `run_n` stops with `stop_reason="game_over"`. A completed run
  is no longer "active", so further `/sim/step` returns 404 (cannot play past the end).
- `SimStepResponse` gains `game_over: bool` and `end_cause: str`.
- `SimStatusResponse` gains `end_cause: str`.

## Frontend

- `GameView.vue` shows a banner when the run has ended (from the step response or a `complete`
  status) and disables the "Run Cycle" button. Cause is rendered in plain language.

---

## Done when

- `process_mayor_removal` starts a countdown when Public reputation ≤ `removal_rep_threshold`,
  decrements it while the trigger holds, and sets `world.game_over` + `end_cause="public_revolt"`
  when it elapses — `tests/test_removal.py`  `[automated]`
- Debt > `removal_threshold` drives the same countdown to `end_cause="removal_coalition"` —
  `tests/test_removal.py`  `[automated]`
- A countdown clears (no game over) if every trigger lifts before it elapses —
  `tests/test_removal.py`  `[automated]`
- The grace window scales with difficulty (easy outlasts hard) — `tests/test_removal.py`  `[automated]`
- `game_over` latches: once set, the resolution is a no-op even if the Mayor recovers —
  `tests/test_removal.py`  `[automated]`
- A full cycle (`run_cycle`) with sustained low reputation ends the run within grace+1 cycles —
  `tests/test_removal.py`  `[automated]`
- `game_over`/`end_cause` and `Mayor.removal_countdown` survive serialization round-trip —
  `tests/test_removal.py`  `[automated]`
- Population ≤ `pop_collapse` ends the run with `end_cause="population_collapse"` on normal/hard,
  but only floors (no death) on easy — `tests/test_population_fail.py`  `[automated]`
- The low-population warning latches on at ≤ `pop_warn_on`, persists through the hysteresis band,
  clears only above `pop_warn_off`, and drains support each active cycle —
  `tests/test_population_fail.py`  `[automated]`
- `ThePublic.pop_warning` survives serialization round-trip — `tests/test_population_fail.py`  `[automated]`
- In the UI, a run that ends shows the reign-ended banner (incl. population collapse) and the Run
  Cycle button is disabled — `[human-required]`

---

## File Structure

```
engine/
    special/removal.py     ← process_mayor_removal + process_population (the resolutions)
    cycle/runner.py        ← calls them late in the cycle (population first, then removal)
    models.py              ← WorldState.game_over/end_cause, Mayor.removal_countdown, ThePublic.pop_warning
    balance.py             ← removal + population dials
serializer.py              ← persists the new fields
db/models.py, db/session.py ← SimRun.end_cause + migration
api/schemas.py, api/routes/sim.py ← end_cause / game_over surfacing
frontend/src/views/GameView.vue   ← reign-ended banner + disabled control
```

## Tests

- `tests/test_removal.py` — countdown state machine, recovery, debt trigger, difficulty grace,
  latch, `run_cycle` integration, serialization round-trip.
- `tests/test_population_fail.py` — collapse (lethal vs easy floor), hysteresis warning latch,
  support drain, `run_cycle` integration, serialization round-trip.
