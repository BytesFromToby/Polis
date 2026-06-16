# Piety + Unrest — two new Public scales

**Date:** 2026-06-16
**Spec:** `public-needs_spec.md` (Features: Piety, Unrest), `events_spec.md` (gates + 2 flagships),
`faction-behavior_spec.md` (unrest→Steal), `special-factions_spec.md` (fields + support catalog).
**Proposal:** `../proposals/public-model.md` (the approved 7-scale model + band matrix).
**Scope call (user):** "Standard — both scales fully wired + the City Guard lever + flagship events."

## Concrete mechanical choices (the proposal left these open)

**Piety driver = a temple supply mirroring the food chain.** Temple-domain factions produce
`PIETY_PER_LEVEL × level`; `piety` drifts toward `100 × supply/(demand × PIETY_PARITY)`. Chosen
over a flat per-temple piety tick because it reuses the existing supply→target→drift machinery,
makes temple *strength* matter (a decimated temple roster lets piety slide), and lets Toil/Withhold
act on temples (a priestly strike). Constants provisional.

**Both ends of piety bite.** Godless → crises blamed on the Mayor (amplified support penalties);
Zealous → temples defy the Mayor (`support` −1/cycle). Keeps the proposal's "neither extreme purely
good" filter true.

**Crisis-blame scales the needs step's OWN support penalties, not arbitrary events.** Events don't
currently apply support penalties to the Public, so there was nothing for a generic "event blame"
modifier to scale. Instead piety scales the negative shortage/health support deltas the needs step
already applies (Starving −5, etc.). Self-contained, testable, and needs no new event-support
machinery. Flagship events lean on band *gating*, not support effects.

**Unrest = pressure aggregate with asymmetric memory.** `unrest_target` = Σ band-keyed pressure
(hunger + impiety + low confidence + drunkenness). Unrest rises toward a higher target at
`DRIFT_STEP` but eases toward a lower one at only `UNREST_EASE` (4) — the cause clears faster than
the mood. This is the "memory" the proposal wanted, with no extra state: the asymmetry *is* the
memory.

**City Guard = costed symptom suppression.** With `city-guard` present and payroll met, unrest is
pressed down `GUARD_SUPPRESS × level` *after* drift — it does not touch `unrest_target` (the cause
festers). Heavy suppression (≥ `GUARD_HEAVY_THRESHOLD` removed) costs `support` (−2). So a strong
Guard buys calm at the price of resentment — the proposal's "buy time vs. fix the cause" spine, in
one mechanic. Ordering: `piety` settles before `unrest` reads its band (impiety is an unrest term).

**Confidence is the existing `support`, not a new field.** Band-modeling its consequences is
deferred with consumption to a later slice; this slice only *reads* `support` as an unrest term.

## Deferred (out of this slice)
Consumption (the alcohol balance-axis); the two Public→production wires (health-output,
consumption-output); the richer extreme-event deck (Witch-Hunt, Oracle's Demand, Insurrection,
Acclamation, the Exodus) — only The Mob Marches (unrest) + The Ignored Omen (piety) ship now.
