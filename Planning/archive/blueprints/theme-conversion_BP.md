# Blueprint: Greek Theme Conversion
Spec: Planning/specs/theme-conversion_spec.md
Date: 2026-05-26

---

## Builder instructions
- Execute steps in order. Do not skip, reorder, or read ahead into the next slice.
- Check off each step when complete: [ ] → [x]
- One step = one logical concern. If a step can't be tested on its own, it's too small — merge it. If it touches more than one concern, split it.
- Deviation: if you do something differently than the step says, note it inline and keep going.
- Stuck: stop immediately. Do not try alternative approaches. Report exactly where and why.
- **Source of truth for content:** `Planning/reference/theming.md` (domain roster + faction entries). Engine field names: `Planning/reference/data-models.md`. Match the existing embedded-leader JSON shape in the current `backend/data/factions.json`.
- Run all commands from `backend/` unless told otherwise.

---

## Slice 1: Greek seed data
**Scope:** `backend/data/domains.json` and `factions.json` hold the eight Greek domains and 41 factions with default values, and load cleanly.

### Step 1: Write the eight Greek domains
**Build:** Rewrite `backend/data/domains.json` with exactly eight domain records, ids `aristocracy`, `guilds`, `trade`, `professions`, `temples`, `military`, `academy`, `harbor` (drop the article on "The Professions"). Each: `name` = English display name from `theming.md`, `cap` = 300, `drift` = 0.0, and a `relationships` array with one entry per domain — the self-entry `trait` = `"Foe"`, every other domain `trait` = `"Neutral"`. Use the existing `domains.json` structure as the format reference.
**Test:** `py -c "import json; d=json.load(open('data/domains.json')); print(len(d))"` prints `8`.
**Done When:** `domains.json` parses; 8 records with the exact ids; each has cap 300, drift 0.0, and an 8-entry relationships row (self Foe, rest Neutral).
**Stuck If:** `theming.md` is missing a domain or the existing JSON format is unclear.
- [x] Complete

