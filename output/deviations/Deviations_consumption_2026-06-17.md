# Deviations — Consumption + the Public→production wire

Blueprint: Planning/blueprints/consumption_BP.md
Date: 2026-06-17 (build spanned 06-16→06-17)

| Slice | Step | Deviation | Why |
|-------|------|-----------|-----|
| 1 | 4 | `ChainOutput.drunk: bool` → `wine_happy: float`; the chain stops computing `drunk` and `DRUNK_THRESHOLD` is removed. Readers updated: `prompt_builder.py` (now reads `public.drunk`), `test_needs_chain.py` (`TestDrunkThreshold` reframed to `TestWineHappy`), and the `out_with` helpers in `test_piety`/`test_unrest`/`test_needs_drift` (`drunk=` → `wine_happy=`). | The refactor the blueprint anticipated: consumption is now the single source of `drunk`. All mechanical id/keyword swaps; the drunk *property* moved to `test_consumption.py`. |
| 1 | 5 | `CONSUMPTION_PARITY` tuned **0.18 → 0.10 → 0.27** (see fix below). | First guesses were measured from an *evolved* roster (drifted winepressers); the **fresh** std city's `wine_happy/demand = 0.27`, so PARITY = 0.27 lands it Tempered. |
| FIX | — | **Inspector FAIL repair (2026-06-17):** PARITY 0.10 → **0.27**; added `TestStdCityRestsTempered` (3 tests: fresh city opens Tempered, never pins Sodden across seeds 101/202/303, resting efficiency == 1.0). | The 0.10 tune was measured wrong (0.097 from a drifted roster, not the 0.27 fresh roster), so the std city pinned **Sodden/drunk** at rest — a standing −10% wire drag + perma-armed Drunken Riot half-gate. The inspector caught it (no test asserted the std city's resting band; the old parity test was a tautology). Now: rests Tempered, drifts to Sober/Dry as the pop treadmill outpaces wine (legitimate), 0 Sodden cycles. |
| 2 | 1 | Added `HEALTH_BANDS` (Plague/Sickly/Healthy/Robust/Thriving) + `health_band()` — health had only the `sickly` threshold before. Plague+Sickly = the sub-40 bands, so `is_sickly` is unchanged. | The wire needs Robust/Thriving; the band table was missing. |
| 2 | 2 | The efficiency multiplier scales `fed_supply`/`happy_supply` (the food the people *get*), NOT `raw`, `units`, or `wine_happy`. | Preserves per-chain unit conservation and keeps the consumption driver (`wine_happy`) independent of the wire — proven by `test_efficiency_does_not_touch_raw_units_or_wine`. |
| Final | 2 | The Drunken Riot reuses the existing `chaos` effect + the public-targeted `health` effect (like The Mob Marches), rather than new project-damage machinery. | Proportional; reuses what exists. Its compound gate (Sodden AND Restless+) is honoured by `_matches_trigger`'s existing AND-of-all-gates logic. |

**Observed (out of scope — flag for tuning, not a bug):** the standard city's **piety pins at 100
(Zealous)** at rest, so the zealot-tax (−1 support/cycle) is effectively always on. That is a
*piety* balance question (PIETY_PER_LEVEL / PIETY_PARITY), shipped + inspected in the prior slice —
noted here for a future tuning pass, not touched.

**Tests:** `test_consumption.py` (12), `test_production_wire.py` (9), `test_consumption_events.py`
(5) + reframed `test_needs_chain` = 26 new/changed. Result: **534 green** (520 → 529 → 534);
headless `main.py --cycles 10` clean; the shipped dynamics + three-source redundancy still pass
with the wire live (the magnitudes were kept small enough to nudge, not break).
