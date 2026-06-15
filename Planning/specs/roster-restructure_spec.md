# Spec: Roster Restructure

A pure data/structural migration from the current **41-faction / 9-domain** roster to the designed
**28-faction / 7-domain** roster (`../proposals/faction-resource-map.md` → Roster Decisions). No new
gameplay mechanics — factions are cut, merged, split, and re-homed; two domains are deleted and one
renamed; everything that references the roster (seed, caps, project catalog, tests, reference docs)
is brought into line. The point is to unlock the downstream slices (City Guard, Port mechanics,
differentiated estates) that assume this roster.

## Scope
- Does: rewrite `data/factions.json` (→ 28) and `data/domains.json` (→ 7); update the code project
  catalog (`BASE_PROJECT_NAMES`) and `reference/theming.md` + `reference/data-models.md`; re-seed the
  official city; update the roster-count/consistency tests; keep the shipped food chains and the full
  suite green.
- Does NOT: add or change any mechanic (the cut factions simply disappear; merges are new data rows;
  Garland-Chasers' "becomes an event" and the City Guard's *behaviour* are later slices — this slice
  only adds the City Guard faction *entry*); migrate existing saved games (new games only — see
  Feature: Seed, saves & docs); re-tune the food balance (aristocracy Σ level is conserved); build
  the wine/oil/goods chains the new estates/factions will later feed.

## Feature: The new roster data

`data/factions.json` becomes exactly these **28** factions (surviving factions keep their current
`id`/`rating`/`traits`/`blurb`/`description` unless noted; `Σ level` per `int(rating)`). Ids use the
existing hyphen convention.

**aristocracy (4)** — Σ level conserved at **9** (so the harvest chain is undisturbed):
| id | name | rating | note |
|---|---|---|---|
| `eumelidai` | The Eumelidai | 4.0 | keep — flocks |
| `pyrrhidai` | The Pyrrhidai | 3.0 | keep — grain |
| `skiadai` | The Skiadai | **1.0** | was 2.0 — now the **vine** estate (grapes) |
| `elaiades` | The Elaiades | **1.5** | **NEW** olive estate (the stronger of the split pair; still level 1, so Σ=9) |

**guilds (9)** — keep 8, merge 2:
`bronzehands`(3) `keelwrights`(2) `kerameis`(2) `ovenmen`(2) `winepressers`(2) `oil-pressers`(4)
`tanners`(2) `weavers`(2) kept, plus **NEW** `the-builders` "The Builders" r3.0 (merge of
`stonewrights`+`carpenters`).

**port (4)** — new domain id `port` (was `harbor`):
`netmenders`(2, re-homed harbor→port) and `storehouse-ring`(3, re-homed trade→port) kept, plus
**NEW** `dockhands` "The Dockhands" r4.0 (merge `quaymen`+`harborwardens`) and **NEW**
`merchant-houses` "The Merchant Houses" r4.0 (merge `amphora-houses`+`saltroad-houses`+`outland-houses`).

**military (3)**: `shieldsworn`(4, the Army/land force) and `oarsworn`(3, the Fleet) kept, plus
**NEW** `city-guard` "The City Guard" r3.0 (internal order — its behaviour is a later slice).

