# Proposal: Elections & the Title Ladder (endgame)

**Date:** 2026-06-10
**Status:** PARTIALLY BUILT. The **election verdict** shipped 2026-06-21 as
[elections_spec](../specs/elections_spec.md) (slice 3a: rank-weighted approval, cadence, campaign
warning, approval readout; loss = game over). **Still unbuilt from this proposal:** the title
ladder + demotion-with-floor + victory at the top rung, and "support me in the election" as a deal
term. The sections below remain the design reference for those.

## Problem

A run cannot end well. The removal coalition (mayor_spec — Public rep ≤ −30 starts a 5-cycle
countdown; hostile-faction pressure; bankruptcy) is a **failure spiral**: it punishes, but
nothing ever *judges* the Mayor, and there is no positive arc to complete. Polis is currently a
sandbox with a brilliant mechanic; stakes, session rhythm, and replay all hang on a run being
able to end.

## Core idea

A recurring **election** every N cycles: the city renders a verdict on the Mayor's tenure.
Diegetic (the Prytanis answered to the Assembly), recurring (a heartbeat, not a single finish
line), and built almost entirely from currencies that already exist — Public support, per-faction
Mayor reputation, faction rank.

Paired with a **title ladder**: election wins and city growth advance the Mayor's title; the
title feeds back into how faction leaders treat the Mayor; reaching the highest title is a
victory condition.

## The vote (rough shape)

- **Electorate = the two currencies that already exist.**
  - *The Public* is the popular vote: its `support` (−50..+50) and disposition map to a vote
    weight. Public support finally has a payoff beyond the removal countdown.
  - *Faction leaders* are the influential vote: each faction votes by its Mayor-reputation tier
    (hostile/cold/neutral/warm/allied — the tiers exist), **weighted by rank**. This instantly
    makes faction rank matter *to the Mayor*, not just to the faction — propping up a friendly
    faction becomes electoral strategy, and Sabotage of a hostile one becomes voter suppression
    (with all the reputation consequences that should carry).
- **Cadence:** every N cycles (tunable constant, à la `CAP_HEADROOM_MULT`). The approach of an
  election is the session rhythm: a known judgment day that turns the preceding cycles into a
  campaign.
- **Outcome:** win → title progress (below) + a fresh mandate. Lose → see open question; the
  forgiving version is demotion on the title ladder, the roguelike version is game over.

## Deals as campaign politics (the high-value hook)

If "support me in the coming election" can be a **deal term**, the headline LLM-negotiation
mechanic becomes load-bearing for the endgame with near-zero new machinery: promises made before
the vote, the existing deal-fidelity/memory system tracking whether *either side* delivered
after. A faction that pledged its vote and was then sabotaged remembers. This is the single
strongest integration in the proposal — it should not be cut to "simplify."

This pairs with the stance layer (`crisis-and-stance.md`): an election result is exactly the
kind of major world moment that should trigger faction stance calls (gloating, resentment,
renewed loyalty).

## The title ladder

- A small ordered ladder of historical titles (exact set is theming work —
  `reference/theming.md`), advanced by election wins and/or city growth (population, once
  `resource-chains.md` lands, is the natural growth metric).
- **Titles change how leaders address the Mayor.** The title threads into the audience prompt
  the same way player identity already does (player-identity_spec: name/city/title are already
  in the prompt — the ladder makes the existing `title` field *dynamic*). A lowly Prytanis gets
  haggled with; a revered Archon gets deference — attitude shifts in the prompt, not just
  cosmetics. This was the original design intent: advancement the player *feels in conversation*.
- **Reaching the highest title = victory.** Combined with the existing removal spiral and
  bankruptcy as defeats, a run now has both poles.

## Prerequisite: a visible approval signal

Elections feel arbitrary unless the player can watch the needle move. Per-faction Mayor
reputation and Public support exist in engine state but are not first-class UI. Surfacing an
approval readout (and ideally a pre-election forecast) is a **prerequisite, not polish** — it is
what converts a loss from "random" to "I saw it coming and fought it."

## How the pieces chain (the roadmap spine)

resource chains give the city a body → disasters wound it (`crisis-and-stance.md`) → stance
layer makes factions react in character → audiences are how the Mayor triages → the election
judges the handling → titles are the score. Every existing system load-bearing, one spine.

## Open questions

- **What does losing mean?** Game over (clean, roguelike, makes runs tense) vs title demotion
  with game-over only at the bottom rung (forgiving, makes the ladder two-directional). Pick by
  intended run length; demotion-with-floor is the likely default.
- Vote math: simple weighted sum vs a per-faction d20-style roll against reputation (texture vs
  legibility). Lean legible — the forecast UI wants determinism-ish math.
- Does the existing removal coalition stay alongside elections (mid-term coup vs scheduled
  judgment), or fold into "snap election triggered by crisis"? Both existing removal triggers
  (Public ≤ −30, bankruptcy) map cleanly onto a snap-election trigger.
- Can the Mayor *campaign*? (Endorse/Condemn/Meet already move reputation — maybe that's the
  campaign kit and no new actions are needed. Flagged in the mayor-actions decision as the next
  consolidation candidates; an election gives them their job.)
- N for the cadence — long enough to govern, short enough that a session contains at least one
  verdict. Probably 10–15 cycles to start.
