# Blueprint: Public Needs — flocks slice
Spec: Planning/specs/public-needs_spec.md (v3 — Feature: The pastoral chain)
Date: 2026-06-14

> Increment on the shipped public-needs build. The original `public-needs_BP.md` (barley) and
> `public-needs-fish_BP.md` (fish) are closed, inspector-signed records — left untouched. This
> blueprint covers only the flocks slice.
>
> **Engine confirmed: NO chain.py change required.** The fish slice already generalized
> `compute_chain` to `faction_id` producers and made the unprocessed label come from data.
> Flocks is the identical shape (faction-keyed, processor-less, label `"meat"`). This slice is
> **data + tests only.** If the builder finds an engine gap, that is a Stuck — report it.
>
> "Constants" (`FLOCKS_PER_LEVEL`, `MEAT_FED_PER_UNIT`) live in `data/chains.json` as data — tests
> read them from the loaded chain def, never hardcode.

---

## Builder instructions
- Execute steps in order. Do not skip, reorder, or read ahead into the next slice.
- Check off each step when complete: [ ] → [x]
- One step = one logical concern. If a step can't be tested on its own, it's too small — merge it. If it touches more than one concern, split it.
- Deviation: if you do something differently than the step says, note it inline and keep going.
- Stuck: stop immediately. Do not try alternative approaches. Report exactly where and why.
- All test commands run from `backend/`: `py -m pytest tests/<file> -q`.

---

## Slice 1: The pastoral chain (data + unit tests)
**Scope:** `compute_chain` produces meat from the Eumelidai (a third faction-keyed processor-less
producer feeding `fed` directly), additively — barley and fish are byte-for-byte unchanged — and
the chain unit tests prove it in isolation.

### Step 1: Add the pastoral chain
**Build:** In `data/chains.json`, add a third chain object **after** the existing `harvest` and
`fishery` entries, leaving those two **byte-for-byte unchanged** (additive, no re-tune):
```json
{
  "id": "pastoral",
  "producers": {"faction_id": "eumelidai", "per_level": 1},
  "processors": [],
  "unprocessed": {"fed_per_unit": 1.0, "label": "meat"}
}
```
(Eumelidai already exists in `data/factions.json` — aristocracy, rating 4.0. It is a *mixed*
estate: it stays in the harvest chain's `domain: aristocracy` pool **and** produces flocks here.
No roster change. Provisional constants `per_level 1`, `fed_per_unit 1.0`.)
**Test:** `py -c "from loaders import load_chains; c=load_chains(); print([x['id'] for x in c]); print(c[2]['producers'], c[2]['unprocessed'])"` from `backend/`.
**Done When:** `load_chains()` returns 3 chains `['harvest','fishery','pastoral']`; pastoral has a `faction_id` producer (eumelidai), no processors, and a `meat` unprocessed label.
**Stuck If:** The JSON fails to parse.
- [x] Complete

### Step 2: Pastoral unit tests
**Build:** In `tests/test_needs_chain.py`, read the pastoral constants from the loaded def
(`PASTORAL = next(c for c in CHAINS if c["id"] == "pastoral")`, `EPL = PASTORAL["producers"]["per_level"]`,
`MEAT_FPU = PASTORAL["unprocessed"]["fed_per_unit"]`) and add a `TestPastoral` class with a
`mk_flock_city(eumelidai=4.0, with_other_aristocracy=False)` helper (Eumelidai at `domain="aristocracy"`):
(a) faction-keyed producer sums **only** the Eumelidai — add another aristocracy faction and confirm
it adds no flocks via the *pastoral* chain (note: the other aristocracy faction WILL feed the harvest
chain — isolate by asserting `units["meat"] == EPL × 4`, the Eumelidai-only meat); (b) processor-less
routing — `units["meat"] == EPL × eumelidai.level` and `fed_supply` rises by `meat × MEAT_FPU`
(verify via `fed_target` against a Eumelidai-only city); (c) zero Eumelidai (absent) → zero meat;
(d) toiling Eumelidai → `× TOIL_MULT` meat; (e) `eumelidai` is in `chain_role_faction_ids`;
(f) per-chain conservation — for a Eumelidai-only city `units["meat"] == out.raw`.
Also add an **additive-guard** test: assert `HARVEST["producers"]["per_level"] == 2` and
`FISHERY["producers"]["per_level"] == 3` and `FISHERY["unprocessed"]["fed_per_unit"] == 1.0`
(the fish-slice values — proves no re-tune of barley/fish).
**Test:** `py -m pytest tests/test_needs_chain.py tests/test_toil.py -q`.
**Done When:** All pastoral cases + the additive-guard pass; existing chain/Toil tests still green
(the standard `mk_city` has no Eumelidai, so its harvest tests are unaffected).
**Stuck If:** A pastoral expected value disagrees with `compute_chain` and the cause isn't a stale
literal — report. Or the engine doesn't already handle the faction-keyed `meat` chain (would mean
the fish-slice generalization is incomplete — report, do not patch the engine here).
- [x] Complete
**Deviation:** Pastoral math tested with the pastoral chain in **isolation** (`compute_chain(city, pop, [PASTORAL])`)
rather than the full `CHAINS`, because the Eumelidai also feed the harvest chain (mixed estate),
which would add porridge noise — isolation keeps `meat == raw` clean. Same assertions, cleaner
fixture. Also renamed the shipped `TestLoader.test_loads_two_chains` → `test_loads_three_chains`
(the chain-count assertion moved 2→3). Engine confirmed unchanged — no `chain.py` edit (the
fish-slice generalization already covers flocks).