**professions (4)**: `asklepiads`(3) `players`(2) `quillsworn`(3) `perfumers`(2) kept. (`quillsworn`
absorbs the cut Silverbench's bookkeeping — identity/blurb note only, no field change.)

**temples (4)**: `greenmantle`(2) `bright-order`(4) `raving-choir`(2) `tidesworn`(3) kept.
(`bright-order` absorbs the cut Stargazers' sky-knowledge — identity/blurb note only.)

**Removed (18 ids)**: `stonewrights` `carpenters` (→ builders); `quaymen` `harborwardens`
(→ dockhands); `amphora-houses` `saltroad-houses` `outland-houses` (→ merchant-houses); `free-spears`
`companions` `stallmongers` `silverbench` `adorners` `garland-chasers` `hearthwardens`; and all of
**academy**: `grove` `sophists` `goldentongues` `stargazers`.

`data/domains.json` becomes **7** domains: the six faction domains `aristocracy` `guilds` `port`
`professions` `temples` `military` plus the faction-less `civic` (unchanged). `trade` and `academy`
are gone; `harbor`→`port`. Each faction domain keeps `cap: 300`, `drift: 0.0`, and a **rebuilt
relationships row** with one entry per faction domain (self = `Foe`, every other = `Neutral`); `civic`
keeps its empty relationships and authored cap 12.

Proposed blurbs/descriptions for the 5 new factions are in the decision log — **user-reviewable
flavor**; the build may transcribe them or the user may revise. No cross-references exist in the data
(verified: 0 relational traits / relationships), so cuts dangle nothing.

- Input: the current `data/factions.json` + `data/domains.json` + `../proposals/faction-resource-map.md`.
- Output: the 28-faction / 7-domain data files.

**Done when:**
- `data/factions.json` has exactly 28 factions; per-domain counts are aristocracy 4, guilds 9, port 4, military 3, professions 4, temples 4; no faction has `domain_primary` in {`trade`,`academy`,`harbor`}  `[automated]`
- None of the 18 removed ids appears in `data/factions.json`; the 5 new ids (`elaiades`,`the-builders`,`dockhands`,`merchant-houses`,`city-guard`) are present with valid functional traits/intensities  `[automated]`
- `data/domains.json` has exactly 7 domains {aristocracy,guilds,port,professions,temples,military,civic}; each faction domain's relationships row covers exactly the six faction-domain ids (self Foe, others Neutral); civic relationships `[]`, cap 12  `[automated]`
- Aristocracy Σ `int(rating)` == 9 (unchanged from the pre-split roster), so the harvest chain's raw is unchanged  `[automated]`
- `load_state_from_json("data")` loads cleanly; `_freeze_base_caps` yields a positive `base_cap` for every faction domain and leaves `civic`'s authored cap intact (the faction-less exception still holds)  `[automated]`

## Feature: Code, seed & docs consistency

The project catalog and the canonical/reference docs must match the new domain set, and the official
city must be re-seeded.

- `engine/projects/processing.py` `BASE_PROJECT_NAMES`: drop `trade`("Agora") and `academy`("Lyceum");
  rename the `harbor`("Docks") entry to `port`("Docks"). The dict's keys become the six faction
  domains + `civic`. (`BASE_PROJECT_DESCRIPTIONS` is empty — default is used — no change.)
- `reference/theming.md` (the canonical roster source): updated to the 28-faction / 7-domain roster —
  remove cut factions, add the 5 new ones, the Port section, the temples/Apollo absorption note.
- `reference/data-models.md`: the domain list updated to the 7 domains (it currently lists the 9).
- `db/seed.py` `seed_official_cities`: the official "Polis" city is **refreshed** to the new roster.
  It skips an already-seeded city by `city_name`, so the build removes/replaces the existing official
  "Polis" row at startup so it re-seeds — **non-destructively for user-created cities and saved runs**
  (only the official template row is refreshed).

- Input: the new data files; the existing catalog/seed/docs.
- Output: catalog, seed, and docs all consistent with the 28/7 roster.

**Done when:**
- `set(BASE_PROJECT_NAMES) == {aristocracy,guilds,port,professions,temples,military,civic}`; `base_project_name("port")` returns its name (e.g. "Docks"); no `trade`/`academy`/`harbor` key remains  `[automated]`
- No engine/api/db source file references the domain ids `"trade"`, `"academy"`, or `"harbor"` (only historical comments allowed)  `[automated]`
- After seeding into a fresh DB, the official "Polis" city has 28 factions and the 7 domain ids, and **no** legacy domain id (`trade`/`academy`/`harbor`) in its stored domains  `[automated]`
- `reference/data-models.md`'s domain list names exactly the 7 domains; `reference/theming.md` contains none of the 18 removed faction names and contains the 5 new ones  `[human-required]`

## Feature: Seed, saves & regression integrity

The migration applies to **new games**; existing saved snapshots are self-contained (they serialize
their own factions/domains) and restore **graceful-but-stale** on their old roster — no save migration.
The roster-count tests and any roster-coupled tests are brought into line, and nothing else regresses.

- Save policy: **new games only.** A new game (fresh seed) carries the 28/7 roster; an existing
  snapshot still `deserialize_state`s without error on its embedded (old) roster. (Same precedent as
  the faction-descriptions slice. This is an alpha/tech-demo — no migration tooling.)
- Tests to reconcile: `tests/test_theme_data.py` (`EXPECTED_DOMAIN_IDS`, `EXPECTED_FACTION_COUNTS`,
  `len==41`→28, the `BASE_PROJECT_NAMES` expectation, legacy-prefix checks); `tests/test_seed_official.py`
  (`EXPECTED_DOMAIN_IDS`, `len==41`→28, the legacy-domain-id guard); `tests/test_faction_descriptions.py`
  (`len==41`→28, and its blurb spot-check currently names `silverbench` — which is **cut** — so move it
  to a surviving faction). The **food** tests (`tests/test_needs_*.py`) reference `eumelidai`,
  `netmenders`, `ovenmen`, `winepressers` — all survive — and must stay green.

- Input: the migrated roster; the existing test suite.
- Output: a green suite on the new roster; old saves still loadable.

**Done when:**
- The shipped food chain + dynamics + redundancy tests (`tests/test_needs_chain.py`, `_dynamics.py`, `_cycle.py`, `test_toil.py`) pass unchanged in intent on the new roster — the three-source redundancy still holds  `[automated]`
- `test_theme_data.py` and `test_seed_official.py` pass against the 28/7 roster (their hardcoded domain set, counts, and legacy guards updated); `test_faction_descriptions.py` passes (count 28; the cut `silverbench` spot-check moved to a surviving faction)  `[automated]`
- A snapshot serialized from the *old* roster still `deserialize_state`s without error (graceful-but-stale) — proven with a fixture snapshot carrying a cut faction/domain id  `[automated]`
- The full suite is green  `[automated]`
- `py main.py --cycles 5` runs to completion on the new roster (28 factions, the Public summary line sane), and a freshly seeded game loads in the UI with the 7 domains and no legacy faction/domain visible  `[human-required]`

## Open Questions
- The 5 new factions' **names/blurbs** (in the decision log) are proposed flavor — the user should
  confirm or revise `elaiades`/`the-builders`/`dockhands`/`merchant-houses`/`city-guard` before or
  during the build (renaming is a trivial data edit). Not build-blocking.
- The military 3 keep evocative names (`shieldsworn` as the Army, `oarsworn` as the Fleet) rather than
  literal "The Army"/"The Fleet", for roster consistency — confirm that reading.
