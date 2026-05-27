# Spec: Greek Theme Conversion

Converts the running game from the legacy Twin Cities placeholder data to the canonical
ancient-Greek theme defined in `Planning/reference/theming.md`. This is a pure content/data
re-skin: it swaps the seed data to the eight Greek domains and their factions (using default
mechanical values), collapses the game to a single official city, deletes the obsolete Rivers
Point data and all old saved games, and refreshes stale theme references in the specs and
README. No engine logic changes — the simulation runs identically, just with the Greek roster.

## Scope
- **Does:** rewrite `backend/data/domains.json` and `factions.json` to the eight Greek domains
  and ~41 factions from `theming.md`; collapse `seed.py` to one official city, "Polis"; delete
  Rivers Point data and all old saved games; refresh theme references in `city-generation_spec.md`,
  `treasury_spec.md`, and `README.md`.
- **Does NOT:** change engine logic, contest math, or cycle behavior; wire faction-to-faction
  relationships (they stay empty/inert); reflavor the player term "Mayor" to the rank ladder;
  balance or tune the mechanical numbers — default values only, deliberate balancing is a later
  spec.

The source of truth for all names, traits, and leaders is `Planning/reference/theming.md`. The
engine data structures and field names are unchanged — see `Planning/reference/data-models.md`.

## Feature: Greek seed data

Rewrite `backend/data/domains.json` and `backend/data/factions.json` to encode the eight Greek
domains and their factions, using default mechanical values (a later balance pass tunes them).

- Input: the domain roster and faction entries in `theming.md` (names, character traits with
  intensities, leader names and personality notes).
- Output: `domains.json` (8 records) and `factions.json` (41 records) that load via `loaders.py`
  in the existing embedded-leader format (matching the current `data/factions.json` shape).

**Default values (uniform; tuned later):**

Domains — for each of the eight:
- `id`: kebab-case of the English name — `aristocracy`, `guilds`, `trade`, `professions`,
  `temples`, `military`, `academy`, `harbor` (the article in "The Professions" is dropped)
- `name`: English display name
- `cap`: `300`
- `drift`: `0.0`
- `relationships`: a full row covering all eight domains — the self-entry trait `Foe` (so
  factions within a domain compete), every other domain `Neutral`

Factions — for each of the ~41:
- `id`: kebab-case of the name
- `name`, `domain_primary`: from `theming.md` (owning domain id)
- `rating`: `3.0` · `health`: `80` · `entrench`: `75` · `leadership_need`: `0.0`
- `traits`: the faction's **Character traits** from `theming.md`, each `{trait, intensity}` as
  written (these are the engine's functional traits)
- `leader`: `{ name: <doc name>, traits: [<faction's character trait names>], status: "present",
  personality_notes: [<the doc's leader sentence>] }`
- `relationships`: `[]` (empty — inert, deferred)

Per-domain faction counts must match `theming.md` exactly: Aristocracy 3, Guilds 10, Trade 5,
The Professions 6, Temples 5, Military 4, Academy 4, Harbor 4 — total **41**.

**Done when:**
- `domains.json` contains exactly 8 domains with ids `{aristocracy, guilds, trade, professions, temples, military, academy, harbor}`; each has `cap` 300, `drift` 0.0, and a `relationships` row with one entry per domain (self = `Foe`, all others = `Neutral`)  `[automated]`
- `factions.json` contains 41 factions; every `domain_primary` resolves to one of the 8 domain ids; per-domain counts are 3/10/5/6/5/4/4/4 matching `theming.md`  `[automated]`
- every faction `trait` is one of the ten functional traits (`aggressive`, `defensive`, `ambitious`, `paranoid`, `opportunistic`, `expansionary`, `conservative`, `corrupt`, `industrious`, `destructive`) and every `intensity` ∈ {`slight`,`moderate`,`strong`,`very`}  `[automated]`
- `loaders.load_state_from_json("backend/data")` returns 8 domains and 41 factions without error  `[automated]`
- `py tools/validate_state.py` passes against `backend/data` (every faction domain reference resolves)  `[automated]`

## Feature: Single official city; remove Rivers Point

`seed.py` seeds exactly one official city, "Polis", loaded from `backend/data/`. The Rivers
Point entry and its data files are deleted.

- Input: the `_OFFICIAL_CITIES` list in `seed.py`; `backend/data/past_cities/Rivers_Point/`.
- Output: a single-entry `_OFFICIAL_CITIES`; the Rivers Point directory removed.
- Rules:
  - `_OFFICIAL_CITIES` holds one entry: `city_name="Polis"`, `data_dir="data"`, with a
    description that no longer mentions a "pending re-theme."
  - Delete `backend/data/past_cities/Rivers_Point/` and all its files.
  - No remaining references to Rivers Point in `backend/` (code or data).

**Done when:**
- `seed_official_cities` seeds exactly one official city named "Polis", carrying the 8 Greek domains and 41 factions  `[automated]`
- `backend/data/past_cities/Rivers_Point/` does not exist  `[automated]`
- a grep for `Rivers` / `Rivers_Point` across `backend/` returns no matches  `[automated]`

## Feature: Clear old saved games

Remove the legacy SQLite database so no old-theme cities or saved games persist; the app
recreates and re-seeds a fresh database on next startup.

- Input: `backend/polis.db` (the default SQLite store; `POLIS_DB_URL` can override the location).
- Output: no old `polis.db`; on next server/CLI startup a fresh DB seeded with the Greek "Polis"
  as the only official city.
- Rules: delete the database file at the default location (`backend/polis.db`). Startup
  initialization recreates the schema and seeds the single Greek official city. If an operator
  has set `POLIS_DB_URL` to a non-default store, they clear that store themselves (documented,
  not automated).

**Done when:**
- after conversion, a fresh server/CLI startup produces a `polis.db` whose only official city is "Polis" with the 8 Greek domains  `[automated]`
- no city in the database references any legacy domain id (e.g. `traditional_media`, `political`, `street`, `underworld` in its old sense) or any Rivers Point faction  `[automated]`

## Feature: Refresh stale theme references

Update theme-bound text in the specs and README to the Greek theme.

- Input: `Planning/specs/city-generation_spec.md`, `Planning/specs/treasury_spec.md`, `README.md`.
- Output: the same files with old-theme references replaced.
- Rules:
  - `city-generation_spec.md`: replace the 14 legacy domains (and drift table) with the 8 Greek
    domains; replace the dead `scr/data/` path with `backend/data/`; replace the Rivers Point
    starting-projects example. Keep its `FUTURE FEATURE` status.
  - `treasury_spec.md`: replace the "Rivers Point starts with 2…" line with the Greek city (or a
    generic "the starting city").
  - `README.md`: replace the "twelve domains (Media, Political, Street…)" and "newsrooms,
    political blocs, community groups, criminal networks" copy with the eight Greek domains and
    Greek faction flavor; correct the domain count.

**Done when:**
- a grep across `Planning/specs/` and `README.md` for legacy terms (`Twin Cities`, `Minneapolis`, `Rivers Point`, `scr/data`, and the old domain names) returns no matches  `[automated]`
- `city-generation_spec.md` lists the eight Greek domains; `README.md` states eight domains and names the Greek ones  `[automated]`
- README theme copy reads cleanly and matches `theming.md`  `[human-required]`

## Open Questions
<!-- none -->
