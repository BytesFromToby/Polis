# Proposal: The Barley Run — Population, Public Needs, and the First Chain

**Date:** 2026-06-12
**Status:** PROPOSAL — scheduled for build. This is the v1 slice of `resource-chains.md`:
one production chain, a real population number, and Public needs in place of abstract supply
gauges. The **Spec Impact** section below is what `architect` works from.

## Problem

Faction strength has no material consequence — see `resource-chains.md`. This slice fixes that
with the smallest loop that can prove it: one chain, one consumer, one new action.

## Core idea

**The Public is the center of the city.** It eats, has opinions, gets scared and sick. Factions
struggle a layer up, but the Public is what makes the city. Factions earn mechanical meaning by
which Public need they service — and the first chain (the barley run) is the proof.

This replaces the "supply gauges" framing from `resource-chains.md`: the gauges *are* the
Public's needs. No new gauge entities.

## The Public gains state

- **`population`** — real city-level number, 10–50k scale. Grows slowly when fed and healthy;
  shrinks under sustained shortage. Stored state (it has memory).
- **`fed`, `happy`** — 0–100 traits on `ThePublic`. **`health`** (0–100) already exists as a
  "general city wellbeing proxy" — this finally gives it a driver.
- **Drift, not snap:** each cycle the chain produces a *target* value (`supply / demand`,
  capped); the stored trait drifts toward it. The drift *is* the granary — one bad cycle dents,
  only sustained shortage starves. This is why traits are legitimately stored, not derived.
- **Word bands, defined once** (in `reference/formulas.md`): e.g. fed → Starving / Hungry /
  Fed / Well fed. Everything keys off bands — audience prompt, UI, event gating — so design
  and code speak the same language. Precedent: `ThePublic.disposition` already derives word
  bands from `support`.
- **"Drunk" is not stored.** Track wine's share of this cycle's happiness gain; when it
  dominates, the descriptor reads "drunk" instead of "content." Flavor without a new axis.

## The chain (mapped to the real roster)

- **Producers:** the aristocracy estates — Eumelidai, Pyrrhidai, Skiadai. Raw **harvest**
  scales with their levels (the discussion's "estate that grows barley").
- **Processors** split the harvest in proportion to their strength:
  - **The Ovenmen** (guilds) → bread: high fed.
  - **The Winepressers** (guilds) → wine: low fed, +happy. *(Discussion said barley → beer;
    the roster already has Winepressers and wine is the right Greek flavor. Mechanics
    identical — one raw, two competing conversions with different need profiles.)*
  - **Unprocessed remainder** → porridge: low fed. The porridge floor — losing processors
    degrades the city, never cliffs it.
- **Conservation:** bread + wine + porridge inputs ≤ raw harvest. Nothing invented or lost.
- **Consumption:** 1 production point feeds 1,000 pop; demand = population / 1000. A level-2
  Ovenmen can feed 3,000 but not 30,000 — production is absolute, demand scales with pop.
- **The split is the gameplay:** strong Winepressers + weak Ovenmen = a drunk, hungry city.
  Faction *balance* matters, not just faction health, and the Mayor can want a faction weaker.
- **The treadmill:** pop growth is both the score and the difficulty curve — a growing city
  outgrows yesterday's faction lineup.

## The Public acts through events

Need bands gate event-deck entries (reusing the existing event system, no new machinery):
- Starving → bread riot unlocks; low health → plague outbreak chance; Well fed + happy →
  festival / boon (the Mayor-title hook — parked for the titles proposal).
- **Sentinel events for testing:** empty no-effect events, one per band, asserting the gate
  logic fires. They stay as permanent regression probes.

## Toil (new faction action)

- The faction works its trade instead of maneuvering: production contribution up for one
  cycle, in place of Grow/Attack. The opportunity cost is the balance — toiling factions
  stand still politically.
- NPC weighting: shortage in a faction's output raises Toil weight (the prosocial branch
  beside hungry → Steal; personality decides which).
- Audience-dealable via the existing `committed_action` machinery — this answers
  `resource-chains.md`'s open question about deals touching supply with "yes, it's just an
  action." A Mayor who demands Toil every audience grinds that faction into a serf class —
  intended, and it should cost relationship.

## Cycle touchpoints

New step (or fold into world-pressure processing): derive harvest and split from current
faction state → compute targets vs population → drift traits → apply band effects (support /
health drains, event weights). Chain output is derived each cycle (per the
no-persistent-derived-fields decision); population and traits are stored.

## Audience prompt

One line built from band words: *"The people are Hungry, drunk, and restless."*

## Testing (agreed approach)

1. **Pure math** — the chain as a pure function: producer scaling, proportional splits,
   degenerate cases (no processors, one processor, dead estates), conservation.
2. **Cycle wiring** — traits update at the right step; drains flow through existing channels;
   band gating shifts event weights; Toil bumps exactly one cycle then decays.
3. **Scenario fixtures** (the design, encoded): *Drunk city* (strong Winepressers + weak
   Ovenmen → happy up, fed down), *Porridge floor* (no processors → degrade, no cliff),
   *Dead estates* (no raw → processors irrelevant).
4. **Dynamics** (headless `--cycles` runs, tolerance bands): stability (a balanced city never
   starves on its own), legibility (halve the estates → visible hunger within ~5 cycles),
   recoverability (restore the estates → the city climbs back; spirals require sustained
   neglect), Toil matters (same shortage, with vs. without a Toil deal → shallower trough).

## Spec Impact

- **New:** `specs/public-needs_spec.md` — population, fed/happy/health traits, drift, band
  tables, the barley chain, consumption math. Owns the loop.
- `specs/actions_spec.md` — add Toil (resolution + opportunity cost).
- `specs/faction-behavior_spec.md` — Toil weighting under shortage.
- `specs/cycle-runner_spec.md` — the new/folded cycle step.
- `specs/events_spec.md` — band-gated deck entries + sentinel events.
- `specs/audience_spec.md` — the needs line in the prompt.
- `specs/special-factions_spec.md` — `ThePublic` gains `population`, `fed`, `happy`; `health`
  gets its driver.
- `reference/data-models.md`, `reference/formulas.md` — fields, band tables, chain constants.

## Deliberately out of v1

- Fish (the Netmenders) — the designated first extension: a second Food producer, zero new
  mechanics.
- All other chains (wool, iron, olives), warehouses, per-resource trade values — see
  `resource-chains.md`'s philosophy line; still binding.
- Pop-gated faction levels (workers per level) — a third master on caps; revisit post-v1.
- Mayor split levers ("mandate grain to bakeries") and title-driven influence — parked for
  later discussion.

## Open questions resolved by this slice

- Per-domain or per-faction production? → **Per-faction** (named factions are load-bearing;
  that's the flavor win).
- Food only for v1? → **Yes** — one chain proves producer, competing processors, two needs.
- Can deals touch supply? → **Yes, via Toil** as a normal committable action.
- Mayor relief levers? → **Through Toil deals** for now; direct levers deferred.
