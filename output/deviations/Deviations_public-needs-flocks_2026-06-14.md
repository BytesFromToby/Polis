# Deviations — Public Needs: flocks slice
Blueprint: Planning/blueprints/public-needs-flocks_BP.md
Date: 2026-06-14

| Slice | Step | Deviation | Why |
|-------|------|-----------|-----|
| 1 | 2 | Pastoral math tested with the chain in isolation (`[PASTORAL]`), not full `CHAINS` | The Eumelidai also feed the harvest chain (mixed estate) → full CHAINS adds porridge noise; isolation keeps `meat == raw` clean. Same assertions. |
| 1 | 2 | Renamed shipped `TestLoader.test_loads_two_chains` → `test_loads_three_chains` | Chain count moved 2→3. |
| Final | — | Repaired `test_needs_cycle.py::TestToilingReset` — split into the reset assertion + a drift-independent boost check (`compute_chain` `fed_target` higher when estates toil) | Three sources raise the base `fed_target` to ~76, so a single cycle's drift from `fed=50` caps at `DRIFT_STEP` for both toil and control — the boost is hidden by the cap, not absent. Proven at the source now (more robust, not weakened). Same regime-shift category as the fish legibility repair. |

No engine (`chain.py`) change — the fish-slice generalization already covers faction-keyed,
processor-less chains. No constant tuning needed — `FLOCKS_PER_LEVEL=1`, `MEAT_FED_PER_UNIT=1.0`
satisfied all four three-source redundancy bands on the first try. Full suite **455 green**;
headless smoke fed=72 (top of Fed, the lean closed) with population grown to 26,388 (treadmill
engaged).
