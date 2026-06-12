# Blueprint: Public Needs (The Barley Run)
Spec: Planning/specs/public-needs_spec.md
Date: 2026-06-12

Cross-spec contracts: actions_spec (Toil) · faction-behavior_spec (weights) · cycle-runner_spec
(item 5b + `toiling`) · events_spec (Public-need gates) · audience_spec (Toil term + needs line)
· special-factions_spec (ThePublic fields).

**Wiring fact the spec assumes but the code lacks:** live paths (`main.py`, `api/routes/sim.py`)
currently call `run_cycle` with **no `public=` and no event deck** — The Public exists only in
tests. Slice 5 fixes both plumbing gaps.

---

## Builder instructions
- Execute steps in order. Do not skip, reorder, or read ahead into the next slice.
- Check off each step when complete: [ ] → [x]
- One step = one logical concern. If a step can't be tested on its own, it's too small — merge it. If it touches more than one concern, split it.
- Deviation: if you do something differently than the step says, note it inline and keep going.
- Stuck: stop immediately. Do not try alternative approaches. Report exactly where and why.
- All test commands run from `backend/`: `py -m pytest tests/<file> -q`.

---

## Slice 1: ThePublic state + word bands
**Scope:** ThePublic carries population/fed/happy; band lookups and the needs line exist as pure functions; everything round-trips.

### Step 1: Extend ThePublic
**Build:** In `engine/models.py`, add to `class ThePublic`: `population: int = 20000`, `fed: int = 60`, `happy: int = 50` (after `health`). Add field `toiling: bool = False` to `class Faction` with comment `# cycle-only: set by Toil resolution, consumed by needs step, reset in end_of_cycle — never persisted`. Slice 5 wires the reset; do not wire it here.
**Test:** `py -m pytest tests/ -q` (no regressions; fields default correctly via a quick `python -c` check).
**Done When:** `ThePublic().population == 20000`, `.fed == 60`, `.happy == 50`; `Faction` accepts the flag defaulting False; suite green.
**Stuck If:** ThePublic is constructed positionally somewhere and new fields break it.
- [x] Complete

### Step 2: Band tables module
**Build:** New package `engine/needs/` (`__init__.py` re-exporting the public names). Create `engine/needs/bands.py`: `FED_BANDS` and `HAPPY_BANDS` as ordered `(upper_bound, word)` tables exactly per spec (0–20 Starving/Miserable, 21–45 Hungry/Sullen, 46–75 Fed/Content, 76–100 Well fed/Festive); functions `fed_band(value: int) -> str`, `happy_band(value: int) -> str`, `band_index(word, table) -> int` (for ≤/≥ gate comparisons — slice 6 uses this, keep it table-generic); `SICKLY_THRESHOLD = 40`; `is_sickly(health) -> bool`; `needs_line(public, drunk: bool) -> str` producing `"The people are {fed band}{, drunk}{, sickly}, and {happy band}."`
**Test:** Write `tests/test_needs_bands.py`: boundary cases 20/21/45/46/75/76 for both tables (spec Done-when); sickly at 39/40; needs_line with and without flags. Run it.
**Done When:** All boundary assertions pass exactly as the spec table states.
**Stuck If:** —
- [x] Complete

### Step 3: Serialization round-trip
**Build:** In `serializer.py`, add `serialize_the_public(public) -> dict` and `deserialize_the_public(data: dict) -> ThePublic` (pattern-match the existing entity serializers). Include `support`, `disposition`, `traits`, `health`, `population`, `fed`, `happy`. Absent keys on deserialize → field defaults (existing saves load). Do **not** serialize `Faction.toiling`. Extend `serialize_state(...)` with optional `public=None` kwarg → key `"the_public"` when provided; extend its deserialize counterpart symmetrically. Forward constraint: slice 5 passes `public` through `_save_cycle` and session restore — keep the kwarg optional so existing callers stay valid.
**Test:** Add round-trip + missing-fields-default cases to `tests/test_needs_bands.py` (or `tests/test_serializer.py` if one exists). Run full suite.
**Done When:** Round-trip preserves all seven fields; `deserialize_the_public({})` equals defaults; suite green (spec round-trip Done-when).
**Stuck If:** No deserialize counterpart of `serialize_state` exists — report how restore actually rebuilds state instead of improvising.
- [x] Complete
**Deviation:** `deserialize_state` returns an 8-tuple now (public appended); its four unpack sites (sim.py ×2, test_base_stack_serde.py ×2) updated mechanically. Serialization tests live in `test_needs_bands.py` alongside the band tests rather than a separate file.

