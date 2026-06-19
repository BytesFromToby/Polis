# Adopt the Geometric-pottery UI + quadrant relayout

**Date:** 2026-06-17
**Spec:** `game-ui_spec.md` (rewritten). **Reference:** `reference/ui-art-direction.md` (new,
promoted from the proposal). **Proposal archived:** `archive/ui-pottery-art-direction.md`.

## What

The play UI's deferred "thematic redo" is picked up. Two things land together: the **Geometric-
pottery art direction** (was a proposal, now adopted) and a **quadrant relayout** of `GameView`
(arrived at by iterating a mockup to v6 with the user).

## Decisions

**Pottery over Wine-Dark.** The verdigris/wine "Wine-Dark" tokens are replaced by glaze-brown
grounds, terracotta figure-ink, clay text, and oxblood-for-conflict. Reference: 8th-c. Geometric
Attic pottery — stacked bands, flat silhouettes, ornament at the edges.

**Port the primitives into the existing token architecture — do not rewrite.** `style.css` already
has a clean semantic-token layer; the reskin swaps primitive *values* and adds band-chrome classes.
Low-risk, reversible, reskins the whole app in one pass. (The proposal's open question, resolved.)

**Two-glaze themes.** Red-figure = dark (default), black-figure = light, via the existing
`data-theme` switch. Dark ships first; light follows. The inversion test constrains colour choices now.

**Quadrant relayout** (user-art-directed): left rail splits into Factions (top) + Projects (bottom);
the main panel fills the right and splits into the Mayor command panel (top) + Active Events &
Chronicle (bottom). Both columns share the midline.

**Mayor panel becomes the command centre.** Treasury + Action Points (pips, between Spent and the
buttons) + Take Action / Hold Audience on the left; the **seven-scale People readout** as a co-header
on the right (it extends up beside the Mayor title). **Standing and World are dropped** from this
panel — reputation lives in the audience/faction context; chaos gets a later home. This also closes
the long-standing gap: piety/unrest/consumption/confidence finally surface in the UI (the engine has
served their band keys since v0.3.0).

**Active Events is a new panel** sourced from the live event deck (name + cycles-remaining; oxblood
for disasters, terracotta for boons), beside the Chronicle highlights — the old centre-bottom Event
Log's home.

## Deferred (out of this build)
Per-domain silhouette **emblems**; the **LLM-chronicler** in-character cycle summaries (the Highlight
uses the existing dramatic-beat narrative for now); **light-mode polish** (dark first); a home for
the dropped **chaos/Standing** detail.

## Note
A UI spec is mostly `[human-required]` Done-when items — the inspector verifies via playwright
screenshots (per CLAUDE.md), not pytest. The few `[automated]` items are the build succeeding, the
projects/public-state data the panels consume, and the no-`commission`/no-`entrench`/no-raw-`rating`
guards.
