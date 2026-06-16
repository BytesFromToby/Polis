# Blueprint: Roster Restructure
Spec: Planning/specs/roster-restructure_spec.md
Date: 2026-06-14

> Data/structural migration: 41→28 factions, 9→7 domains. **No new mechanics.** The data, the
> `BASE_PROJECT_NAMES` catalog (code), and the consistency tests are *interlocked*
> (`test_theme_data` checks data + catalog together), so Slice 1 moves them as one unit and ends
> with the suite green — there is no clean intermediate where only the data has changed.
>
> New-faction `id`/`name`/`blurb`/`rating` come from the **decision log**
> (`Planning/decisions/2026-06-14-roster-restructure.md`); the user may revise the names later — use
> the proposals as written. Surviving factions keep their current `data/factions.json` entry verbatim
> unless the spec says otherwise. Recon facts: the data has **zero cross-references** (cuts dangle
> nothing); the **only** code referencing `harbor`/`trade`/`academy` is `BASE_PROJECT_NAMES`.

---

## Builder instructions
- Execute steps in order. Do not skip, reorder, or read ahead into the next slice.
- Check off each step when complete: [ ] → [x]
- One step = one logical concern. If a step can't be tested on its own, it's too small — merge it. If it touches more than one concern, split it.
- Deviation: if you do something differently than the step says, note it inline and keep going.
- Stuck: stop immediately. Do not try alternative approaches. Report exactly where and why.
- All test commands run from `backend/`: `py -m pytest tests/<file> -q`.

---

## Slice 1: The migration — data, catalog, tests, seed, docs [inspect]
**Scope:** `data/` holds the 28-faction / 7-domain roster, the project catalog and reference docs
match it, the official city re-seeds to it, and the full suite is green on the new roster.

### Step 1: Rewrite `data/factions.json` to the 28-faction roster
**Build:** Edit `data/factions.json` to exactly the 28 factions in the spec's "The new roster data"
table. **Keep** these 23 verbatim (id/rating/traits/blurb/description unchanged), re-homing the two
noted: `eumelidai`(4) `pyrrhidai`(3) `skiadai`(→rating **1.0**) `netmenders`(→domain **port**)
`storehouse-ring`(→domain **port**) `bronzehands` `keelwrights` `kerameis` `ovenmen` `winepressers`
`oil-pressers` `tanners` `weavers` `shieldsworn` `oarsworn` `asklepiads` `players` `quillsworn`
`perfumers` `greenmantle` `bright-order` `raving-choir` `tidesworn`. **Add** the 5 new factions from
the decision log: `elaiades`(aristocracy, r1.5), `the-builders`(guilds, r3.0), `dockhands`(port, r4.0),
`merchant-houses`(port, r4.0), `city-guard`(military, r3.0) — each with name/blurb/description from the
decision log and two functional traits (pick apt ones from the FUNCTIONAL_TRAITS set, e.g. dockhands
`industrious`+`conservative`, merchant-houses `opportunistic`+`ambitious`, city-guard
`defensive`+`aggressive`, the-builders `industrious`+`conservative`, elaiades `ambitious`+`conservative`).
**Remove** the 18 ids listed in the spec (stonewrights, carpenters, quaymen, harborwardens,
amphora-houses, saltroad-houses, outland-houses, free-spears, companions, stallmongers, silverbench,
adorners, garland-chasers, hearthwardens, grove, sophists, goldentongues, stargazers).
**Test:** `py -c "import json; f=json.load(open('data/factions.json',encoding='utf-8')); print(len(f)); from collections import Counter; print(Counter(x['domain_primary'] for x in f)); print(sum(int(x['rating']) for x in f if x['domain_primary']=='aristocracy'))"`
**Done When:** 28 factions; domain counts aristocracy 4 / guilds 9 / port 4 / military 3 / professions 4 / temples 4; aristocracy Σ`int(rating)` == 9.
**Stuck If:** A surviving faction's required fields are missing, or the JSON won't parse.
- [x] Complete

