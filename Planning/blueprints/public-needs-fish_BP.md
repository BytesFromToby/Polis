# Blueprint: Public Needs — fish slice
Spec: Planning/specs/public-needs_spec.md (v2 — Feature: The fishery)
Date: 2026-06-14

> Increment on the shipped public-needs build. The original `public-needs_BP.md` is the closed,
> inspector-signed barley record — left untouched. This blueprint covers only the fish slice:
> faction-keyed + processor-less producers, the fishery chain, the barley re-tune, and the
> redundancy tests. All "constants" the spec names (`HARVEST_PER_LEVEL`, `FISH_PER_LEVEL`,
> `FISH_FED_PER_UNIT`) live in **`data/chains.json`** as data, not Python constants — tests must
> read them from the loaded chain def, never hardcode the number.

---

## Builder instructions
- Execute steps in order. Do not skip, reorder, or read ahead into the next slice.
- Check off each step when complete: [ ] → [x]
- One step = one logical concern. If a step can't be tested on its own, it's too small — merge it. If it touches more than one concern, split it.
- Deviation: if you do something differently than the step says, note it inline and keep going.
- Stuck: stop immediately. Do not try alternative approaches. Report exactly where and why.
- All test commands run from `backend/`: `py -m pytest tests/<file> -q`.

---

## Slice 1: Faction-keyed + processor-less producers, the fishery chain [inspect]
**Scope:** `compute_chain` produces fish from the Netmenders (a faction-keyed, processor-less
producer feeding `fed` directly), barley is re-tuned to a partial source, and the chain unit
tests pass under the new two-chain data.

### Step 1: Faction-keyed producers earn a chain role
**Build:** In `engine/needs/chain.py`, `chain_role_faction_ids`: in addition to the existing
producer-`domain` members and processor `faction_id`s, also add `chain["producers"].get("faction_id")`
to the role set when present (so a faction-keyed producer like the Netmenders becomes a chain-role
faction and can Toil). Guard: only add if that id is in `factions`.
**Test:** `py -m pytest tests/test_toil.py tests/test_needs_chain.py -q` (no regression yet; full assertions land in Step 7).
**Done When:** A chain whose producers are `{"faction_id": "netmenders"}` yields `netmenders` in `chain_role_faction_ids`.
**Stuck If:** `chain_role_faction_ids` is called somewhere that assumes domain-only producers and breaks.
- [ ] Complete