---
End of Slice 1. Builder checkpoint: `test_needs_chain.py` + `test_toil.py` green.
**Note:** adding the pastoral chain shifts the *dynamics* (the real loaded city — which HAS the
Eumelidai — is now better-fed), so `tests/test_needs_dynamics.py` will go transiently red here. That
is expected and repaired in the Final Slice (same cross-slice sequence as the fish slice). Do not
treat the dynamics red as a Slice 1 failure.

---

## Final Slice: Three-source redundancy + verification [inspect]
**Scope:** The three-source redundancy property holds, the shipped dynamics still pass under three
sources, and every v3 spec Done-when is verified.

### Step 1: Update the redundancy test to three sources
**Build:** In `tests/test_needs_dynamics.py`, update `TestRedundancy` (currently two-source) to the
three-source property, using the standard loaded city (fixed seed; remove sources by `factions.pop`):
- all three running → `min(band_i(v) for v in fed[-10:]) >= band_index("Fed", FED_BANDS)`;
- remove the Netmenders (fish, ~30%) → city stays **Fed**: `band_i(fed[-1]) >= band_index("Fed", FED_BANDS)`
  (the resilience gain — a smaller-source loss is absorbed);
- remove the `ARISTOCRACY` factions (drops barley **and** flocks — the Eumelidai produce both) →
  fed never Starving and settles **Hungry**: `all(band_i(v) >= band_index("Hungry", FED_BANDS) for v in fed)`
  and `band_i(fed[-1]) == band_index("Hungry", FED_BANDS)`;
- remove `ARISTOCRACY + ("netmenders",)` (all food) → `band_i(fed[-1]) == band_index("Starving", FED_BANDS)`.
**Test:** `py -m pytest tests/test_needs_dynamics.py::TestRedundancy -q`.
**Done When:** All four three-source scenarios pass. If they don't, tune the provisional pastoral
constants in `data/chains.json` (`pastoral.per_level`, `pastoral.unprocessed.fed_per_unit`) — and
ONLY those (barley/fish stay fixed, the additive guard protects them) — until the bands hold; record
each change as a deviation.
**Stuck If:** No pastoral constant set gives "all three → Fed+" **and** "remove aristocracy → Hungry
not Starving" **and** "remove all → Starving" together — report the trade-off data.
- [x] Complete

### Step 2: Re-verify the shipped dynamics under three sources
**Build:** Run stability, legibility/recoverability, and Toil-matters in `tests/test_needs_dynamics.py`.
The added source shifts the numbers; the tests are property-based, so they should still hold (the
legibility test pins the aristocracy, which now cuts barley *and* flocks → a *larger* shortage, so it
should still drop a band). Update any assertion that reads a stale value or whose band threshold moved.
Do not weaken a property to force a pass — a genuine break is a Stuck.
**Test:** `py -m pytest tests/test_needs_dynamics.py -q`.
**Done When:** All shipped dynamics tests pass alongside the updated redundancy test.
**Stuck If:** A shipped property fails and can't be restored without weakening it or re-tuning
barley/fish (which the additive guard forbids) — report.
- [x] Complete

### Step 3: Headless smoke
**Build:** No new code. Run the city and read the result.
**Test:** `py main.py --cycles 30 --seed 3` from `backend/`.
**Done When:** Run completes; the `THE PUBLIC:` summary shows a sane fed band at the **top of Fed /
into Well-fed** (the fish-slice lean is gone) with population **growing** (the treadmill engaging);
no crash.
**Stuck If:** The run errors, or fed sits at Hungry/Starving at rest (pastoral under-tuned — return
to Final Step 1).
- [x] Complete

### Final Step: Verify spec Done when items
**Build:** No new code. Confirm every `**Done when:**` item in `public-needs_spec.md` v3 — the new
"Feature: The pastoral chain" items and the still-applicable shipped ones (the fishery's two-source
`Redundancy` item is *superseded* — its replacement is the three-source `TestRedundancy`).
**Test:** `py -m pytest tests/ -q` — full suite. Capture output. The `[human-required]` UI item
carries forward from the barley build.
**Done When:** Every `[automated]` criterion passes via its committed test; the full suite is green.
**Stuck If:** An automated criterion fails and the cause is not clear from the output.
- [x] Complete
**Deviation:** Repaired `tests/test_needs_cycle.py::TestToilingReset` (surfaced only in the full
suite). With three sources the city's base `fed_target` is ~76, so a single cycle's drift from
`fed=50` caps at `DRIFT_STEP` (→60) for *both* the toiling and control runs — the boost is hidden
by the drift cap, not absent. Split the test into (a) the spec Done-when (`toiling` False after
`run_cycle`) and (b) a **drift-independent** boost check (`compute_chain` `fed_target` is higher
with the estates toiling than without). Same regime-shift category as the fish slice's legibility
repair; the boost is now proven *more* robustly (at the source, before the drift cap), not weakened.
No constant tuning was needed — provisional `FLOCKS_PER_LEVEL=1`, `MEAT_FED_PER_UNIT=1.0` satisfied
all four three-source redundancy bands first try.

---
⛔ Final slice complete. Run **inspector** for final sign-off.
