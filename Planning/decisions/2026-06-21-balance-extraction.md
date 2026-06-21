# Balance extraction — single source of truth for tunable dials

**Date:** 2026-06-21

## What

Created `engine/balance.py` as the one home for difficulty/feel/stakes dials, as a
`BalanceProfile` dataclass with `NORMAL` (base) plus `EASY`/`HARD` overrides and a `get_profile`
resolver. Engine modules (`formulas`, `needs/drift`, `needs/scales`, `mayor/actions`,
`special/moneylender`) now re-export their historical constant names *from* `NORMAL`
(e.g. `DRIFT_STEP = NORMAL.drift_step`). Added `SimRun.difficulty` (default `"normal"`),
persisted at `/sim/start` and restored on `/sim/switch`. Spec: `specs/balance_spec.md`.

## Why these choices

- **Source of truth is code, not a doc.** A markdown "constants spec" would duplicate numbers and
  drift from the code within weeks. `balance.py` is authoritative; the spec describes it.
- **Re-export from NORMAL instead of replacing usages.** Tests import the module constants by name
  (`from engine.needs.drift import DRIFT_STEP`). Keeping the names and only changing their RHS to
  `NORMAL.<field>` makes the refactor behavior-preserving and minimal-diff — all 567 tests pass,
  566 unchanged.
- **Behavior-preserving first; difficulty inert.** Per `proposals/roadmap.md` item 0:
  "pure refactor first, then add easy/hard and tune." `NORMAL` is the only profile the engine
  consumes this slice; `EASY`/`HARD` and `SimRun.difficulty` exist and persist but do not yet
  change gameplay. Threading the active profile through the cycle is Slice 2.
- **Selective extraction, not a god-module.** Only difficulty/feel/stakes dials moved; structural
  invariants (`RATING_MAX`, the d20, term-type maps, action-point costs) stayed put. Discriminator
  recorded in the spec.

## Consequences

- All tuning of the extracted dials now happens in one file.
- `EASY`/`HARD` override values are provisional and untuned — do not treat them as balanced.
- Difficulty selection has no gameplay effect until Slice 2 wires the active profile through the
  engine and adds the new-game selector. This unblocks the `endgame` proposal, whose thresholds
  (population floor, election cadence, removal triggers) are balance dials.
