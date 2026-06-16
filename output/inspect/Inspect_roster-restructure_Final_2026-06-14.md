# Inspection Report — Roster Restructure (Final sign-off)

- **Feature:** roster restructure — 41→28 factions, 9→7 domains
- **Spec:** Planning/specs/roster-restructure_spec.md (3 features)
- **Blueprint:** Planning/blueprints/roster-restructure_BP.md
- **Deviations:** output/deviations/Deviations_roster-restructure_2026-06-14.md
- **Date:** 2026-06-14
- **Verdict:** ✅ PASS (full suite 456 green; all automated Done-when verified; human-required prose verified by read; UI visual marked needs-human with headless/seed evidence)

---

## Results table

| Criterion | Status | Fidelity | Evidence |
|---|---|---|---|
| **F1** factions.json = 28; counts arist 4 / guilds 9 / port 4 / military 3 / professions 4 / temples 4; no domain_primary in {trade,academy,harbor} | ✅ PASS | High | `len=28`; `Counter({guilds:9, aristocracy:4, temples:4, port:4, professions:4, military:3})`; domain set has no legacy id |
| **F1** none of 18 cut ids present; 5 new ids present w/ valid functional traits | ✅ PASS | High | cut present: `[]`; new present: all 5; each new faction carries 2 traits in `FUNCTIONAL_TRAITS` (ambitious/conservative/industrious/opportunistic/defensive/aggressive), non-empty blurb+description |
| **F1** domains.json = 7 {aristocracy,guilds,port,professions,temples,military,civic}; each faction domain 6-entry relationships (self Foe, others Neutral); civic [] cap 12 | ✅ PASS | High | Read of domains.json: 6 faction domains each with 6 rows (own=Foe, others=Neutral), civic relationships `[]` cap 12 |
| **F1** Aristocracy Σ int(rating) == 9 (food conservation) | ✅ PASS | High | `arist_sum=9` (eumelidai 4 + pyrrhidai 3 + skiadai 1 + elaiades 1 = 9) |
| **F1** load_state_from_json loads cleanly; _freeze_base_caps positive base_cap per faction domain; civic keeps authored cap | ✅ PASS | High | 28 factions loaded; base_caps arist 11 / guilds 26 / port 16 / professions 12 / temples 13 / military 12 (all >0); civic base_cap=12 (authored) |
| **F2** set(BASE_PROJECT_NAMES) == 6 faction domains + civic; base_project_name("port")="Docks"; no trade/academy/harbor key | ✅ PASS | High | set match True; `port`→"Docks"; no legacy key |
| **F2** no engine/api/db (non-test) live reference to harbor/trade/academy | ✅ PASS | High | grep `engine api db --include=*.py`: only `db/seed.py:36 _STALE_DOMAIN_MARKERS = {"trade","academy","harbor"}` (intentional detection set for the refresh, not a live domain reference) |
| **F2** fresh-DB seed → official "Polis" has 28 factions, 7 domain ids, no legacy id | ✅ PASS | High | test_seed_official.py green; drove seed into in-memory DB → 28 factions, domains == {6 faction domains}∪{civic}, no legacy |
| **F2** data-models.md lists 7 domains; theming.md no cut factions as live entries, includes 5 new `[human-required]` | ✅ PASS | High | data-models.md L104 lists exactly the 7; theming.md: 5 new factions are live entries; cut factions appear only in the "Academy — dissolved" disposition note + prose, never as live roster entries |
| **F3** old-roster snapshot deserialize_states without error | ✅ PASS | High | test_roster_migration.py green — silverbench (cut) in `trade` (cut) round-trips through serialize→deserialize |
| **F3** food tests (needs_chain/_dynamics/_cycle, toil) pass; redundancy + harvest balance unchanged | ✅ PASS | High | all green; chain producers (eumelidai, netmenders, ovenmen, winepressers) all exist; harvest producer = domain:aristocracy ×2, Σ=9 ⇒ raw unchanged |
| **F3** full suite green (~456) | ✅ PASS | High | `456 passed in 1.73s` |
| **F3** headless run completes, 28 factions, sane Public `[human-required]` | ✅ PASS | High | `py main.py --cycles 5 --seed 3` → "Factions: 28", "THE PUBLIC: pop=21,224 fed=77 (Well fed) happy=52 (Content) health=100", no crash, no legacy id |
| **F3** UI: freshly seeded game shows 7 domains, no legacy faction `[human-required]` | 🟡 NEEDS-HUMAN | — | UI not driven in this headless inspect environment; evidence by proxy — fresh-DB seed yields 28 factions/7 domains/no legacy, and headless run renders 28 factions with no legacy id. See note below. |

**Per-feature pass counts:**
- Feature 1 (new roster data): 5/5 automated PASS
- Feature 2 (code/seed/docs): 3/3 automated PASS, 1/1 human-required PASS (prose read)
- Feature 3 (saves & regression): 4/4 automated PASS, 1 human-required split — headless PASS, UI visual needs-human (evidence by proxy)

