# Decisions: Faction Descriptions

Spec: Planning/specs/faction-descriptions_spec.md
Date: 2026-05-29

- **Two fields — `blurb` (short gloss) and `description` (full identity line)** — maps the
  two distinct text pieces in `theming.md`'s per-faction format onto two distinct lengths:
  `blurb` for the dense left-panel list, `description` for the audience. Rejected a single
  combined field (left panel would be too long) and rejected showing the whole theming.md
  block (character/leader lines duplicate data already on the faction).

- **Store the text in `factions.json` + the `Faction` model, not parsed from `theming.md`
  at runtime** — runtime markdown parsing of a reference doc is fragile and couples the
  engine to doc formatting. The data is the source of truth once transcribed; `theming.md`
  remains the human-authored origin.

- **Description is fed into the LLM audience prompt, not just displayed** (user's call) —
  the faction's self-conception strengthens in-character roleplay. `PromptBuilder.build`
  already receives the `Faction`, so it reads `description` directly; no new plumbing into
  the audience flow is required. An empty description omits the line cleanly.

- **Refresh the seeded official city rather than add an upsert/versioning system** — the
  seeder intentionally skips existing cities; a one-time refresh of the official "Polis"
  template is enough to propagate the new fields to new games. Building a city-template
  migration/versioning mechanism is out of proportion for a content addition.
