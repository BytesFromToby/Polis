# Factions sway public opinion — Rally / Agitate (build)

**Date:** 2026-06-21

## What

Implemented the proposal `proposals/faction-influence.md`. Two new faction actions:
- **Rally** (`resolve_rally`) — moves `mayor.reputation["the_public"]` up by
  `max(1, round(influence_per_level × faction.level))`.
- **Agitate** (`resolve_agitate`) — the same, down.

Both base-weight 0 in `BASE_WEIGHTS`; Step 3 of the behavior engine lifts Rally when the Mayor's
standing with the faction is high (≥ `RALLY_THRESHOLD`) and Agitate when low (≤ `AGITATE_THRESHOLD`),
scaling per 10 points beyond the threshold — mirroring the Withhold anger gate. The indifferent
middle reaches for neither; no Mayor → neither. `balance.influence_per_level` is the difficulty
dial. Resolution threads `mayor`/`balance` through `run_sequential_actions` → `_execute`. Specs:
`actions_spec.md` (resolution) + `faction-behavior_spec.md` (weighting).

## Why these choices

- **Modelled on Withhold.** Same "base 0, lifts only from the Mayor relationship" shape, same
  constant-placement (weights/thresholds in `behavior.py`, the support magnitude as a balance dial).
  Consistency with the existing precedent over inventing a new pattern.
- **No new persisted state.** It rides `mayor.reputation["the_public"]` (already the support source
  of truth, already serialized), so it feeds elections and the removal spiral with zero new
  machinery — and the build is low-risk (621 tests, 611 unchanged).
- **Direction from `mayor.get_reputation(faction.id)`.** Reuses existing state and creates the
  intended loop: court a faction → it rallies the people for you; antagonise one → it agitates.

## Playtest finding (a tuning lever, recorded)

An engaged-Mayor playtest (two factions courted, two antagonised) confirmed the mechanic fires and
moves public support — but support **flatlined at +10**. The governor is `apply_reputation_decay`,
which pulls any reputation past ±10 back toward ±10 each cycle. So Rally/Agitate move support
*within* the ±10 band quickly but can't easily push beyond it, which keeps approval (≈ half of
support) in a ±5 knife-edge around the election pass score of 0.

**Implication:** the lever for wider, more decisive election mandates is the **±10 reputation-decay
band**, not the influence magnitudes. That's a separate balance decision (it governs the whole
support/approval system, as the earlier endgame playtest also showed) — flagged for a future tuning
pass, deliberately not changed here.

## Consequences

- Faction relationships are now load-bearing every cycle (they move the number elections and removal
  read), not just at audience time.
- Remaining follow-up: the deal-term hook (Rally/Agitate as `committed_action`/`committed_abstain`),
  and a balance pass on the reputation-decay band if wider swings are wanted.