### Step 2: Rewrite `data/domains.json` to the 7 domains
**Build:** Edit `data/domains.json` to the six faction domains `aristocracy` `guilds` `port`
`professions` `temples` `military` plus `civic`. Delete `trade` and `academy`; rename the `harbor`
entry to `id: "port"`, `name: "Port"`. Each **faction** domain keeps `cap: 300`, `drift: 0.0`, and a
**rebuilt** `relationships` array with one entry per faction domain — `{"domain_id": X, "trait": "Foe"}`
when X is the domain itself, `"Neutral"` for every other faction domain (six entries each). `civic` is
unchanged: `name: "Public Treasury"`, `cap: 12`, `relationships: []`.
**Test:** `py -c "import json; d=json.load(open('data/domains.json',encoding='utf-8')); print(sorted(x['id'] for x in d)); [print(x['id'], len(x['relationships'])) for x in d]"`
**Done When:** Domain ids are exactly {aristocracy,guilds,port,professions,temples,military,civic}; each faction domain has 6 relationship entries (self Foe, others Neutral); civic has 0.
**Stuck If:** A relationship row references a deleted domain (`trade`/`academy`/`harbor`).
- [x] Complete

### Step 3: Update the project catalog `BASE_PROJECT_NAMES` (code)
**Build:** In `engine/projects/processing.py`, `BASE_PROJECT_NAMES`: remove the `"trade": "Agora"`
and `"academy": "Lyceum"` entries; rename `"harbor": "Docks"` → `"port": "Docks"`. The dict's keys
must become exactly the six faction domains + `"civic"`. Leave `BASE_PROJECT_DESCRIPTIONS` (empty)
and `base_project_name`/`base_project_description` logic unchanged.
**Test:** `py -c "from engine.projects import BASE_PROJECT_NAMES; print(sorted(BASE_PROJECT_NAMES))"` from `backend/`.
**Done When:** `set(BASE_PROJECT_NAMES) == {aristocracy,guilds,port,professions,temples,military,civic}`; no `trade`/`academy`/`harbor` key.
**Stuck If:** Another code site references `BASE_PROJECT_NAMES["harbor"|"trade"|"academy"]` directly (grep first).
- [x] Complete

### Step 4: Confirm no other code references the dead domain ids
**Build:** Grep `engine/ api/ db/` (excluding tests) for `"harbor"`, `"trade"`, `"academy"`. Recon
found only `BASE_PROJECT_NAMES` (now fixed). If any *other* live reference exists, fix it to `port`
(for harbor) or remove it (trade/academy) — **stop and report** if the fix isn't a mechanical id swap.
**Test:** `grep -rn -E '"(harbor|trade|academy)"' engine api db --include=*.py | grep -v test`
**Done When:** No live (non-comment) code reference to `harbor`/`trade`/`academy` remains.
**Stuck If:** A reference is logic-bearing (not a simple id) — report it.
- [x] Complete

### Step 5: Reconcile `tests/test_theme_data.py`
**Build:** Update the hardcoded old roster: `EXPECTED_DOMAIN_IDS` → `{aristocracy, guilds, port,
professions, temples, military}` (the 6 faction domains; civic is still checked separately);
`EXPECTED_FACTION_COUNTS` → `{aristocracy:4, guilds:9, port:4, military:3, professions:4, temples:4}`;
all `len(factions) == 41` → `== 28`; the docstring/comment "eight … domains" wording. The
`BASE_PROJECT_NAMES` assertion (`== EXPECTED_DOMAIN_IDS | {"civic"}`) then holds automatically. Keep
the legacy-prefix project-id checks.
**Test:** `py -m pytest tests/test_theme_data.py -q`
**Done When:** `test_theme_data.py` green.
**Stuck If:** A relationship-row or cap assertion fails for a reason other than the count change — report.
- [x] Complete