---
End of Slice 1. Builder checkpoint: tests green → continue to Slice 2.

---

## Slice 2: The harvest chain (pure math)
**Scope:** A pure function turns live faction state + population into supply targets; chains defined in data.

### Step 1: Chain definition data
**Build:** Create `data/chains.json`:
```json
[
  {
    "id": "harvest",
    "producers": {"domain": "aristocracy", "per_level": 3},
    "processors": [
      {"faction_id": "ovenmen",      "per_level_capacity": 6, "fed_per_unit": 1.0,  "happy_per_unit": 0.0, "label": "bread"},
      {"faction_id": "winepressers", "per_level_capacity": 6, "fed_per_unit": 0.15, "happy_per_unit": 0.6, "label": "wine"}
    ],
    "unprocessed": {"fed_per_unit": 0.4, "label": "porridge"}
  }
]
```
Add `load_chains(data_dir="data") -> list[dict]` to `loaders.py` (pattern-match existing loaders; missing file → `[]`).
**Test:** Quick load assertion appended to `tests/test_needs_chain.py` (created next step) — fine to write file now, test next step.
**Done When:** File parses; loader returns one chain.
**Stuck If:** —
- [x] Complete

### Step 2: Chain computation
**Build:** Create `engine/needs/chain.py`. Constants at module top (tests must import these, never copy values): `TOIL_MULT = 1.5`, `PARITY_TARGET = 75`, `BASE_HAPPY = 30`, `DRUNK_THRESHOLD = 0.25`, `POP_PER_SUPPLY_UNIT = 1000`. Dataclass `ChainOutput`: `fed_target: float`, `happy_target: float`, `drunk: bool`, `raw: float`, `units: dict[str, float]` (label → units processed, including `"porridge"`). Function `compute_chain(factions: Dict[str, Faction], population: int, chains: list[dict]) -> ChainOutput`, **pure — no mutation**:
1. `raw = Σ per_level × faction.floor_rating` over factions whose `domain_primary` matches producers' domain, ×`TOIL_MULT` per toiling producer.
2. Capacity per processor = `per_level_capacity × level`, ×`TOIL_MULT` if toiling. If `Σ capacity ≥ raw`: split raw proportional to capacity. Else: each processes its capacity; remainder → porridge.
3. `fed_supply = Σ units × fed_per_unit` (+ porridge), `happy_supply = Σ units × happy_per_unit`.
4. `demand = population / POP_PER_SUPPLY_UNIT`; `fed_target = min(100, PARITY_TARGET × fed_supply / demand)`; `happy_target = clamp(BASE_HAPPY + PARITY_TARGET × happy_supply / demand, 0, 100)`; `drunk = (wine happy contribution / demand) >= DRUNK_THRESHOLD`. Guard `demand == 0` → targets 100, drunk False.
**Test:** Write `tests/test_needs_chain.py`: purity (same input twice → identical, no faction mutated); raw = Σ3×level over aristocracy; dead-estates fixture (aristocracy ratings → produce 0 raw → all units 0); over/under capacity splits; conservation `Σ units == raw` exactly; porridge-floor fixture (drop both processors from the chain def → fed_supply == 0.4 × raw ≠ 0); toiling producer ×1.5 and toiling processor ×1.5.
**Done When:** Every spec Done-when under "The harvest chain" has a passing named test.
**Stuck If:** `floor_rating` isn't the level property name in `models.py` (verify, use the real one).
- [x] Complete
**Deviation:** Used `Faction.level` (alias of `floor_rating`) for readability — same property.

---
End of Slice 2. Builder checkpoint: tests green → continue to Slice 3.

---

## Slice 3: Drift, shortage, plenty
**Scope:** Targets become trait movement, health/support deltas, and population change.

