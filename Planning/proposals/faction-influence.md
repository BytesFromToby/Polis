# Proposal: Factions Sway Public Opinion of the Mayor

**Date:** 2026-06-21
**Status:** PROPOSAL — not built. A new faction action that lets factions move the Public's opinion
of the Mayor, for good or ill. Captured from a design discussion; promote via the Spec Impact
section when scheduled (see `proposals/README.md`).

## Problem

Factions affect the Mayor's standing only *indirectly*: their per-faction Mayor reputation feeds
the election's "influential vote" ([elections_spec](../specs/elections_spec.md)). They cannot act
on **public opinion** — the `mayor.reputation["the_public"]` support score that both elections and
the removal spiral ([fail-states_spec](../specs/fail-states_spec.md)) read.

The 2026-06-21 endgame playtest exposed the cost of this: with no one moving public opinion, the
faction vote sat near 0, approval was just half of public support, and elections were a flat
knife-edge around 0. Faction relationships are mostly flavour between audiences — they aren't
load-bearing for survival cycle to cycle.

## Core idea

A new faction action — **Rally** (pro-Mayor) / **Agitate** (anti-Mayor) — by which a faction
spends its turn moving public support of the Mayor. Direction follows the faction's stance toward
the Mayor; magnitude scales with its rank. This makes the Mayor↔faction relationship matter every
cycle, opens up the approval dynamic range, and gives the audience/deal mechanic a sharp new
currency.

## Mechanics (rough)

- **A new action in the NPC system.** It joins `BASE_WEIGHTS` in `engine/npc/behavior.py` and is
  selected like any other action in the sequential-initiative loop — so it has a real opportunity
  cost against Grow/Protect/Toil/etc. (natural rate-limiting; a faction won't sway every cycle).
- **Direction = the faction's stance toward the Mayor.** Reuse `mayor.get_reputation(faction_id)`:
  a faction the Mayor stands well with (allied/warm) **Rallies** (+public support); a hostile one
  **Agitates** (−). Factions in the indifferent middle band don't bother — so it is a *meaningful*
  signal, not constant noise. (Trait hooks like "angry at mayor" / a loyalty trait can lift the
  weight further.)
- **Magnitude scales with faction rank**, consistent with the rank-weighting elections already use
  — a powerful faction sways more.
- **Effect on `mayor.reputation["the_public"]`** (the support source of truth), clamped −50..+50 as
  usual. Each action writes an `ActionResult` → the chronicle ("the Temple denounces the Mayor in
  the agora").
- **All magnitudes are balance dials** (`engine/balance.py`) — tunable, and per-difficulty if
  wanted.

## The loops it creates (the payoff)

- *Court a faction → it rallies the people for you* — makes the Mayor's existing Meet/Endorse
  actions doubly valuable (faction vote **and** public opinion).
- *Neglect or sabotage a faction → it turns the people against you* — neglect finally has teeth
  between elections, and it feeds the removal spiral.
- **The deal hook (the strongest part).** "Endorse me publicly" / "stop agitating against me"
  becomes a deal term, expressed with the deal system's existing `committed_action` /
  `committed_abstain`. A faction that pledged its public voice and then didn't deliver is tracked by
  the existing deal-fidelity/memory. This ties the headline LLM-negotiation USP directly to survival
  with near-zero new machinery.

## Risks / things to get right

- **Don't double-count carelessly.** A hostile faction would now hurt the Mayor two ways — its own
  rank-weighted election vote *and* by dragging public support down via Agitate. Thematically fine
  (a hostile house *should* hurt twice), but keep the per-cycle delta small (≈ ±1–3 × rank) so the
  faction layer doesn't swamp the public scale.
- **Mind the spiral.** Hostile factions tanking support → removal is a legitimate failure path, but
  only fair if recovery is reachable inside an election cycle. Keep the delta recoverable so
  diplomacy or a deal can turn the tide.
- **Stance threshold.** Pick the reputation bands at which a faction will Rally / Agitate so the
  indifferent middle stays quiet (avoids every faction swaying every cycle).
- **Weight tuning.** The new action's base weight must not crowd out the economic actions that keep
  the city (and the chains) running.

## Open questions

- **One signed action or two?** A single "Sway" whose sign comes from stance, vs. distinct
  Rally/Agitate actions (clearer in the chronicle and for trait modifiers). Lean two for legibility.
- **Does Rally/Agitate also touch unrest or only support?** Probably support only in v1 (keep it one
  clean channel); agitation feeding unrest is a tempting follow-up.
- **Should the City Guard counter Agitate** (it already suppresses unrest), or is diplomacy the only
  counter? Lean diplomacy-only — the Guard is a symptom tool, opinion is a cause.
- **Deal term in the same slice or a follow-up?** The hook is high value and cheap given
  committed_action/abstain exist, but it can ship a slice later if the core action is wanted first.

> **Status (2026-06-21):** SHIPPED. Core Rally/Agitate actions, plus both deal terms —
> `committed_action: "Rally"` ("publicly endorse me") and `committed_abstain: "Agitate"` ("cease
> agitating"). See `decisions/2026-06-21-faction-influence.md`, `-rally-deal-term.md`,
> `-agitate-abstain-term.md`.

## Spec Impact *(rough — finalize when scheduled)*

- **Changed:** `faction-behavior_spec.md` (the new action + its weight logic and stance threshold);
  `balance_spec.md` (the new magnitude/threshold dials); `public-needs_spec.md` (a new external
  driver of public support); optionally `audience_spec.md` (Rally/Agitate as a deal term).
- **New tests:** stance → direction, rank → magnitude, opportunity cost in selection, effect on
  public support, indifferent factions abstain, and (if included) the deal-term path.
- **Depends on:** nothing new — builds on the NPC action system, the public-support source of truth,
  the balance dials, and the deal system, all already in place.

## Cross-references

- [elections_spec](../specs/elections_spec.md) / [fail-states_spec](../specs/fail-states_spec.md) —
  what public support feeds (the verdict and the removal spiral this mechanic now influences).
- [audience_spec](../specs/audience_spec.md) — the deal system whose `committed_action` /
  `committed_abstain` express the Rally/Agitate deal term.
- [faction-behavior_spec](../specs/faction-behavior_spec.md) — the NPC action/weight system the new
  action joins.
