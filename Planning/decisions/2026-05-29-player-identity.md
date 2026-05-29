# Decisions: Player Identity

Spec: Planning/specs/player-identity_spec.md
Date: 2026-05-29

- **Store `player_name` / `player_title` on `SimRun`, not the engine `Mayor` model** —
  run-scoped player identity sits beside the existing carried fields (`setting`,
  `description`), and the audience route already loads the run, so threading into the
  prompt is trivial. Rejected putting it on the `Mayor` dataclass: cleaner for the prompt
  path but ripples through the engine model, serializer, and every `Mayor` construction
  /restore. Cost accepted: a `SimRun` column add (the dev SQLite DB is recreated).

- **Single canonical briefing replaces the `SETTING_TONE` dict** — `reference/theming.md`
  declares one canonical Greek theme ("no multi-theme system"), and the multi-theme dict
  was already dead (the DB seeds `setting="Greek"`, which had no key, and the audience
  route never passed `city_setting` anyway → blank tone line). The prompt now always opens
  with the theming.md situation briefing. Rejected adding a `"Greek"` key: keeps a
  vestigial dict and a long value, and leaves the multi-theme fiction in the spec.
  `llm-system_spec.md` §"City Setting / Tone" updated to mark the dict superseded.

- **Rename "Mayor" → the player's title (Prytanis) throughout the audience prompt only** —
  one consistent in-theme register, fed by the stored `player_title`. Scope deliberately
  bounded to the prompt: the engine `Mayor` model, API, and other UI keep their current
  names (renaming those is out of scope and higher risk).

- **Title is a fixed `"Prytanis"` default, not a user input** — the rank-ladder system
  behind titles is a future feature (`reference/theming.md`). We persist the field now for
  forward-compatibility but do not expose it on the New Game form.

- **Theme regression root cause (for the record)** — the Greek theme conversion wrote the
  leader's voice into `reference/theming.md` ("LLM situation briefing") but never wired it
  into `prompt_builder.py`; `SETTING_TONE.get("Greek", "")` returned empty. This spec
  closes that gap and also fixes two defects in the briefing text (typo "summond";
  hardcoded "Prytanis"/"Polis" → placeholders).
