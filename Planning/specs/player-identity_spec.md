# Spec: Player Identity

**Version:** v1
**Date:** 2026-05-29

The player and their city get a name at the start of a new game, and those names —
together with the player's title — are threaded into the LLM audience prompt so faction
leaders address the player by name and title and speak inside the canonical Greek world.
This also repairs a theme-conversion regression: the audience prompt currently injects a
blank tone line (the Greek voice in `reference/theming.md` was never wired into the prompt
builder), which flattened the leaders' "attitude."

## Scope
- Does: capture a **player name** and **city name** on the New Game screen (pre-filled
  with the canonical defaults — Kallisto, Polis); persist `player_name` and `player_title`
  on the run and the city name on the city; thread city name, player name, and title into
  the audience system prompt; replace the dead multi-theme `SETTING_TONE` lookup with the
  single canonical Greek **situation briefing** (with placeholders); rename "Mayor" → the
  player's title (Prytanis) throughout the audience prompt; sharpen the voice instruction.
- Does NOT: build the title/rank-progression system — the title is a fixed `"Prytanis"`
  default and is **not** user-editable in this feature (see `reference/theming.md`, "Player
  title — the rank ladder", future feature). Does NOT change the audience step flow, deal
  mechanics, Mayor-confirm behaviour, or debug instrumentation (`audience_spec.md`). Does
  NOT add multi-theme support — Polis has one canonical theme (`reference/theming.md`).
  Does NOT rename "Mayor" anywhere outside the audience prompt (engine model, API, other
  UI keep their current names).

---

## Feature: New-Game Identity Capture

The New Game button currently auto-loads the official template with no prompts. It instead
opens a small inline form on the title screen: a **player name** field and a **city name**
field, both pre-filled with the defaults, and a Start control. On Start the game begins
with the entered (or default) values.

- Input: player name and city name typed on the title screen (each pre-filled — Kallisto,
  Polis).
- Output: a started run whose persisted city name and player identity reflect the entered
  (or default) values.

The player **title** is not an input. It is set to the fixed default `"Prytanis"`.

**Done when:**
- The New Game flow shows a player-name field pre-filled "Kallisto" and a city-name field pre-filled "Polis", with a Start control  `[human-required]`
- Starting with the pre-filled defaults yields a run with `player_name` = "Kallisto", `player_title` = "Prytanis", and the city named "Polis"  `[automated]`
- Editing both fields and starting persists the entered player name and city name on the run/city  `[automated]`
- Submitting a blank player name or blank city name falls back to that field's default — no empty value is persisted  `[automated]`

---

## Feature: Identity Persistence

`player_name` and `player_title` are stored on the `SimRun` row, beside the existing
carried fields (`setting`, `description`, `details`). The city name continues to live on
the `City` row (`city_name`, already present and PATCH-able).

- Input: player name / title at run creation; city name at city setup.
- Output: durable run + city records carrying the identity, readable by the audience route.

**Done when:**
- `SimRun` has `player_name` and `player_title` columns; a run created without explicit values defaults to `player_name` = "Kallisto" and `player_title` = "Prytanis"  `[automated]`
- A snapshot/restore round-trip preserves `player_name`, `player_title`, and `city_name` (no value is lost or reset)  `[automated]`

---

## Feature: Prompt Threading & Single-Canon Briefing

`PromptBuilder.build` gains `city_name`, `player_name`, and `player_title` parameters. The
multi-theme `SETTING_TONE` dict is removed; the prompt instead always opens with the
canonical Greek **situation briefing** sourced from `reference/theming.md` ("LLM situation
briefing"), with `{city}`, `{player_name}`, and `{title}` substituted in. The audience
route reads the run's `player_name` / `player_title` and the city name and passes all three
into the builder, so every audience call (begin / reply / conclude) carries the same
identity-bearing system prompt.

- Input: `faction`, `mayor`, run + city records (for `city_name`, `player_name`,
  `player_title`), plus the existing context.
- Output: a system prompt that opens with the briefing and names the city, player, and
  title — never a blank tone line.

**Done when:**
- The built audience system prompt contains the city name, the player name, and the player title  `[automated]`
- The prompt opens with the canonical Greek briefing — its signature phrases ("bows to no king" and "never a master") are present in the built prompt  `[automated]`
- `SETTING_TONE` is removed; building a prompt produces the briefing regardless of any setting value, with no blank leading line  `[automated]`
- The audience route passes the run's `player_name`/`player_title` and the city name into the prompt builder for the begin step  `[automated]`

---

## Feature: Prompt Voice & Prytanis Rename

Inside the audience prompt, references to "Mayor" become the player's title (Prytanis),
fed by `player_title` — including the relationship line and the valid-terms templates
("What the Prytanis can offer you"). The brevity instruction is kept but the dampening
phrase "measured, not verbose" is replaced with a sharper, in-character line so leaders
keep their pride and edge.

- Input: the assembled prompt fields plus `player_title`.
- Output: a single in-theme register throughout the prompt; brevity preserved without
  flattening voice.

**Done when:**
- The built audience system prompt contains no occurrence of the word "Mayor"; player references use the title (e.g. "Prytanis")  `[automated]`
- The prompt no longer contains "measured, not verbose"; a brevity instruction (≈3–4 sentences) is retained alongside a voice line directing pride/edge  `[automated]`
- After the rename and voice change, a stub audience still yields a parseable `<deal>` block — the deal contract is unaffected  `[automated]`

---

## Edges & Notes
- The existing `test_setting_tone_injected` test (asserting DnD tone injection) is obsoleted
  by the single-canon briefing and must be updated or replaced.
- Deserialising an older run/snapshot that predates the new fields must default to
  Kallisto / Prytanis rather than error.
- `reference/theming.md`'s briefing currently hardcodes "Polis" and "the Prytanis" and has
  two defects to fix when it becomes the parameterised source: the typo "summond" →
  "summoned", and "stand before **Prytanis**" needs the substituted "{title} {player_name}".

## Open Questions
<!-- none -->
