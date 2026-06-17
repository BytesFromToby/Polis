# Confidence — the 7th scale's band-consequences

**Date:** 2026-06-17
**Spec:** `public-needs_spec.md` (Feature: Confidence), `faction-behavior_spec.md` (posture
modifier), `events_spec.md` (gates + 3 flagships). **Proposal:** `../proposals/public-model.md`.
**Scope call (user):** "Band-gated pressure event only" for the Removal Coalition (no hard endgame).

## What

Confidence is the last of the seven Public scales — and it is **not new state**: it is the
existing `support` axis (−50..+50), given the band-consequences the proposal's matrix calls for.

## Decisions

**No new field — confidence reads `support`.** `support` (owned by `special-factions_spec.md`) is
the confidence axis. This slice adds a 5-band view over the −50..+50 range
(Hostile/Suspicious/Neutral/Favorable/Beloved) and its consequences. `disposition` stays as the
separate coarse label; confidence is the finer band the events + behavior modifier read.

**Bands over −50..+50, not 0–100.** Unlike the other scales, the band table is on the support
range: Hostile ≤−30, Suspicious −29..−10, Neutral −9..+10, Favorable +11..+30, Beloved ≥+31.

**Standing consequence = faction posture.** Low confidence (Hostile/Suspicious) emboldens rivals
(Harm/Steal lifted); high (Favorable/Beloved) damps open aggression (public backing raises its
cost). A faction-behavior Step-3 modifier, mirroring the unrest→crime one. This generalizes the
old disposition→faction-politics intent into the band model.

**Removal Coalition = a band-gated PRESSURE event, not the endgame.** The removal-countdown
machinery in `moneylender.py` exists but is **dormant** (never wired into the runner). Per the
user's scope call, this slice does NOT activate a hard countdown-to-defeat — that belongs to
`../proposals/elections-and-titles.md`. Instead, Hostile confidence fires a Removal Coalition
*event* that emboldens a ringleader faction (rating + domain chaos) — real pressure, no game-over.

**Events reuse existing effect fields.** Removal Coalition (rating + chaos), Effigy (rating +
public support), Acclamation (public support windfall) — all via existing `rating`/`chaos`/
public-targeted effects. No trait-add machinery (the standing behavior modifier carries the
"emboldened" posture). Acclamation's title-ladder step is deferred to elections-and-titles; for
now it is the political-capital (support) boost.

## Result
The Public's seven-scale model from `public-model.md` is **structurally complete**. Deferred
(not part of "the scales"): the hard removal endgame, misery→drink feedback, the multiplier on
non-food production, the richer event deck, and the title ladder.