---

## Fidelity judgments (the HARD three)

### (a) Food balance genuinely conserved — ✅ VERIFIED, not massaged
Independently confirmed aristocracy Σ int(rating) == 9 directly from factions.json
(eumelidai 4 + pyrrhidai 3 + skiadai 1 + elaiades 1 = 9; note elaiades rating is 1.5 but
`int(1.5)=1`, so the split is level-conserving as the spec intends). The harvest chain's
`harvest` producer is `{"domain": "aristocracy", "per_level": 2}` — raw = 2 × 9 = unchanged
from the pre-split roster. All four chain producer faction ids (eumelidai, netmenders, ovenmen,
winepressers) still exist in factions.json. The redundancy tests (TestRedundancy) pass with
their band assertions intact. Conservation is real.

### (b) Legibility test reframe — ✅ LEGITIMATE ADAPTATION (not a masking weakening)
The builder changed TestLegibilityAndRecovery from *pin estates to 1.0* to *remove the
aristocracy (cycles 10–19) then restore (cycle 20)*. I re-derived both scenarios on the live
data (seed 202):
- **Pin-to-1.0 no longer drops a band:** with the 4th estate (elaiades) raising the floor (4
  estates × min level 1), pinning all estates to rating 1.0 keeps fed at band 2 — the old
  shortage is genuinely cushioned. (min band cycles 10–15 = 2, start band = 2 ⇒ no drop.)
- **The new removal shortage is real and legible:** removing the aristocracy drops fed to band
  1 within 5 cycles (visible) and recovers to band 2 within the 20–35 window (recoverable).
The property under test (visible ≤5, recover ≤15) is unchanged; the shortage was made *more
severe to stay real*, not the assertion loosened. The cause is a genuine regime shift from the
Skiadai split, and the pin-cushioning behaviour is still independently exercised by
TestRedundancy (which removes producer factions). Same category as the prior fish/flocks
legibility repairs. Not a regression mask.

### (c) Seed refresh non-destructive — ✅ VERIFIED
Read `db/seed.py`: `seed_official_cities` queries with `is_official=True` (L50-52), so
user-created cities are never even fetched. `_is_stale` checks stored domains against
`_STALE_DOMAIN_MARKERS`; a current official template is skipped, a stale one is **updated in
place** (L70-74, keeps its id — FK-safe), never deleted. Drove it: planted a stale official
"Polis" (old roster) and a user city "MyTown" (is_official=False, carrying legacy
harbor/trade/silverbench). After seed: official refreshed to 28 factions / `port` not `harbor`;
**user city byte-identical, untouched** (still has silverbench + harbor). Non-destructive
confirmed.

---

## Deviations (reviewed — all sound)
- Steps 1–2: data files rewritten via one-off Python transform — same result, deterministic. OK.
- Steps 5–7: two extra test-fixture id swaps (test_audience_terms.py, test_domain_base_project_name.py)
  broke when trade/harbor left BASE_PROJECT_NAMES — mechanical swaps. Harmless synthetic dead-id
  labels left in test_actions/test_city_load_cap_freeze/test_events_system (outside the no-dead-id
  Done-when, which is engine/api/db only). OK.
- Step 7 food coupling: ARISTOCRACY tuple gained elaiades; legibility test reframed — judged
  legitimate above (b).
- Step 8: in-place refresh of stale official template — judged non-destructive above (c).
- Final Step 1: graceful-save test placed in new tests/test_roster_migration.py. OK.

## Minor observations (non-blocking, not failures)
- theming.md L266-267 prose ("Guilds *make* goods; Trade sells them, Harbor ships them") and the
  Port section header at L238 still carry stale *prose* referencing the old trade/harbor domain
  split. These are descriptive flavor lines, not live faction/domain entries, so they do not
  violate the Done-when (which requires only: no cut faction as a live entry, 5 new present). Worth
  a tidy-up pass on the reference doc, but not a sign-off blocker.
- The new Elaiades leader is named "Theron of the Grove" — "the Grove" is a cut academy faction
  name reused as cosmetic leader flavor. Purely a name string, not a data/id reference; the
  recorded flavor note already invites the user to revise the 5 new factions' names.

## Human sign-off required
- **UI visual** (Feature 3, F3 final `[human-required]`): a freshly seeded game loading in the Vue
  UI showing the 7 domains and no legacy faction/domain. Not driven here — this inspect ran
  headless with no browser/server session. **Evidence by proxy is strong:** the fresh-DB seed
  produces exactly 28 factions / 7 domains / no legacy id (test_seed_official.py + driven seed),
  and `py main.py --cycles 5` renders 28 factions with no legacy id. A human should confirm the
  rendered UI once (server + new game) to close this item.

## Failures
None.