### Step 1: Drift + effects function
**Build:** Create `engine/needs/drift.py`. Constants: `DRIFT_STEP = 10`, `HEALTH_DELTAS = {"Starving": -4, "Hungry": -2, "Well fed": +2}`, `SUPPORT_DELTAS = {"Starving": -5, "Hungry": -2, "Well fed": +2, "Miserable": -2, "Festive": +2}`, `POP_GROWTH = 0.02`, `POP_MIN = 1000`. Function `apply_needs(public: ThePublic, out: ChainOutput, mayor=None) -> list[ActionResult]`:
1. Drift `fed` then `happy` toward their targets by ≤ `DRIFT_STEP` (land exactly on target, no overshoot; round to int).
2. Health delta from the **new** fed band, clamp 0–100.
3. Support delta from new fed band + new happy band; apply the same way existing code couples `public.support` and `mayor.reputation["the_public"]` (read `engine/special/public.py` first and mirror it — they are documented as the same value).
4. Population: Well fed AND `health ≥ 70` → `round(population × 1.02)`; Starving OR `health < 30` → `round(population × 0.98)`; floor `POP_MIN`.
Return `ActionResult` entries for the cycle log (actor `"the_public"`; narrative only when a band changed or population moved — keep log noise low).
**Test:** Write `tests/test_needs_drift.py`: drift 30-below rises exactly 10; ≤10 away lands on target; each band's health/support delta; pop +2%/−2%/floor; the demand-scales case (pop 20k→40k with same factions halves `fed_target` via `compute_chain`).
**Done When:** Every spec Done-when under "Drift, shortage, and plenty" except the drunk-city fixture has a passing test.
**Stuck If:** Support coupling in `public.py` contradicts the spec's single-value claim.
- [x] Complete
**Deviation:** Support deltas route through `mayor.adjust_reputation("the_public", …)` when a mayor exists (that value is source of truth; `public.support` syncs from it in `process_the_public`); direct `public.support` adjustment only mayorless — matches the existing coupling.

### Step 2: Drunk-city fixture
**Build:** In `tests/test_needs_drift.py`, add the drunk-city scenario per spec: balanced baseline city (real `data/factions.json` ratings via loaders) vs. swapped city (winepressers rating 4.0, ovenmen 1.0); iterate `compute_chain` + `apply_needs` 10 cycles each; assert swapped run ends with `happy` above and `fed` below baseline run.
**Test:** Run the file.
**Done When:** Fixture passes deterministically (no RNG in chain/drift — there should be none).
**Stuck If:** Chain/drift turn out to need RNG (they must not — report).
- [x] Complete

---
End of Slice 3. Builder checkpoint: tests green → continue to Slice 4.

---

## Slice 4: Toil
**Scope:** The sixth faction action exists: resolvable, NPC-selectable under shortage, committable in deals.

### Step 1: Chain-role helper + resolver
**Build:** In `engine/needs/chain.py`, add `chain_role_faction_ids(chains, factions) -> set[str]` (producer-domain members + processor faction_ids). In `engine/actions/faction.py`, add `resolve_toil(faction: Faction) -> ActionResult` (pattern-match `resolve_protect`): set `faction.toiling = True`; ActionResult action `"Toil"`, no rank/health change, narrative like `"{faction.name} bend to their trade."` Wire dispatch where the other resolvers dispatch (`engine/cycle/resolution.py` — find the action→resolver mapping and add `"Toil"`).
**Test:** Write `tests/test_toil.py`: resolve sets flag, rank and health unchanged.
**Done When:** Toil resolves; suite green.
**Stuck If:** Resolution dispatch is structured so an untargeted action can't be added without touching >2 functions — report the shape first.
- [x] Complete

### Step 2: NPC weights + gating
**Build:** In `engine/npc/behavior.py`: add `"Toil": 10` to `BASE_WEIGHTS`; after weights are built, **zero** the Toil weight for factions not in `chain_role_faction_ids` (load chains once at module import or accept via param — match how the module gets other data; keep it overridable for tests). Add state modifier: Public fed band ≤ Hungry AND faction has chain role → Toil +25 — `select_faction_action` must therefore receive the public (or its fed band) — extend its signature with optional `public=None`, defaulting to no modifier when absent (forward constraint: runner passes it in Slice 5; existing call sites stay valid). Add `Toil +10` to the `industrious` trait row wherever trait modifiers live (check `engine/npc/weights.py` vs `behavior.py`).
**Test:** In `tests/test_toil.py`: non-chain faction never selects Toil over many draws (weight is exactly 0 in the built weight dict — assert on the dict, not sampling); chain faction's Toil weight is 10 base and 35 when a Hungry public is passed; industrious adds +10.
**Done When:** Weight assertions pass; suite green.
**Stuck If:** Trait table and state modifiers live in conflicting modules.
- [x] Complete
**Deviation:** `select_faction_action` gains `public=None, chain_roles=None` (precomputed id set) rather than loading chains itself — engine stays IO-free; runner passes both in slice 5. Weight-dict assertions capture the dict by monkeypatching `weighted_choice` instead of refactoring a seam into the selector.

