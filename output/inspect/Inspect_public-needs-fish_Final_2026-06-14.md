# Inspection Report — Public Needs: The Fishery (fish slice) — FINAL SIGN-OFF
**Date:** 2026-06-14
**Inspector:** final-sign-off pass (fresh eyes; independent of builder — code treated as a black box)
**Spec:** `Planning/specs/public-needs_spec.md` (v2 — Feature: The fishery; + the still-shipped barley features)
**Blueprint:** `Planning/blueprints/public-needs-fish_BP.md`
**Deviations file:** `output/deviations/Deviations_public-needs-fish_2026-06-14.md`

**Verdict: PASS** — every `[automated]` Done-when criterion is proven by a committed test that
would fail if the criterion were violated. The two scrutiny points (the redundancy test and the
legibility repair) were re-derived independently and both hold: **fidelity ok on both.** The single
`[human-required]` UI item carries forward from the barley build (needs-human, not judged). No
failures.

## Done-when inventory (public-needs_spec.md v2)
- **Total `**Done when:**` items: 26** across 5 features.
  - Public needs state: 3 automated
  - The harvest chain: 6 automated
  - The fishery (fish slice, the focus): 7 automated
  - Drift, shortage, plenty: 4 automated
  - Cycle integration: 9 items — 8 automated, **1 human-required** (UI needs read clearly)
- **Automated: 25 · Human-required: 1.**

