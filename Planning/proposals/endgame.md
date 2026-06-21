# Proposal: Endgame & Fail States

**Date:** 2026-06-21
**Status:** PROPOSAL — not built. The fail-state framework that turns Polis from a sandbox into a
game. Sits above [elections-and-titles.md](elections-and-titles.md), which details the single
biggest trigger (the election). Promote via a Spec Impact section when scheduled.

## Problem

A run cannot end — there is no win, no loss, no "the reign is over." Worse, the pieces of a
failure spiral *already exist but fizzle*:

- [`engine/special/public.py`](../../backend/engine/special/public.py) — low Public support fires
  a `RemovalRisk` "removal countdown active" narrative.
- [`engine/special/moneylender.py`](../../backend/engine/special/moneylender.py) — debt >
  `REMOVAL_THRESHOLD` (800) → `REMOVAL_GRACE_CYCLES` (5) grace → `MayorRemovalAttempt`,
  "removal coalition."
- A `removal_coalition` event in [`data/events.json`](../../backend/data/events.json).

But the engine has **no `game_over` / terminal state** — these triggers emit dramatic narrative
and then the game simply continues. The gap isn't "no fail states"; it's "the fail states have no
teeth." Until a run can end, difficulty, achievements, and Mayor progression are all hollow.

## Core architecture: one end-state, many triggers

Do **not** scatter independent game-over checks. Build a single terminal resolution —
**"the Mayor loses office, the run ends"** — and feed it from multiple triggers. Two triggers
already exist (Public support, debt) and currently dead-end; this work gives them teeth and adds
three more roads to the same end.

```
TRIGGERS                          →   RESOLUTION                →   OUTCOME
- Public support ≤ threshold          run_ended = True              difficulty decides:
- Debt > REMOVAL_THRESHOLD            (record cause + cycle)        - easy: forgiving
- Population ≤ floor          ──────► "Mayor loses office"  ──────► - normal: demotion w/ floor
- Election verdict: lost                                            - hard: game over
- Σ faction reputation < X (coup)
```

Every trigger writes a **cause** and **cycle** so the end screen / chronicle can say *why* the
reign ended. The existing removal triggers route into this same resolution instead of fizzling.

---

## Trigger 1 — Population collapse

