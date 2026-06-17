# Inspect — Confidence (the 7th and final Public scale) — FINAL

**Feature:** Confidence — band-consequences over the `support` axis (−50..+50)
**Date:** 2026-06-17
**Inspector:** fresh-eyes, read-only
**Verdict:** ✅ **PASS**
**Suite:** **550 passed** (`py -m pytest tests/ -q`, 1.79s) · headless `py main.py --cycles 10` clean
**Confidence tests:** `test_confidence.py` (7) + `test_confidence_events.py` (6) = 13, all green

---

## Done-when items — verified

### public-needs_spec.md → Feature: Confidence

**DW1 — `confidence_band(support)` returns Hostile/Suspicious/Neutral/Favorable/Beloved at the
−30/−10/+10/+30 boundaries `[automated]`**
PASS. Re-derived independently (not via the test): ran `confidence_band` over a hand-built boundary
set. Output:
```
-50→Hostile  -30→Hostile  -29→Suspicious  -10→Suspicious  -9→Neutral
 10→Neutral   11→Favorable  30→Favorable    31→Beloved      50→Beloved   ALL OK
```
Matches the spec table exactly. Backed by `test_confidence.py::TestBands::test_boundaries`
(−30/−29/−10/−9/10/11/30/31) and `test_extremes` (−50/+50). `confidence_band` lives at
`bands.py:106-108`; table `bands.py:64-70`.

**DW2 — A Hostile/Suspicious public lifts faction Harm/Steal; Favorable/Beloved damps them;
Neutral unchanged; `public` absent → no effect `[automated]`**
PASS. Code at `behavior.py:173-181` — single `if/elif` on the band (no double-apply path).
Verified via captured weight dicts:
- `test_hostile_emboldens` / `test_suspicious_emboldens`: Harm & Steal = base + EMBOLDEN(10)
- `test_beloved_damps`: Harm & Steal = base − COOP(10)
- `test_neutral_unchanged`: support=5 (Neutral) equals the **no-public** baseline → proves Neutral
  AND `public is None` both no-op (the test compares them directly).

### faction-behavior_spec.md → Step-3 confidence-posture row
PASS. The Step-3 block (`behavior.py:171-181`) reads `confidence_band(public.support)` and applies
EMBOLDEN to Harm+Steal at Hostile/Suspicious, −COOP at Favorable/Beloved, nothing at Neutral, and
is guarded by `if public is not None`. Mirrors the unrest→crime block above it. Constants
`CONFIDENCE_EMBOLDEN_WEIGHT = 10.0` / `CONFIDENCE_COOP_WEIGHT = 10.0` at `behavior.py:25-26`.

### events_spec.md → confidence gates + 3 flagships

**`min_/max_confidence_band` gate templates at their support-band boundaries `[automated]`**
PASS. `_NEED_GATE_KEYS` includes both keys (`event_system.py:71-72`); gate logic at
`event_system.py:134-139` uses `CONFIDENCE_BANDS`/`confidence_band(public.support)` with the same
band-index ≤/≥ pattern as the other scales. `test_confidence_events.py::TestGates` proves the
boundaries (max Hostile eligible at −40, not −20; min Beloved eligible at +40, not +20).

**Removal Coalition (Hostile-only; faction rating +0.3 + domain chaos +1) `[automated]`**
PASS. `events.json:110-125`: `max_confidence_band: "Hostile"`, effects `rating +0.3` on
merchant-houses + `chaos +1` on port. `TestRemovalCoalition::test_fires_and_gated` drives
`process_active_events`: rating 4.0→4.3, port chaos 0→1.0; eligible at −40, **not** at −15. Gate
ANDs correctly (a single gate key, honored).

**Effigy in the Agora (Hostile/Suspicious; faction rating +0.2 + public support −2) `[automated]`**
PASS. `events.json:126-141`: `max_confidence_band: "Suspicious"`, `rating +0.2` + `the_public
support −2`. `TestEffigy`: eligible at −40 and −15, not at 0; rating 4.0→4.2, support −20→−22.

**Acclamation (Beloved-only; public support +5) `[automated]`**
PASS. `events.json:142-156`: `min_confidence_band: "Beloved"`, `the_public support +5`.
`TestAcclamation`: support 40→45; eligible at +40, not at +20.

**Serialization — derived display key, no new persisted field `[automated]`**
PASS. `serialize_the_public` (`serializer.py:197-220`) adds `confidence_band` as a derived key off
`p.support` (comment: "ignored on deserialize"). `deserialize_the_public` (`:223-236`) has **no**
`confidence` field. `test_confidence.py::TestSerialization` confirms the key reads off support.