## Test baseline
`cd H:\Polis\backend; py -m pytest tests/ -q` → **447 passed in 2.21s** (zero failures, zero skips;
matches the ~447 expected — up from the barley build's 436 by the new fishery + redundancy tests).
Fish-slice files alone: `tests/test_needs_chain.py tests/test_needs_dynamics.py tests/test_toil.py
tests/test_needs_cycle.py -q` → **38 passed in 0.48s**.

## Headless run
`py main.py --cycles 30 --seed 3` → completes, no crash. Summary line:
`THE PUBLIC: pop=22,523 fed=68 (Fed) happy=55 (Content) health=100`
City sits in the **Fed** band (not Starving, not Well-fed) — exactly the "slightly lean, Fed-at-rest"
state the spec calls intentional pending the flocks source. Sane.

---

## Per-criterion results — Feature: The fishery (the fish slice)

| # | Criterion | Status | Fidelity | Evidence (`tests/test_needs_chain.py` unless noted) |
|---|---|---|---|---|
| F1 | `compute_chain` sums a `faction_id`-keyed producer over only that one faction; domain path unchanged | PASS | ok | `TestFishery::test_faction_keyed_sums_only_netmenders` — adds a 2nd harbor faction (quaymen, rating 4.0) and asserts `units["fish"] == FPL*2` (Netmenders level 2 only); domain path covered unchanged by `TestProduction`/`TestSplit`. Would fail if the domain branch leaked into the faction-keyed sum. |
| F2 | Processor-less chain routes all raw to `fed` at `FISH_FED_PER_UNIT`; raw = `FISH_PER_LEVEL×level`; zero Netmenders → zero fish | PASS | ok | `test_processor_less_routes_raw_to_fed` (asserts `fed_target` == `PARITY_TARGET*(raw_fish*FFP)/demand`, constants read from loaded def) + `test_zero_netmenders_zero_fish` (empty factions → `units.get("fish",0)==0`, `raw==0`). |
| F3 | Toiling Netmenders contributes `×TOIL_MULT` fish, this cycle only | PASS | ok | `test_toiling_netmenders` — `boosted == baseline * TOIL_MULT`. "This cycle only" closed by the reset proof `test_needs_cycle.py::TestToilingReset` (all `toiling` False after `run_cycle`). |
| F4 | Per-chain conservation (harvest: bread+wine+porridge=raw; fishery: fish=fish raw) | PASS | ok | `test_per_chain_conservation` (`units["fish"]==out.raw` on a fishery-only city) + `TestSplit::test_conservation` (harvest, 3 rating sets, 1e-9 tol). |
| F5 | **Redundancy**: both → Fed+; barley gone → Hungry never Starving; fish gone → Hungry never Starving; both gone → Starving | PASS | **ok** (re-derived — see Fidelity §A) | `test_needs_dynamics.py::TestRedundancy` (4 tests). |
| F6 | Shipped harvest dynamics still pass under the re-tune + added fish | PASS | **ok** (legibility repair re-derived — see Fidelity §B) | `TestStability`, `TestLegibilityAndRecovery`, `TestToilMatters` all green at HPL=2. |
| F7 | All chain tests reference the named constants, never baked-in literals | PASS | ok | `test_needs_chain.py` reads `HPL/CAP/FPL/FFP/PORRIDGE_FPU` from `load_chains()` at module top (lines 30-38). Remaining integer literals (`27`, `9`) are fixture **level-sums**, not production constants, and are multiplied by the loaded `HPL`. |

## Per-criterion results — shipped features (spot-check: no regression under the re-tune)

| Feature / # | Criterion | Status | Fidelity | Evidence |
|---|---|---|---|---|
| Chain 1 | Pure function; twice → identical, no mutation | PASS | ok | `TestPurity` |
| Chain 2 | Raw = Σ HPL×level; dead estates → zero | PASS | ok | `TestProduction` (`raw == HPL*(4+3+2)`; dead-estates via faction removal) |
| Chain 3 | Over-cap → full caps + porridge; under-cap → proportional, no leftover | PASS | ok | `TestSplit::test_under_capacity_..` (raw HPL*3 ≤ 24 → 50/50/0), `test_over_capacity_..` (explicit high-aristocracy fixture HPL*27 > 24 → caps + porridge). Regime shift handled per blueprint Step 6. |
| Chain 4 | Conservation bread+wine+porridge=raw | PASS | ok | `TestSplit::test_conservation` |
| Chain 5 | Porridge floor: no processors → 0.4×raw, nonzero when raw nonzero | PASS | ok | `TestPorridgeFloor` |
| Chain 6 | Toil ×1.5 producer / ×1.5 processor | PASS | ok | `TestToil` (both) |
| State 1-3 | round-trip; band boundaries; drunk/sickly | PASS | ok | `test_needs_bands.py`, `test_needs_cycle.py::TestSnapshotRoundTrip` (full suite green) |
| Drift 1-4 | drift step; deltas; population; drunk-city | PASS | ok | `test_needs_drift.py` (full suite green) |
| Cycle 1-2 | needs step ordering; sentinel band-gating | PASS | ok | `test_needs_event_gates.py` (full suite green) |
| Cycle 3 | `toiling` false after `run_cycle` | PASS | ok | `test_needs_cycle.py::TestToilingReset` |
| Cycle 4 | Stability ≥ 50/60 Hungry-or-better | PASS | ok | `TestStability` (seed 101) |
| Cycle 5 | Legibility ≤5 / recoverability ≤15 | PASS | **ok** (repaired — §B) | `TestLegibilityAndRecovery` |
| Cycle 6 | Toil matters | PASS | ok | `TestToilMatters` (committed Protect vs committed Toil) |
| Cycle 7 | Audience prompt needs line | PASS | ok | `test_audience_terms.py` |
| Cycle 8 | **[human-required]** UI reads clearly across a shortage | **NEEDS-HUMAN** | n/a | Carries forward from the barley build (screenshots in `Inspect_public-needs_final_2026-06-12.md`). Not re-judged this slice — no UI change in the fish slice. |

---

## Fidelity — the two scrutiny points

### §A — Redundancy test (`TestRedundancy`): **fidelity ok**
I instrumented the four scenarios on the real standard city (seed 404, 30 cycles), the same path
the test drives:

| Scenario | end `fed` | end band | min `fed` | min band |
|---|---|---|---|---|
| both sources | 55 | **Fed** | 54 | Fed |
| barley gone (del aristocracy) | 22 | **Hungry** | 22 | Hungry |
| fish gone (del netmenders) | 40 | **Hungry** | 23 | Hungry |
| both gone | 0 | **Starving** | 0 | Starving |

Each scenario lands in a **genuinely different band**, so no assertion is vacuous:
- `test_both_sources_fed_or_better` asserts `min(last-10) >= Fed` — real (the band is Fed, not coasting at a boundary).
- `test_barley_gone` / `test_fish_gone` assert `all(>= Hungry)` (the "never Starving" guard, checked over **every** cycle, not just the end) **and** `band(last) == Hungry` (settles) — both live; removing either source genuinely lands Hungry and never touches Starving.
- `test_both_gone` asserts `band(last) == Starving` — and with both removed `fed` collapses to 0. This would fail if the two sources weren't both load-bearing.

The test proves "lose either → Hungry and NOT Starving" and "lose both → Starving" exactly as the
spec's redundancy goal states. `netmenders` and the three aristocracy factions all exist in the real
`data/factions.json`, so the deletions remove live sources (confirmed). Not vacuous.

### §B — Legibility repair (halve → pinned 1.0): **fidelity ok — legitimate adaptation, not a weakening**
The builder changed the induced shortage in `TestLegibilityAndRecovery` from a one-time *halve* of
the aristocracy ratings to a *sustained pin at 1.0* across cycles 10–19, then restore at 20. I
re-derived both behaviors independently on the two-source city (seed 202):

- **Old halve, run against the two-source world:** `fed` dips only 61→51→54 and **never leaves the
  Fed band** (`min(band 10:15) == 2 == start_band`). The old assertion `min <= start_band-1` would
  **FAIL**. The estates regrow after a one-time halve and fish cushions the dip — the system
  correctly absorbs a transient blip. So the halve no longer *induces a shortage at all* in the
  two-source world; keeping it would test nothing.
- **New pin:** `fed` falls 61→41→37→33, dropping to the **Hungry** band (`min(band 10:15) == 1 ==
  start_band-1`) — a real, **exactly one-band** drop (not a vacuously huge cut), then recovers to
  band ≥ Fed by cycle ~23 (`any(band >= start) in 20:35` holds).

Judgment: the change makes the shortage *real and sustained* instead of a blip the redundant system
is supposed to absorb. The test's **property is unchanged** — "a shortage is visible within 5 cycles
and recovers within 15" — and both assertions still bind with no slack (the cut drops exactly one
band; recovery is genuine, not asserted-by-coincidence). It uses the same pin-at-1.0 pattern already
accepted in the shipped `TestToilMatters`. This is a correct adaptation to the redundancy the slice
introduced, **not** a weakening that masks a regression. If legibility or recoverability genuinely
broke, this test would still fail.