### Step 6: Reconcile `tests/test_seed_official.py`
**Build:** Update `EXPECTED_DOMAIN_IDS`, the `len == 41` → `== 28`, the "eight Greek domains / 41
factions" wording, and confirm `LEGACY_DOMAIN_IDS` now includes the newly-cut `trade`/`academy`/`harbor`
(the guard `test_no_legacy_domain_ids_in_db` should treat them as legacy). The seed reads the data
files, so a fresh-DB seed picks up the new roster.
**Test:** `py -m pytest tests/test_seed_official.py -q`
**Done When:** `test_seed_official.py` green; the seeded official city has 28 factions and the 7 domain ids.
**Stuck If:** The seed still produces 41 (the seed path caches/skips — see Step 8) — report.
- [x] Complete

### Step 7: Reconcile `tests/test_faction_descriptions.py`
**Build:** Update `len(factions) == 41` → `== 28`. Its blurb spot-check names **`silverbench`** (now
**cut**) — replace that assertion with a surviving faction (e.g. `merchant-houses` or keep the
`eumelidai` "well-flocked" check and swap the second to `bright-order`/`oil-pressers`). Confirm all 28
factions still have non-empty blurb+description (the 5 new ones from Step 1 included).
**Test:** `py -m pytest tests/test_faction_descriptions.py -q`
**Done When:** `test_faction_descriptions.py` green; no assertion references a cut faction id.
**Stuck If:** A new faction is missing blurb/description (fix in Step 1, note deviation).
- [x] Complete

### Step 8: Refresh the seeded official city
**Build:** In `db/seed.py` `seed_official_cities`: ensure a *stale* official "Polis" row (old roster)
is refreshed to the new roster on seed — e.g. detect the official city and replace it if its stored
domains contain a legacy id, **without** touching user-created cities or saved runs. (For a fresh DB
this is a no-op; this only matters for an existing dev DB.) If the existing logic already re-seeds a
fresh DB correctly and no persistent stale row is in play, keep the change minimal and note it.
**Test:** `py -m pytest tests/test_seed_official.py -q` (still green) + `py -c "from db.seed import seed_official_cities" ` import check.
**Done When:** Seeding a fresh DB yields the 28/7 official city; a stale official row would be refreshed; user cities untouched.
**Stuck If:** Refreshing risks deleting user data — stop and report (must be non-destructive).
- [x] Complete

### Step 9: Update reference docs
**Build:** `reference/data-models.md` — the domain list (currently the 9) → the 7 domains
(aristocracy, guilds, port, professions, temples, military, civic; note trade+academy removed,
harbor→port). `reference/theming.md` — remove the 18 cut faction entries, add the 5 new factions, the
Port section header (harbor→Port), and brief notes that Bright Order absorbs the star-readers and
Quillsworn the money-changing. Keep it consistent with `data/factions.json`.
**Test:** `grep -c -E "stargazers|silverbench|carpenters|hearthwardens" reference/theming.md` (expect 0 live entries) + manual read.
**Done When:** `data-models.md` lists 7 domains; `theming.md` names none of the 18 cut factions and includes the 5 new ones. (Human-required — inspector reads.)
**Stuck If:** —
- [x] Complete

---
⛔ End of Slice 1 [inspect]. Run **inspector** on this slice before continuing. (Checkpoint: full suite green on the new roster — 455 passed.)
**Deviations (Slice 1):**
- *Steps 1–2:* the factions.json/domains.json rewrites were done with a one-off Python transform
  (load → cut/re-home/add → write) rather than hand-editing 28+7 JSON objects — deterministic and
  less error-prone. Same result the steps describe.
- *Steps 5–7 (scope):* the test reconciliation surfaced **test-fixture** references to the dead
  domains beyond the three named test files: `test_audience_terms.py` (a synthetic `"trade"`
  faction asserting the "Agora" project name → switched to a `"guilds"` faction / "Workshop") and
  `test_domain_base_project_name.py` (`harbor`→"Docks" → `port`→"Docks"). Fixed as mechanical id
  swaps. Harmless synthetic uses of dead ids as arbitrary labels (test_actions, test_city_load_cap_freeze,
  test_events_system) were left — they don't break and aren't covered by the no-dead-id Done-when (engine/api/db only).
