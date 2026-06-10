# Proposal: Resource Chains & Population

**Date:** 2026-06-10
**Status:** PROPOSAL — not built, not scheduled. Captured from a roadmap discussion before a
development pause. Promote via a Spec Impact section when scheduled (see `proposals/README.md`).

## Problem

Faction health and rank currently matter only *politically* — a weakened faction is a weaker
player in the contest math, and nothing else. The city has no body to wound. There is no reason
(beyond reputation bookkeeping) for the Mayor to care whether the Fishermen specifically are
starving, because the Fishermen don't feed anyone.

This proposal gives faction strength **material consequences**: factions produce what the city
consumes, so a faction's decline propagates into shortage, and shortage propagates into pressure.

## Core idea

Each domain (or key factions within it) produces a **resource output** scaled by the strength of
its factions. The city consumes those outputs. Shortfall creates pressure.

The canonical example from the discussion: weak Fishermen → less food landed → the Bakers have
less to bake (Guilds output also dips) → the city's food supply falls → The Public suffers.

One faction's collapse is no longer just a power vacuum; it's a supply failure other factions
and the Mayor feel.

**This is not a goods simulation.** Same philosophy as events_spec ("they are not resource
management"): a small number of city-level supply gauges, each fed by domain/faction strength,
each with defined pressure effects when low. No trading, no stockpile micromanagement, no
per-good markets.

## Rough shape

- **Supply gauges** (small set, ~3–5): e.g. Food (Harbor + Guilds), Trade goods/income
  (Trade — already partly exists as treasury tax income), Piety (Temples), Security (Military),
  Knowledge/health (Academy / Professions). Exact set is an open question; Food is the anchor.
- **Production:** each gauge = Σ contribution from its source domains, scaled by faction
  levels/health there (likely reusing the weight table — `reference/formulas.md`).
- **Consumption:** scales with **population**. Population is a city-level number that grows
  slowly when supply is met and shrinks under sustained shortage.
- **Shortage pressure** (reuse existing channels, add no new resolution machinery):
  - The Public: support and health drains while a gauge is low (The Public already has a
    `health` field as a "general city wellbeing proxy" — this finally gives it a driver).
  - Events: low gauges raise event probability / unlock deck entries (famine, bread riots) —
    the event system already scales random-event chance with chaos; gauges become a second input.
  - Factions: hungry domains get action-weight modifiers (more Steal, less Grow) via the same
    `EventEffect`-style field deltas that events already apply.

## Why population

Population is the consumer side that makes production *matter*, and it doubles as the city-growth
metric the **Mayor title ladder** can be measured against (see `elections-and-titles.md`). The
README's "Mayor advancement: dynamic respect scaling based on city growth" needs a growth number;
population is that number.

## Dependency spine (why this proposal is one doc, not four)

resources → population → disasters → titles:
- Resource gauges give **disasters** something material to break (see `crisis-and-stance.md` —
  a harbor disaster that cuts Food is legible in a way "−3 health/cycle" is not).
- Population gives the **title ladder** a score to climb.
- Both run entirely on existing pressure channels (Public support, events, action weights), so
  the engine's pure-rules core and the cycle order survive intact.

## Cycle touchpoints (rough)

- New step (or fold into Step 8 world-pressure processing): derive gauge values from current
  faction state → apply consumption vs population → apply shortage effects.
- Derived-not-stored where possible, per the no-persistent-derived-fields decision
  (`decisions/2026-03-29-no-persistent-derived-fields.md`): gauges recompute from faction state;
  population is real state (it has memory).

## Open questions

- Per-domain or per-faction production? (Per-domain is simpler and probably enough; per-faction
  makes named factions like the Fishermen individually load-bearing, which is the flavor win.)
- Exact gauge set — Food only for v1? Anchor on Food, prove the loop, then add gauges?
- Does population interact with domain caps (more people → higher caps), or stay
  presentation/score-only at first? (Caps are now project-driven per projects v5 — beware
  giving cap two masters.)
- Can audience deals touch supply? (e.g. a deal term committing Fishermen to a Food push —
  would need a new committed-action type; defer until base loop works.)
- Mayor relief levers: does the treasury get a "buy grain" emergency action, or is relief
  entirely deal/project-driven?