`fidelity: ok` for both.

---

## Deviations (from `Deviations_public-needs-fish_2026-06-14.md`)
1. **`[inspect]` gate on Slice 1 flowed past** — single inspector pass at the end, per the user's
   "build on all slices" instruction. This report is that single pass; it covers both slices.
   Acceptable — the re-tune left the legibility test transiently red between Slice 1 and its Final-
   Slice repair, a known cross-slice sequence, and the final suite is fully green.
2. **Legibility test repaired (halve → pinned 1.0)** — judged independently above (§B). Legitimate,
   not a weakening.
3. **No constant tuning needed** — `HARVEST_PER_LEVEL=2`, `FISH_PER_LEVEL=3`, `FISH_FED_PER_UNIT=1.0`
   satisfy all four redundancy bands first try (confirmed: see §A table). Matches `data/chains.json`.

All deviations are recorded and benign. None masks a missing or weakened criterion.

## Failures
None.

## Human sign-off required
- **Cycle integration #8 (`[human-required]`):** "Watching the UI across a shortage, the needs read
  clearly." Unchanged from the barley build (no UI work in the fish slice). Carries forward —
  prior screenshot evidence in `Inspect_public-needs_final_2026-06-12.md`. Mark needs-human; not a
  blocker for this slice's sign-off.

## Conclusion
The fishery slice is **done as specified**. All 25 automated Done-when items pass via committed
tests that genuinely exercise their criteria; the redundancy test and the legibility repair — the
two highest-risk fidelity points — both hold under independent re-derivation. Full suite 447 green;
headless city rests in the Fed band. **PASS.**