### Step 2: compute_chain sums faction-keyed producers
**Build:** In `engine/needs/chain.py`, `compute_chain`, the producer loop (currently
`if f.domain_primary == producers.get("domain")`): generalize so a producer spec keyed by
`faction_id` sums **only that one faction**, while a `domain`-keyed spec is unchanged. E.g. read
`prod_domain = producers.get("domain")` and `prod_faction = producers.get("faction_id")`, and
include faction `fid` when `(prod_domain and f.domain_primary == prod_domain) or (prod_faction and fid == prod_faction)`.
Keep the Toil `× TOIL_MULT` contribution rule intact for both.
**Test:** `py -m pytest tests/test_needs_chain.py -q` (existing harvest tests still pass — domain path unchanged).
**Done When:** A `faction_id` producer contributes `per_level × level` from only that faction; the domain path is byte-for-byte unchanged in behavior.
**Stuck If:** The domain and faction branches double-count a faction that matches both (shouldn't happen with current data, but guard against it).
- [ ] Complete

### Step 3: Unprocessed label comes from data
**Build:** In `engine/needs/chain.py`, `compute_chain`, the leftover/unprocessed block (currently
hardcodes `units["porridge"]`): take the label from data — `label = unprocessed.get("label", "porridge")`
— and accumulate into `units[label]`. The `fed_supply += leftover × fed_per_unit` line is unchanged.
This makes a processor-less chain log its raw under its own label (e.g. `"fish"`), not `"porridge"`.
**Test:** `py -m pytest tests/test_needs_chain.py -q`.
**Done When:** The harvest chain still logs `"porridge"` (its unprocessed label); a chain with unprocessed label `"fish"` logs under `"fish"`.
**Stuck If:** Any code downstream reads `units["porridge"]` by literal and would miss a renamed label (grep `units\[` / `"porridge"` across `engine/` and `tests/`).
- [ ] Complete

### Step 4: Re-tune barley to a partial source
**Build:** In `data/chains.json`, the `harvest` chain: change `producers.per_level` from `3` to `2`.
(Forward constraint: this drops the standard city's harvest raw from 27 to 18, which is now **≤**
the processors' capacity of 24 — so the standard city moves from the over-capacity regime
(bread/wine/porridge split) into the **proportional, no-porridge** regime. Step 6 reworks the
chain tests for this regime shift. The redundancy goal: barley alone ≈ Hungry, so fish is
load-bearing — see Step 5 and the Final Slice.)
**Test:** `py -m pytest tests/test_needs_chain.py -q` (expected to FAIL here — baked-in literals; Step 6 fixes them).
**Done When:** `data/chains.json` harvest `per_level == 2`.
**Stuck If:** —
- [ ] Complete

### Step 5: Add the fishery chain
**Build:** In `data/chains.json`, add a second chain object:
```json
{
  "id": "fishery",
  "producers": {"faction_id": "netmenders", "per_level": 3},
  "processors": [],
  "unprocessed": {"fed_per_unit": 1.0, "label": "fish"}
}
```
(Netmenders is already in `data/factions.json` under the harbor domain at rating 2.0. No roster
change. Provisional constants: `per_level 3`, `fed_per_unit 1.0`.)
**Test:** `py -c "from loaders import load_chains; c=load_chains(); print(len(c), [x['id'] for x in c])"` from `backend/` → 2 chains `['harvest','fishery']`.
**Done When:** `load_chains()` returns both chains; the fishery has no processors and a `fish` unprocessed label.
**Stuck If:** The JSON fails to parse.
- [ ] Complete

### Step 6: De-bake and rework the harvest chain tests
**Build:** In `tests/test_needs_chain.py`, remove hardcoded production literals so the tests read
the value from the loaded chain def (e.g. `HARVEST_PER_LEVEL = CHAINS[0]["producers"]["per_level"]`
at module top, then compute expected from it). Rework the regime-specific fixtures for the new
per_level: the standard `mk_city` is now **under** capacity (raw 18 ≤ 24), so any test that must
exercise the **over-capacity** split (full processor caps + porridge) must use an explicit
high-aristocracy fixture (raise estate ratings so raw > 24), not the standard city. Keep the
purity, dead-estates, conservation, porridge-floor, and Toil tests — recompute their expected
numbers from the loaded constant.
**Test:** `py -m pytest tests/test_needs_chain.py -q`.
**Done When:** `test_needs_chain.py` is green with no baked-in `3`/`27`/`12`/`3`-porridge literals; the over-capacity path is still covered by an explicit fixture.
**Stuck If:** A reworked expected value disagrees with `compute_chain` and the cause isn't a stale literal — stop and report the mismatch.
- [ ] Complete

### Step 7: Fishery unit tests
**Build:** In `tests/test_needs_chain.py`, add fishery cases (read constants from the loaded
fishery def): (a) a `faction_id` producer sums **only** the Netmenders — add another harbor
faction and confirm it contributes no fish; (b) processor-less routing — `fed_supply` rises by
`raw_fish × FISH_FED_PER_UNIT` where `raw_fish = FISH_PER_LEVEL × netmenders.level`, and the
output logs under `units["fish"]`; (c) zero Netmenders level (faction absent) → zero fish;
(d) a toiling Netmenders contributes `× TOIL_MULT` fish; (e) per-chain conservation — fishery
`units["fish"] == raw_fish` (and harvest still conserves); (f) `netmenders` appears in
`chain_role_faction_ids`.
**Test:** `py -m pytest tests/test_needs_chain.py tests/test_toil.py -q`.
**Done When:** All fishery cases pass; Toil tests still green (Netmenders now a chain-role faction).
**Stuck If:** `level` of an absent faction can't be expressed — use a faction at min rating and assert proportionally, or omit it (note the deviation).
- [ ] Complete

---
⛔ End of Slice 1 [inspect]. Run **inspector** on this slice before continuing.

---

## Final Slice: Redundancy dynamics + verification
**Scope:** The two-source redundancy property holds over long runs, the shipped dynamics still
pass under the re-tune, and every spec Done-when is verified.

### Step 1: Redundancy dynamics test
**Build:** In `tests/test_needs_dynamics.py`, add a redundancy test using the standard city loaded
via loaders (fixed seed; constants read from loaded chains). Four scenarios, asserting fed **bands**
(tolerance, not exact values), each run from a Fed start: (a) both sources running → fed band is
**Fed** or better across the run; (b) delete the aristocracy estates from the factions dict (barley
gone) → fed settles in **Hungry** and never reaches **Starving** within 30 cycles; (c) delete
`netmenders` (fish gone) → fed settles in **Hungry**, never Starving; (d) delete both → fed reaches
**Starving**. (Removal = `del factions[id]`, mirroring the dead-estates fixture — faction level can't
be zeroed since rating floors at 1.0.)
**Test:** `py -m pytest tests/test_needs_dynamics.py -q`.
**Done When:** All four redundancy scenarios pass. If they don't, tune the provisional constants in
`data/chains.json` (`harvest.per_level`, `fishery.per_level`, `fishery.unprocessed.fed_per_unit`)
until the band outcomes hold — record each constant change as a deviation.
**Stuck If:** No constant set satisfies "lose either → Hungry (not Starving)" **and** "lose both →
Starving" simultaneously — stop and report the trade-off data (it's a real design conflict).
- [ ] Complete

### Step 2: Re-verify the shipped dynamics under the re-tune
**Build:** Run the shipped dynamics (stability, legibility, recoverability, Toil-matters) in
`tests/test_needs_dynamics.py`. The re-tune + fish shift the numbers; the tests are property-based,
so they should still hold, but update any that read a stale baked constant or whose band threshold
moved. Do not weaken a property to force a pass — if a property genuinely breaks, that's a Stuck.
**Test:** `py -m pytest tests/test_needs_dynamics.py -q`.
**Done When:** All shipped dynamics tests pass alongside the new redundancy test.
**Stuck If:** A shipped property (e.g. stability: fed ≥ Hungry for 50/60) fails and can't be
restored by constant tuning without breaking redundancy — report.
- [ ] Complete

### Step 3: Headless smoke
**Build:** No new code. Run the city and read the result.
**Test:** `py main.py --cycles 30 --seed 3` from `backend/`.
**Done When:** Run completes; the `THE PUBLIC:` summary line shows a sane fed band (expected
**Fed**, slightly lean per the spec's intentional flocks-gap); no crash.
**Stuck If:** The run errors, or fed sits at Starving/Well-fed at rest (re-tune is off — return to Final Step 1).
- [ ] Complete

### Final Step: Verify spec Done when items
**Build:** No new code. Confirm every `**Done when:**` item in `public-needs_spec.md` v2 — both the
new "Feature: The fishery" items and the still-applicable shipped ones.
**Test:** `py -m pytest tests/ -q` — full suite. Capture output. The `[human-required]` UI item
(needs read clearly) is unchanged from the barley build; note it carries forward.
**Done When:** Every `[automated]` criterion passes via its committed test; the full suite is green.
**Stuck If:** An automated criterion fails and the cause is not clear from the output.
- [ ] Complete

---
⛔ Final slice complete. Run **inspector** for final sign-off.