### Step 3: Committable Toil
**Build:** `faction.committed_action == "Toil"` must force a Toil plan — verify the existing committed-action path in `behavior.py` (line ~87) handles an arbitrary action name; add `"Toil"` to whatever validation/whitelist exists there and in the deal machinery (`grep committed_action` across `engine/llm/` and `engine/mayor/`).
**Test:** In `tests/test_toil.py`: a faction with `committed_action="Toil"` returns a Toil plan from `select_faction_action`.
**Done When:** Forced-Toil test passes (spec actions Done-when 3).
**Stuck If:** Committed actions are whitelisted in >3 places — list them, update all, note as deviation.
- [x] Complete
**Deviation:** Engine-side committed path has no whitelist (generic fall-through — works for Toil as-is). The only whitelist is `VALID_FACTION_ACTIONS` in `response_parser.py` (LLM-side), updated in Slice 6 Step 3 where the blueprint already addresses it.

---
End of Slice 4. Builder checkpoint: tests green → continue to Slice 5.

---

## Slice 5: Cycle integration + live plumbing [inspect]
**Scope:** The needs step runs in every real cycle (headless and API), `toiling` resets, public state persists in snapshots.

### Step 1: The needs step in the runner
**Build:** In `engine/cycle/runner.py`, after the `tick_deals` block and **before** `process_active_events` (orchestration item 5b per cycle-runner_spec), insert: if `public is not None` — `out = compute_chain(factions, public.population, chains)`; `all_results.extend(apply_needs(public, out, mayor=mayor))`; stash `out` + band words on the runner's locals for the event roll (next step). Pass `public=public` into `select_faction_action`'s call site in `cycle/resolution.py` (`run_sequential_actions` needs a `public=None` passthrough param). `chains`: new optional `run_cycle` kwarg `chains: Optional[list]=None`, defaulting to `loaders.load_chains()` result passed by callers — do NOT file-read inside the engine (engine stays IO-free; loaders own files).
**Test:** Write `tests/test_needs_cycle.py`: `run_cycle(world, factions, domains, mayor=mayor, treasury=treasury, public=public, chains=chains)` mutates `public.fed` toward the chain target; without `public=` nothing breaks.
**Done When:** Needs step runs inside `run_cycle`; suite green.
**Stuck If:** Import cycle between `cycle/runner.py` and `engine/needs/` (restructure imports, note deviation).
- [x] Complete
**Deviation:** `chains` defaults to `[]` inside `run_cycle` (no implicit loader call — engine stays IO-free); `chain_roles` computed once per cycle and passed to the action loop alongside `public`.

### Step 2: Reset toiling in end-of-cycle
**Build:** In `engine/cycle/end_of_cycle.py` (`run_end_of_cycle` — wait: needs step runs AFTER `run_end_of_cycle`, so reset must happen later). Correct placement: reset `faction.toiling = False` for all factions at the very end of `run_cycle` (just before building `CycleResult`), matching cycle-runner_spec's "Step 4 (after the Public-needs step consumes it)". Add a comment naming the spec.
**Test:** In `tests/test_needs_cycle.py`: force a Toil via `committed_action`, run a cycle, assert every faction's `toiling` is False after `run_cycle` returns, and that the chain saw the boost (fed target higher than a no-Toil control run with same seed).
**Done When:** Reset test passes (spec cycle Done-when 3).
**Stuck If:** —
- [x] Complete
**Deviation:** Reset placed at the very end of `run_cycle` (before `CycleResult` build) as the step itself corrected — not in `end_of_cycle.py`, which runs before the needs step.