---

## The 4 hard fidelity calls — re-derived independently

1. **Bands map the −50..+50 range, not 0–100** — ✅ CONFIRMED. Hand-checked all 8 named boundaries
   plus the −50/+50 extremes (table above). `_band`'s "first upper ≥ value" logic
   (`bands.py:75-79`) plus the `(-30,…)(-10,…)(10,…)(30,…)(50,…)` thresholds give exactly the spec
   table. The negative-range edge (−30→Hostile vs −29→Suspicious) is correct because `−30 <= −30`
   matches the Hostile bound first.

2. **Posture emboldens low / damps high / no-ops at Neutral & no-public, no double-apply** — ✅
   CONFIRMED. Single `if/elif` branch (`behavior.py:176-181`); no second site touches Harm/Steal
   from confidence. Captured-weight tests prove all four arms. The `if public is not None` guard
   (`:173`) gives the no-public no-op, and `test_neutral_unchanged` ties Neutral to the no-public
   baseline.

3. **Three events gate on correct bands + fire stated effects; target/domain exist** — ✅
   CONFIRMED. Gates AND correctly (proven by the not-eligible assertions). Effects re-derived via
   `process_active_events` in the tests (exact deltas above). `merchant-houses` exists in
   `factions.json:809` with `domain_primary: "port"`; the `port` domain exists in
   `domains.json:67`. The `chaos`/`rating`/public-`support` effect fields are all handled in
   `_apply_single_event_effect` (`event_system.py:300-338`).

4. **No new persisted field — confidence is purely a view over `support`** — ✅ CONFIRMED.
   `ThePublic` gained no `confidence` field; deserialize is unchanged; only the derived
   `confidence_band` display key was added. Round-trip is unaffected (deserialize ignores the key).

---

## Resting-band check (the consumption-slice lesson)

Drove `run_cycle` directly for 40 cycles across seeds 101/202/303, tracking the confidence band
each cycle:
```
seed 101: Neutral 40/40   support=3    {'Neutral': 40}
seed 202: Neutral 40/40   support=6    {'Neutral': 40}
seed 303: Neutral 38/40   support=-10  {'Neutral': 38, 'Suspicious': 2}
```
✅ The standard city rests **Neutral** — the posture modifier and confidence events are dormant at
baseline and reachable only through play. It does **not** pin to an extreme (Hostile/Beloved), which
is the failure class consumption hit. This is the correct outcome.

Note: seed 303 grazes Suspicious for 2 cycles (support touches −10), so the builder's exact
"40/40 across all three seeds" claim is slightly optimistic — it's 40/40/38. The conclusion is
unaffected: Neutral-at-rest holds, no extreme pin. Flagged as a nit, not a defect.

---

## Test fidelity

- **Constants imported, not copied:** `test_confidence.py` asserts against
  `behavior.CONFIDENCE_EMBOLDEN_WEIGHT` / `CONFIDENCE_COOP_WEIGHT` and imports `confidence_band` —
  no hard-coded copies of the band thresholds or weights. Event tests read effect values straight
  from `events.json`. Good.
- **No tautologies:** the posture tests capture real weight dicts through a monkeypatched
  `weighted_choice` and compare against a separately-captured baseline; the event tests run the
  real `process_active_events` and assert on mutated state.
- **No `[automated]` Done-when left unbacked:** every confidence Done-when across the three specs
  has a backing assertion.

### Nits (non-blocking)
1. Builder's deviation log / report says resting is "40/40 across seeds 101/202/303"; actual is
   40/40/38 (seed 303 grazes Suspicious twice). Cosmetic — update the claim if precision matters.
2. The events_spec wording for the gate Done-whens says "sentinel-proven"; the confidence gate
   tests prove boundaries via `_matches_trigger` with literal support values rather than injected
   no-effect sentinel templates. Equivalent rigor (it exercises the real gate path), just a
   different mechanism than the literal spec phrasing. No correctness gap.
3. Spec/deviation drift: Effigy and Removal Coalition spec text says "a rival/high-rating faction";
   implementation hardcodes `merchant-houses`. This is the logged, intentional deviation
   (Deviations_confidence_2026-06-17.md) — a concrete ringleader was needed. Acceptable; noted for
   the record.

---

## Verdict
✅ **PASS.** All automated Done-when items across public-needs / faction-behavior / events specs
are met and independently re-derived. The four hard fidelity calls hold. The scale rests Neutral
(no extreme pin). Suite 550 green; headless clean. The seven-scale Public model is structurally
complete.
