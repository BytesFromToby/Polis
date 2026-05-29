# Spec: Faction Descriptions

**Version:** v1
**Date:** 2026-05-29

Each faction gains two pieces of descriptive text, sourced from the canonical roster in
`Planning/reference/theming.md`: a short **blurb** (the italic gloss after the name) and a
fuller **description** (the one-line identity sentence). The blurb appears under each
faction in the left-panel browser; the description is shown to the player when an audience
opens and is also fed into the faction leader's LLM prompt so the roleplay reflects who the
faction is. Today neither string exists in the data — they live only as prose in
`theming.md`.

## Scope
- Does: add `blurb` (short gloss) and `description` (full identity line) string fields to the
  `Faction` model; populate both for all 41 factions in `backend/data/factions.json` from
  `theming.md`; carry them through `serialize_faction`/`deserialize_faction` and the JSON
  loader; show the blurb in the `GameView` left-panel faction block; show the description in
  `AudienceModal` when an audience opens; inject the description into the audience system
  prompt.
- Does NOT: change contest math, traits, ratings, cycle behaviour, or any tested engine
  logic (theming is content/flavor only — `theming.md`). Does NOT add or edit leader
  `personality_notes` (already present and used). Does NOT change the audience step flow,
  deal mechanics, or Mayor-confirm. Does NOT rewrite the theming.md prose — it is the
  source, transcribed verbatim into the data.

---

## Feature: Faction Description Data

`Faction` gains `blurb` and `description` (both `str`, default `""`). All 41 factions in
`backend/data/factions.json` get both filled from their `theming.md` entry: `blurb` = the
italic gloss after the em-dash on the name line; `description` = the one-line identity
sentence beneath it. Serializer and loader carry both fields.

- Input: `theming.md` per-faction prose (name-line gloss + identity sentence).
- Output: each faction record + `Faction` object carrying `blurb` and `description`.

**Done when:**
- The `Faction` model has `blurb` and `description` string fields, each defaulting to `""`  `[automated]`
- Every one of the 41 factions in `backend/data/factions.json` has a non-empty `blurb` and a non-empty `description`  `[automated]`
- Spot-checked transcription matches `theming.md`: e.g. `eumelidai` blurb contains "well-flocked" and description contains "senior clan"; `silverbench` blurb contains "money-changers" and description contains "bankers at their tables"  `[automated]`
- `serialize_faction` then `deserialize_faction` round-trips `blurb` and `description` unchanged  `[automated]`
- `load_state_from_json` on `backend/data` yields `Faction` objects whose `blurb` and `description` are populated  `[automated]`

---

## Feature: Short Description in the Left Panel

The `GameView` left-panel faction block (under the faction/leader name) shows the faction's
`blurb`.

- Input: `snapshot.factions[*].blurb` from `state.full`.
- Output: a short description line in each expanded faction block.

**Done when:**
- An expanded faction block shows its `blurb` text beneath the faction name/leader  `[human-required]`
- A faction whose `blurb` is empty renders no empty or broken description element  `[human-required]`

---

## Feature: Full Description at the Audience (display + prompt)

When an audience opens, `AudienceModal` shows the target faction's `description`, and the
faction's `description` is injected into the audience system prompt (alongside the existing
city description) so the leader speaks from their identity.

- Input: the target faction's `description` (UI from `snapshot.factions`; prompt from the
  `Faction` passed to `PromptBuilder.build`).
- Output: the description displayed in the audience UI, and present in the system prompt.

**Done when:**
- When an audience opens for a faction, `AudienceModal` displays that faction's `description`  `[human-required]`
- The built audience system prompt contains the faction's `description` text when it is set  `[automated]`
- A faction with an empty `description` produces a prompt with no empty/placeholder description artifact (the line is omitted cleanly)  `[automated]`

---

## Edges & Notes
- **Re-seed required.** `seed_official_cities` skips an already-seeded city (keyed by
  `city_name`), so the descriptions only reach a *new game* once the official "Polis" city
  template is refreshed from the updated `factions.json`. The build must refresh it (e.g.
  remove the existing official city row so it re-seeds at startup) — non-destructively for
  user-created cities and saved runs.
- **Existing saved runs** restore factions from their snapshot JSON, which predates these
  fields; they will show empty blurb/description (graceful `""` default). Only new games
  (post-refresh) carry the descriptions. This is acceptable.
- The two automated prompt criteria are unit-testable against `PromptBuilder.build` with a
  faction that has / lacks a `description`.

## Open Questions
<!-- none -->