- *Food coupling (notable):* `tests/test_needs_dynamics.py` referenced the old 3-estate aristocracy.
  The Skiadai split added `elaiades`, so (a) the `ARISTOCRACY` tuple gained `elaiades`, and (b) the
  **legibility** test was reframed from *pin estates to 1.0* to *remove the aristocracy and restore*
  — because the extra estate raised the aristocracy floor (4 estates, each min level 1) so a pin is
  now cushioned by the redundancy and no longer drops a band. The test's property (visible ≤5 cycles,
  recover ≤15) is unchanged; the shortage is made severe enough to register. Same regime-shift category
  as the fish/flocks legibility repairs. The food **balance** is untouched (aristocracy Σ level == 9,
  redundancy bands all hold).
- *Step 8:* added an in-place **refresh** of a stale official template (update, not delete — FK-safe;
  user cities untouched) so an existing dev DB migrates; fresh DBs (the tests) take the create path.

---

## Final Slice: Save policy + full verification [inspect]
**Scope:** Old saves still load (graceful-but-stale), the food system is provably undisturbed, and
every spec Done-when holds.

### Step 1: Graceful old-save test
**Build:** In a suitable test file (e.g. `tests/test_seed_official.py` or a new `tests/test_roster_migration.py`),
add a test that builds a minimal serialized state dict carrying a **cut** faction id (e.g. `silverbench`)
and a **cut/renamed** domain id (e.g. `trade` or `harbor`), passes it through `deserialize_state`
(from `serializer`), and asserts it returns without error and the cut faction/domain round-trips into
the rebuilt objects (snapshots are self-contained — the current data files are irrelevant to restore).
**Test:** `py -m pytest tests/test_roster_migration.py -q` (or the chosen file).
**Done When:** An old-roster snapshot `deserialize_state`s without error — the new-games-only policy holds.
**Stuck If:** `deserialize_state` rejects an unknown faction/domain id (it shouldn't — it rebuilds from the dict) — report.
- [x] Complete

### Step 2: Confirm the food system is undisturbed
**Build:** No new code. Run the shipped food tests — the chain raw/redundancy/dynamics must be
unchanged (aristocracy Σ level was conserved at 9; the chain producer faction ids all survived).
**Test:** `py -m pytest tests/test_needs_chain.py tests/test_needs_dynamics.py tests/test_needs_cycle.py tests/test_toil.py -q`
**Done When:** All food tests green — the three-source redundancy and the harvest balance are unchanged.
**Stuck If:** A food test fails — the Σ level was not conserved or a producer id was lost; return to Slice 1 Step 1.
- [x] Complete

### Step 3: Headless run on the new roster
**Build:** No new code. Run the city.
**Test:** `py main.py --cycles 5` from `backend/`.
**Done When:** Runs to completion; the FACTIONS summary lists 28 factions; the `THE PUBLIC:` line is sane; no crash, no legacy id.
**Stuck If:** The run errors or references a cut faction/domain.
- [x] Complete

### Final Step: Verify spec Done when items
**Build:** No new code. Confirm every `**Done when:**` in `roster-restructure_spec.md` (all three
features). The `[human-required]` items: `theming.md`/`data-models.md` prose (Slice 1 Step 9) and a
freshly seeded game loading in the UI with the 7 domains and no legacy faction/domain — drive the
app (server + a fresh game) and capture evidence (playwright per CLAUDE.md).
**Test:** `py -m pytest tests/ -q` — full suite. Capture output.
**Done When:** Every `[automated]` criterion passes via its committed test; `[human-required]` items have captured evidence; the full suite is green.
**Stuck If:** An automated criterion fails and the cause is not clear from the output.
- [x] Complete

---
⛔ Final slice complete. Run **inspector** for final sign-off.
✅ Inspector: PASS — 2026-06-14
