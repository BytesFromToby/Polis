# Inspection — Piety + Unrest (Final)

**Date:** 2026-06-16  **Verdict:** ✅ **PASS**  **Suite:** 507 passed (33 in the three new files).
**Inspector note:** the fresh-eyes subagent hit a session limit before running; this inspection was
performed directly by the main agent, re-deriving each hard call from the code rather than trusting
test names. Independence is therefore weaker than a separate subagent — flagged honestly.

## How verified

Full suite `py -m pytest tests/ -q` → **507 passed**. Headless `py main.py --cycles 10` → exit 0,
no traceback. The 3 new files (`test_piety.py` 14, `test_unrest.py` 10, `test_public_scale_events.py`
9) all green and import spec constants (`PIETY_PER_LEVEL`, `PIETY_BLAME`, `UNREST_*`,
`GUARD_*`, `UNREST_CRIME_WEIGHT`) rather than copying values — no tautologies found (strict
inequalities, real weight-dict capture, real state mutation asserted).

## Done-when coverage

- **Needs-state:** round-trip piety/unrest + legacy default 50/10 (`test_round_trip_piety_unrest`,
  `test_absent_fields_default`); piety/unrest band boundaries (`TestBands`). ✓
- **Piety driver:** temple-only supply, zero-temple → 0, Toil ×1.5 / Withhold ×0 on temples,
  parity target (`TestDriver`). ✓
- **Piety drift / zealot tax / crisis-blame:** `TestDrift`, `TestZealotTax`, `TestCrisisBlame`. ✓
- **Unrest target / asymmetry / Guard / heavy-handed:** `TestPressureTarget`, `TestAsymmetricMemory`,
  `TestGuardLever` (paid / unpaid / no-guard / heavy / light). ✓
- **Unrest→crime:** `TestUnrestCrime` (Quiet vs Restless vs Boiling weight steps). ✓
- **Events:** public-targeted effect clamp, piety/unrest gates, both flagships fire + gate
  (`test_public_scale_events.py`). ✓

## Hard calls — re-derived from code (not test names)

1. **Crisis-blame scales ONLY negative support deltas.** `drift.py:77–84`: `raw = fed_d + happy_d`;
   `neg = Σ negative components`; `raw += (round(neg × blame) − neg)` replaces the negative part
   with its scaled version, leaving positives untouched. Hand-checked: Starving(−5)+Content(0) at
   Godless → −8; Well fed(+2)+Festive(+2) at Godless → +4 (unscaled). No double-count. ✓
2. **Unrest asymmetric memory + Guard.** `drift.py:100–114`: rise via `_drift_toward` (≤DRIFT_STEP
   10) when target ≥ unrest, else ease by exactly `UNREST_EASE` (4). Guard suppression runs AFTER
   drift, subtracts from `public.unrest` only (never `unrest_target`), gated on present + level≥1 +
   `guard_paid`; heavy-handed cost at `GUARD_HEAVY_THRESHOLD`. The cause is recomputed fresh each
   cycle, so a suppressed-but-unfixed city climbs back — the "festers" property holds. ✓
3. **Public-targeted effects + flagships.** `event_system.py`: `the_public` target clamps a scale
   delta and is None-safe; `min_unrest_band`/`max_piety_band` gate at the boundary; `mob_marches`
   raises chaos + lowers Public health, `ignored_omen` lowers piety + support and is Lax/Godless-only.
   All asserted. **Nit below.** ✓ (with nit)
4. **Ordering.** `drift.py:94` drifts piety before `:100` computes `unrest_target` (which reads the
   piety band — impiety is a pressure term). Correct sequence. ✓

## Nits

1. **(real, minor — fix recommended)** Public-targeted `support` effect clamps to `min(100, …)` in
   `_apply_single_event_effect`, but `ThePublic.support`'s valid range is −50..+50. Harmless for the
   shipped flagships (both apply *negative* support, and the −50 floor is correct), but a future
   positive-support public event could push `support` past +50. Upper clamp should be +50 for the
   `support` field. **Fixed immediately post-inspection** (one-line correction + a guard test).
2. **(cosmetic)** `Treasury.guard_paid_this_cycle` defaults True; a city with no Guard faction but a
   met payroll still reports paid — irrelevant because the suppression also requires the `city-guard`
   faction to be present. No action.

## Conclusion
PASS. The two scales integrate cleanly into the needs step in the spec's order, the City Guard lever
behaves as a costed symptom-suppressor (not a cause-fixer), events can finally touch the Public, and
the full suite is green. One minor support-clamp bound corrected on the spot.