### Step 3: Load + plumb The Public everywhere
**Build:** (a) `loaders.py`: `load_the_public(data_dir="data") -> ThePublic` reading `world_state.json` key `special_factions.the_public` (missing → defaults). Add that block to `data/world_state.json` with `support 0, health 100, population 20000, fed 60, happy 50`. (b) `main.py`: construct via loader, pass `public=public, chains=load_chains()` to `run_cycle`; add public summary line to `print_summary`. (c) `api/sessions.py`: `SimSession` gains `public: ThePublic = None` (post_init → `ThePublic()` if None... use loader defaults instead: leave None handling to restore). (d) `api/routes/sim.py`: `_restore_session` builds `public` (from snapshot `the_public` key if present, else `load_the_public()`); both `run_cycle` call sites pass `public=session.public, chains=...` (load chains once at module level); `_save_cycle` passes `public` into `serialize_state`.
**Test:** Extend `tests/test_needs_cycle.py` with a serialize→restore round-trip through `serialize_state`; run full suite; run `py main.py --cycles 5` and confirm it completes with a public summary line.
**Done When:** Headless run shows the Public; suite green.
**Stuck If:** Session restore path has no hook for extra state (report the actual restore shape).
- [x] Complete
**Deviation:** `start_sim` builds the public via `load_the_public()` engine defaults rather than the city template (city rows don't carry a `the_public` block yet — city-generation's problem later). Chains loaded once at module level in `sim.py` (`_CHAINS`).

---
⛔ End of Slice 5 [inspect]. Run **inspector** on this slice before continuing.

---

## Slice 6: Event gates + audience surface
**Scope:** Need bands gate the event deck (with a live deck shipped); audiences see the needs line and can buy Toil.

### Step 1: Band gates in the event system
**Build:** In `engine/events/event_system.py`, extend `_matches_trigger` (and thread the public through `roll_for_random_events(world, factions, domains, event_deck, public=None)`): keys `max_fed_band`, `min_fed_band`, `max_happy_band`, `min_happy_band` (compare via `band_index` from `engine/needs/bands.py`), `sickly: true` (`is_sickly(public.health)`). `public is None` → any template carrying a need gate is ineligible. Update the runner's `roll_for_random_events` call to pass `public`.
**Test:** Write `tests/test_needs_event_gates.py`: sentinel no-effect templates, one per fed band + one sickly + one min/max happy, injected as the deck; assert eligibility flips exactly at the band boundaries by setting `public.fed/happy/health` directly (spec sentinel Done-when), and that a Starving-gated template is eligible the same cycle `run_cycle` starves the city (engineer with a tiny population... high demand via large population, zero aristocracy — assert via the deck roll with chance forced/mocked to 100%).
**Done When:** Gate tests pass independently per key; same-cycle test passes (spec cycle Done-whens 1–2).
**Stuck If:** `roll_for_random_events` selection can't be made deterministic for the test without monkeypatching more than the chance roll.
- [ ] Complete

### Step 2: Ship the v1 deck
**Build:** Create `data/events.json` with two entries per events_spec: `bread_riot` (random; `trigger_conditions: {"max_fed_band": "Starving"}`; effects: The Public support −5 one-time, chaos +1 in `civic` or the most food-relevant domain — match `EventEffect` fields as implemented; duration 2) and `plague_outbreak` (gate `{"sickly": true}`; effects per the existing example in events_spec: professions health −3/cycle, Public health −5/cycle, duration 4). Add `load_event_deck(data_dir="data")` to `loaders.py` (missing file → `[]`). Wire: `main.py` and both `sim.py` call sites pass `event_deck=load_event_deck(), active_events=session/local list`; `SimSession` gains `active_events: list = None` (post_init `[]`). Note: active events are NOT persisted in snapshots — known v1 gap, log a deviation note here in the blueprint.
**Test:** Deck loads; full suite; `py main.py --cycles 30` completes (riots may or may not fire — no assertion on randomness here).
**Done When:** Deck file loads and live paths feed it; suite green.
**Stuck If:** `EventEffect`/template instantiation rejects the support/chaos effect fields — check `_instantiate_event` for the real template schema and conform; deviation-note any field-name differences from events_spec examples.
- [ ] Complete

### Step 3: Audience prompt + parser
**Build:** In `engine/llm/prompt_builder.py`: add the needs line (`needs_line(...)` from `engine/needs/bands.py`) to the system prompt's city-state section — the builder must receive the public; follow how `world`/faction state currently reach the prompt builder and thread `public` the same way (likely via the audience entry in `engine/llm/audiences.py` and its API route — `grep` the call chain first). Add `Toil` to the committable-action term list **only when the audience faction has a chain role** (use `chain_role_faction_ids`), with a plain "what it does" line per audience_spec. In `engine/llm/response_parser.py`: treat `Toil` like `Grow`/`Protect` — valid `committed_action`, `target_id` cleared.
**Test:** Extend `tests/test_audience_terms.py` (it exists): prompt for `ovenmen` lists Toil; prompt for a non-chain faction (e.g. `tidesworn`) does not; prompt contains the needs line with current band words; parser clears `target_id` on Toil. Run full suite.
**Done When:** All four audience Done-when additions pass (audience_spec v5.1).
**Stuck If:** The prompt builder has no access path for `public` without widening >2 signatures — report the chain before widening.
- [ ] Complete