- **Death:** population ≤ `POP_FLOOR` (today `POP_MIN = 1000`, currently an unbreakable floor in
  [`engine/needs/drift.py`](../../backend/engine/needs/drift.py)) → terminal in normal/hard;
  stays a floor (can't die) in easy mode.
- **Warning (latched, with hysteresis):** a sustained warning event turns **on at ≤ 1500** and
  stays active **until population recovers > 1750**. While active it slowly drains Public support
  (which feeds elections). The 1500/1750 gap is deliberate — single-threshold warnings flap
  on/off; hysteresis makes the warning stable.
- **New infra required** (see below): a *latched event subtype* and *population trigger gates* —
  the current event system only does fixed-duration events and has no population condition.

## Trigger 2 — Election verdict

The scheduled judgment. Full design in [elections-and-titles.md](elections-and-titles.md);
the points that matter for the fail-state framework:

- **It is a verdict, not a coin-flip event.** Compute the result from currencies that already
  exist — Public `support` + per-faction Mayor reputation weighted by faction rank. Keep the math
  **legible** (a forecast UI needs determinism-ish math). Reducing the election to "an event you
  must pass" throws away the campaign and the deal-as-vote hook.
- **Cadence = a balance dial, default ~12–16 cycles, not hardcoded.** Long enough to govern,
  short enough that a typical session reaches at least one verdict. (24 was floated but risks
  sessions never seeing the endgame — tune against real session length.)
- **Campaign window:** a warning event ~4 cycles before the vote — the visible run-up that turns
  preceding cycles into a campaign.
- **"Support me in the election" as a deal term** — the headline LLM-negotiation mechanic becomes
  load-bearing for the endgame with near-zero new machinery; the existing deal-fidelity/memory
  system tracks who delivered.
- **Losing = difficulty-gated:** demotion on the title ladder (forgiving; ladder is
  two-directional) vs game over (roguelike). Demotion-with-floor is the likely normal default;
  game over for hard.

## Trigger 3 — Assassination / coup *(maybe / later)*

The mid-term coup to the election's scheduled judgment.

- **Fold into the existing removal coalition — do not build a parallel system.** Add a third
  trigger key alongside support and debt: **summed faction reputation < X**.
- **It is a *risk*, not instant death.** When Σ faction rep falls below X, fire a recurring "plot
  against the Mayor" risk that rolls each cycle. The player has agency to fight it: raise faction
  reputation, or lean on the **City Guard** (which already suppresses unrest in
  [`drift.py`](../../backend/engine/needs/drift.py) — let it also defend the Mayor). Non-deterministic
  but not arbitrary.
- Lowest priority of the three — it mostly *extends* code that exists.

---

## New infrastructure these need

1. **Terminal run state.** A `run_ended` flag + `end_cause` + `end_cycle` on the run, checked by
   the cycle runner; the existing removal triggers route here. The "loses office" resolution and
   an end screen / chronicle summary read from it.
2. **Latched event subtype (with hysteresis).** Events today fire for a fixed `duration` then
   auto-resolve. Add a sustained event that stays active while a condition holds and clears on a
   *different* condition (e.g. on ≤1500, off >1750). **Reusable** — Weather and crisis warnings
   want the same pattern; build it once, well, here.
3. **Population trigger gates.** Add `min_population` / `max_population` to the event
   trigger-condition vocabulary (currently chaos / cycle / need-bands only).

## Difficulty integration

Every threshold here is a **balance dial** and several differ by difficulty — so this work
**depends on the balance extraction** (`balance_spec.md`) landing first:

| Dial | easy | normal | hard |
|------|------|--------|------|
| Population floor | floor (can't die) | terminal at 1000 | terminal, maybe higher |
| Election loss | n/a / demotion | demotion w/ floor | game over |
| Assassination | off | on, lenient X | on, harsher X + odds |

## Prerequisites

- **Balance extraction** — so thresholds live in one place, not hardcoded across modules.
- **Visible approval / forecast readout** — a prerequisite for elections feeling fair, not
  polish. Without the needle, a lost vote reads as random.

## Open questions

- **What does losing the election mean** — game over vs demotion-with-floor? (Lean demotion for
  normal, game over for hard.)
- **Vote math** — simple weighted sum vs per-faction d20 roll against reputation (legibility vs
  texture). Lean legible; the forecast UI wants it.
- **Do election (scheduled) and coup (snap) coexist**, or does the coup fold into a
  crisis-triggered snap election? Both existing removal triggers map cleanly onto a snap-election.
- **Can the Mayor campaign?** Endorse / Condemn / Meet already move reputation — likely the
  campaign kit, no new actions needed.
- **Population floor as death vs the City-Guard / unrest interactions** — does a city dwindle to
  death, or get deposed first? Order of trigger checks matters for which cause is recorded.

## Build sequence (within this proposal)

> **Status:** Slices 1–3 **shipped 2026-06-21**. Slices 1–2 → [fail-states_spec](../specs/fail-states_spec.md)
> (terminal `game_over`; removal spiral via Public reputation / debt; population collapse + latched
> warning). Slice 3 → [elections_spec](../specs/elections_spec.md) (the recurring verdict + the
> title ladder: win climbs, top rung = victory, lose demotes-with-floor or is terminal on hard).
> Slice 4 (assassination/coup) remains, plus deferred election follow-ups (titles in the audience
> prompt, deal-as-vote, forecast panel).

1. Terminal end-state + route existing removal triggers into it (the spine).
2. Population fail + latched warning event + population gates (smallest slice; builds reusable infra).
3. Elections (the big trigger) — see elections-and-titles.md; needs the approval readout.
4. Assassination/coup as an extension of the removal coalition (last / maybe).

## Spec Impact *(rough — finalize when scheduled)*

- **New:** `fail-states_spec.md` — the terminal resolution + triggers 1 & 3 + latched-event subtype.
- **New:** `elections_spec.md` (from elections-and-titles.md) — trigger 2 + title ladder.
- **Changed:** `events_spec.md` (latched subtype, population gates), `special-factions_spec.md`
  (removal coalition gains the faction-rep trigger + terminal teeth), `mayor_spec.md` (title field
  becomes dynamic; campaign actions), `public-needs_spec.md` (population floor as death vs easy
  floor), and `balance_spec.md` (all the dials above).
- **Depends on:** `balance_spec.md` shipping first.