### Step 2: Write the 41 factions
**Build:** Rewrite `backend/data/factions.json` with the factions from `theming.md`, in the embedded-leader format. Per-domain counts must be exactly: aristocracy 3, guilds 10, trade 5, professions 6, temples 5, military 4, academy 4, harbor 4 (total 41). For each faction: `id` (kebab-case of name), `name`, `domain_primary` (owning domain id), `rating` 3.0, `health` 80, `entrench` 75, `leadership_need` 0.0, `traits` = the doc's Character traits as `{trait, intensity}`, `leader` = `{name, traits: [<the faction's character trait names>], status: "present", personality_notes: [<the doc's leader sentence>]}`, `relationships` = `[]`.
**Test:** `py -c "import json; f=json.load(open('data/factions.json')); print(len(f))"` prints `41`.
**Done When:** `factions.json` parses; 41 factions; every `domain_primary` is one of the 8 ids; per-domain counts match; every trait is one of the 10 functional traits with a valid intensity.
**Stuck If:** A faction in `theming.md` lists a trait not in the functional set, or a domain count doesn't add to 41.
- [x] Complete

### Step 3: Write the committed data test
**Build:** Add `backend/tests/test_theme_data.py` encoding the Feature "Greek seed data" Done-when items: (a) load `backend/data/domains.json` → exactly 8 domains with the expected ids, each cap 300 / drift 0.0, and a relationships row covering all 8 (self Foe, others Neutral); (b) load `factions.json` → 41 factions, per-domain counts 3/10/5/6/5/4/4/4, every `domain_primary` resolves to a domain id, every trait ∈ the 10 functional traits, every intensity ∈ {slight,moderate,strong,very}; (c) `loaders.load_state_from_json("data")` (or the path the suite uses) returns 8 domains and 41 factions.
**Test:** `py -m pytest tests/test_theme_data.py -q` passes.
**Done When:** All assertions in `test_theme_data.py` pass.
**Stuck If:** `load_state_from_json` raises, or a count/trait assertion fails and the data looks correct (possible format mismatch with the loader).
- [x] Complete

### Step 4: Validate the data with the existing tool
**Build:** No new code. Run the project's state validator against the new data.
**Test:** `py tools/validate_state.py` (point it at `backend/data` if it takes an arg) exits clean.
**Done When:** `validate_state.py` reports no errors (all faction domain references resolve).
**Stuck If:** The validator flags a broken reference or unknown id.
- [x] Complete

---
⛔ End of Slice 1. Run **inspector** on this slice before continuing.

---

## Slice 2: Single official city; remove Rivers Point
**Scope:** `seed.py` seeds exactly one official city, "Polis"; Rivers Point is gone from data and code.

### Step 1: Collapse `_OFFICIAL_CITIES` to one Greek city
**Build:** In `backend/db/seed.py`, reduce `_OFFICIAL_CITIES` to a single entry: `city_name="Polis"`, `data_dir="data"`, and a `description` that no longer mentions a "pending ancient-Greek re-theme" (describe the eight Greek domains instead). Remove the Rivers Point `_CityDef`.
**Test:** `py -c "from db.seed import _OFFICIAL_CITIES; print(len(_OFFICIAL_CITIES), _OFFICIAL_CITIES[0].city_name)"` prints `1 Polis`.
**Done When:** `_OFFICIAL_CITIES` has one entry named "Polis" loading from `data`.
**Stuck If:** Other code imports or depends on the Rivers Point `_CityDef` entry.
- [x] Complete

### Step 2: Delete the Rivers Point data
**Build:** Delete `backend/data/past_cities/Rivers_Point/` and all its files. If `past_cities/` is then empty, remove it too.
**Test:** `py -c "import os; print(os.path.exists('data/past_cities/Rivers_Point'))"` prints `False`.
**Done When:** The Rivers Point directory no longer exists.
**Stuck If:** A file there is referenced elsewhere (search before deleting).
- [x] Complete

### Step 3: Write the committed seeding test
**Build:** Add a test (extend `test_theme_data.py` or add `backend/tests/test_seed_official.py`) that seeds into a fresh/in-memory SQLite DB via `seed_official_cities` and asserts: exactly one official city named "Polis", carrying 8 domains and 41 factions. Follow the existing db-test pattern for session setup.
**Test:** `py -m pytest tests/test_seed_official.py -q` (or the extended file) passes.
**Done When:** The test proves a single official "Polis" city with 8 domains and 41 factions is seeded.
**Stuck If:** No existing db-test pattern to copy, or seeding requires fixtures you can't construct.
- [x] Complete

### Step 4: Confirm no Rivers Point references remain
**Build:** No new code. Search `backend/` for stragglers.
**Test:** `grep -ri "rivers" backend/` (via the Grep tool) returns no matches in code or data.
**Done When:** No `Rivers` / `Rivers_Point` references anywhere under `backend/`.
**Stuck If:** A reference remains in code you haven't touched — report it.
- [x] Complete

---
⛔ End of Slice 2. Run **inspector** on this slice before continuing.

---

## Slice 3: Clear old saved games
**Scope:** The legacy database is gone; a fresh startup re-seeds only the Greek Polis.

### Step 1: Delete the default database
**Build:** Delete `backend/polis.db` if it exists (the default `sqlite:///polis.db` store). Do not change `session.py` defaults.
**Test:** `py -c "import os; print(os.path.exists('polis.db'))"` prints `False`.
**Done When:** No `polis.db` at the default location.
**Stuck If:** The file is locked by a running server — stop and report.
- [x] Complete

### Step 2: Write the committed fresh-seed test
**Build:** Add a test (in `test_seed_official.py`) that initializes a fresh DB, runs the startup seed, and asserts: the only official city is "Polis"; its domains are exactly the 8 Greek ids; and no city in the DB references any legacy domain id (`traditional_media`, `political`, `street`, `high_society`, `bureaucracy`, `university`, etc.).
**Test:** `py -m pytest tests/test_seed_official.py -q` passes.
**Done When:** The test proves a fresh DB contains only the Greek Polis and no legacy domain ids.
**Stuck If:** Startup seeding can't be invoked in isolation from the test.
- [x] Complete

### Step 3: Confirm a real fresh startup re-seeds
**Build:** No new code. Run the app once to regenerate the DB.
**Test:** `py main.py --cycles 1` runs without error and a new `polis.db` is created seeded with the Greek Polis (or start the server and confirm the city list shows Polis with the 8 Greek domains).
**Done When:** A fresh `polis.db` exists containing the Greek Polis; the run completes without error.
**Stuck If:** Startup errors on the new data (trace the failing loader/seed call).
- [x] Complete

---
⛔ End of Slice 3. Run **inspector** on this slice before continuing.

---

## Final Slice: Refresh references and verify
**Scope:** Stale theme references updated across specs and README; full spec verification.

### Step 1: Update `city-generation_spec.md`
**Build:** In `Planning/specs/city-generation_spec.md`, replace the 14 legacy domains and their drift table with the 8 Greek domains; replace the dead `scr/data/` path with `backend/data/`; replace the Rivers Point starting-projects example with a Greek one (or mark it generic). Keep the `FUTURE FEATURE` status line.
**Test:** Grep the file for `Traditional Media`, `High Society`, `scr/data`, `Rivers Point` → none.
**Done When:** The spec lists the 8 Greek domains and has no legacy theme terms.
**Stuck If:** N/A.
- [x] Complete

### Step 2: Update `treasury_spec.md`
**Build:** Replace the "Rivers Point starts with 2…" line with the Greek city name "Polis" (or a generic "the starting city").
**Test:** Grep the file for `Rivers Point` → none.
**Done When:** No Rivers Point reference in `treasury_spec.md`.
**Stuck If:** N/A.
- [x] Complete

### Step 3: Update the README
**Build:** In `README.md`, replace the "twelve domains (Media, Political, Street…)" line and the "newsrooms, political blocs, community groups, criminal networks" flavor with the eight Greek domains and Greek faction flavor; correct any domain-count number. Match the tone of `theming.md`'s Overall Theme.
**Test:** Grep `README.md` for `twelve domains`, `Media, Political`, `newsrooms` → none.
**Done When:** README describes eight Greek domains and names them; no legacy theme copy remains.
**Stuck If:** N/A.
- [x] Complete

### Step 4: Confirm no legacy terms across specs and README
**Build:** No new code. Sweep for stragglers.
**Test:** Grep `Planning/specs/` and `README.md` for `Twin Cities`, `Minneapolis`, `Rivers Point`, `scr/data`, and the old domain names → no matches.
**Done When:** No legacy theme terms anywhere in specs or README.
**Stuck If:** A legacy term remains in a spec not listed in scope — note it and report.
- [x] Complete

### Step 5: Keep the existing suite green
**Build:** Run the full test suite. If any existing test fails because it hardcoded legacy domain/faction ids or the Rivers Point city, update that test to the Greek data (this is fixture maintenance, not a behavior change). Do not alter engine logic.
**Test:** `py -m pytest tests/ -q` — all tests pass.
**Done When:** The full suite is green with the new data.
**Stuck If:** A failure traces to engine logic rather than a data/fixture reference — stop and report.
- [x] Complete

### Final Step: Verify spec Done when items
**Build:** No new code. Confirm all spec `**Done when:**` items are met.
**Test:** Run `py -m pytest tests/ -q` (every `[automated]` item has a committed test from Slices 1–3 and Step 4 grep checks); run `py tools/validate_state.py`; run `py main.py --cycles 5` on the Greek city. Capture output. For the README `[human-required]` item, capture the rendered README intro for human review.
**Done When:** Every `[automated]` criterion passes via its committed test/check; the `[human-required]` README copy has captured evidence for a human to judge.
**Stuck If:** An automated criterion fails and the cause is not clear from the output.
- [x] Complete

---
⛔ Final slice complete. Run **inspector** for final sign-off.