---
End of Slice 6. Builder checkpoint: tests green → continue to Final Slice.

---

## Final Slice: UI surface + dynamics + full verification
**Scope:** The needs are visible in the game UI; the loop's dynamics hold over long runs; every spec Done-when verified.

### Step 1: Expose public in the state API
**Build:** `api/routes/state.py` `get_state`: pass `public=session.public` into `serialize_state` so the payload carries `the_public` (with band words + drunk/sickly added by `serialize_the_public` — extend it with derived keys `fed_band`, `happy_band`, `sickly`; `drunk` needs the last chain output — store `public.last_drunk: bool = False` set by `apply_needs`... simplest: add field `drunk: bool = False` to `ThePublic`, set in `apply_needs` from `ChainOutput.drunk`, serialized like the rest. Note this as a deviation on the spec's "drunk is not stored" — it is *derived then cached for display*, never drifted; record in the deviation note).
**Test:** Suite + manual: start server, `GET /state` shows `the_public` with band words.
**Done When:** Payload carries the needs.
**Stuck If:** —
- [ ] Complete

### Step 2: Show the needs in the UI
**Build:** `frontend/src/views/GameView.vue` (Options API, match existing style/`store.js` data flow): add a compact "The People" panel — population (formatted, e.g. `20,400`), the needs sentence from `fed_band`/`drunk`/`sickly`/`happy_band`, and health. Use existing panel/card classes from `style.css` — no new design system. Rebuild: `cd frontend && npm run build`.
**Test:** Server up, play 3–5 cycles in the browser; needs panel renders and updates.
**Done When:** Panel visible and live — screenshot captured for the `[human-required]` item (playwright per root CLAUDE.md).
**Stuck If:** GameView's layout has no sane slot for another panel — pick the sidebar and deviation-note it.
- [ ] Complete

### Step 3: Dynamics suite
**Build:** Write `tests/test_needs_dynamics.py` (mark `@pytest.mark.slow` if a marker convention exists; otherwise plain). Fixed seeds (`random.seed`). Four tests against the standard city loaded via loaders, mayorless where possible, importing all constants:
1. *Stability*: 60 cycles untouched → fed band ≥ Hungry in ≥ 50 of 60 cycles.
2. *Legibility*: at cycle 10 halve all aristocracy ratings (min 1.0) → fed band drops ≥ 1 step within 5 cycles.
3. *Recoverability*: restore the ratings at cycle 20 → fed back to the original band within 15 cycles.
4. *Toil matters*: same shortage with `committed_action="Toil"` re-applied each cycle on ovenmen+winepressers → min(fed) strictly higher than the no-Toil run, same seed.
**Test:** Run the file; if a dynamics test fails, **tune the constants in `engine/needs/chain.py`/`drift.py`** (they are provisional by spec) until all four pass without breaking unit tests — record each constant change as a deviation note.
**Done When:** All four dynamics tests pass with the committed constants; full suite green.
**Stuck If:** No constant tuning satisfies stability + legibility simultaneously (a real design conflict — stop and report the trade-off data).
- [ ] Complete

### Final Step: Verify spec Done when items
**Build:** No new code. Confirm all spec `**Done when:**` items are met — `public-needs_spec.md` (all four features), plus the additions in actions/faction-behavior/cycle-runner/events/audience/special-factions specs.
**Test:** Run the full test suite — every `[automated]` item now has a committed test from an earlier step. Capture output. Drive the software directly only for an item that genuinely can't be unit-tested. The UI `[human-required]` item: screenshot evidence from Final Step 2.
**Done When:** Every `[automated]` criterion passes (via its committed test). Every `[human-required]` criterion has captured evidence.
**Stuck If:** An automated criterion fails and the cause is not clear from the output.
- [ ] Complete

---
⛔ Final slice complete. Run **inspector** for final sign-off.
