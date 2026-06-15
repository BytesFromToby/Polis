# Inspection — Public Needs: flocks slice (Final Sign-off)

**Feature:** public-needs — the pastoral chain (Feature: The pastoral chain, spec v3)
**Spec:** `Planning/specs/public-needs_spec.md` (v3)
**Blueprint:** `Planning/blueprints/public-needs-flocks_BP.md` (Final Slice)
**Deviations:** `output/deviations/Deviations_public-needs-flocks_2026-06-14.md`
**Date:** 2026-06-14
**Inspector verdict:** ✅ **PASS**

## Commands run
- Targeted: `py -m pytest tests/test_needs_chain.py tests/test_needs_dynamics.py tests/test_needs_cycle.py tests/test_toil.py -q` → **46 passed**
- Pastoral + additive-guard + redundancy alone: `py -m pytest tests/test_needs_chain.py::TestPastoral tests/test_needs_chain.py::TestAdditiveGuard tests/test_needs_dynamics.py::TestRedundancy -q` → **11 passed**
- Full suite: `py -m pytest tests/ -q` → **455 passed** (matches deviations claim)
- Demo: `py main.py --cycles 30 --seed 3` → `THE PUBLIC: pop=26,388 fed=72 (Fed) happy=51 (Content) health=100`

## Done-when results — Feature: The pastoral chain (6 automated, all PASS)

| Criterion | Status | Fidelity | Evidence |
|---|---|---|---|
| Pastoral routes raw → fed at MEAT_FED_PER_UNIT; raw = FLOCKS_PER_LEVEL × eumelidai.level; fed_supply += meat × MEAT_FPU; logs under `units["meat"]`; zero Eumelidai → zero | ✅ PASS | Strong | `TestPastoral.test_processor_less_routes_raw_to_fed`, `test_zero_eumelidai_zero_flocks`. Constants read from loaded def (EPL, MEAT_FPU), not literals. |
| Toiling Eumelidai × TOIL_MULT (this cycle only); `eumelidai` in `chain_role_faction_ids` | ✅ PASS | Strong | `TestPastoral.test_toiling_eumelidai`, `test_eumelidai_has_chain_role` |
| Per-chain conservation across all three chains | ✅ PASS | Strong | harvest `TestSplit.test_conservation`; fishery `TestFishery.test_per_chain_conservation`; pastoral `TestPastoral.test_per_chain_conservation` (meat == raw) |
| Barley + fish unchanged (chains.json byte-for-byte same as fish slice; additive, no re-tune) | ✅ PASS | **Strong — independently verified** | `TestAdditiveGuard` (HPL==2, FPL==3, FFP==1.0) + git diff (see Fidelity (a)) |
| Three-source redundancy (all → Fed+; -fish → Fed; -aristocracy → Hungry never Starving; -all → Starving) | ✅ PASS | Strong | `TestRedundancy` 4 cases (see Fidelity (b)) |
| Shipped dynamics still pass under three sources | ✅ PASS | Strong | `TestStability`, `TestLegibilityAndRecovery`, `TestToilMatters` all green |

## Carried-forward shipped items (regression check — all green)
- Public needs state (round-trip, bands, drunk/sickly), harvest chain (purity, production, split, porridge floor, drunk threshold, toil), drift/shortage/plenty, cycle integration, fishery — all pass in the 455-green full suite.
- **Faction.toiling reset** Done-when (`test_needs_cycle.py::TestToilingReset::test_flags_false_after_run_cycle`): PASS.

## Fidelity judgments (the three hard calls)

### (a) Additive guard / no-engine-change — **HONEST, independently confirmed**
- `TestAdditiveGuard.test_barley_and_fish_unchanged` asserts `HPL == 2`, `FPL == 3`, `FFP == 1.0` (the fish-slice values). These are read from the loaded `data/chains.json` defs, so the test would fail if barley/fish were re-tuned. Real guard, not vacuous.
- **Independent git evidence (decisive):** the flocks commit `b82cdff` changed `data/chains.json` with a **purely additive** diff — only the 6-line `pastoral` object was inserted after `fishery`; zero `-` lines touched `harvest`/`fishery`. The parent (`fab717e`, fish slice) chains.json has harvest `per_level 2` and fishery `netmenders per_level 3 / fed_per_unit 1.0`, byte-for-byte identical to current.
- **No engine change:** `engine/needs/chain.py` is **NOT** in commit `b82cdff`'s file list. Its last modification was the fish slice (`fab717e`). The fish-slice generalization (faction-keyed + data-driven unprocessed label) already covers flocks. Builder/blueprint/deviations claim verified true.

### (b) Three-source redundancy — **NOT vacuous; proves the spec property**
Re-derived the four scenarios via `TestRedundancy` (drops producer factions from the standard loaded city, seed 404, 30 cycles):
- all three → `min(fed[-10:]) >= Fed` ✅
- remove Netmenders (fish, ~30%) → `fed[-1] >= Fed` ✅ (resilience gain over the 2-source world, where this used to fall to Hungry — a genuinely stricter assertion)
- remove ARISTOCRACY (drops barley **and** flocks — Eumelidai feed both) → `all(fed) >= Hungry` **and** `fed[-1] == Hungry` (pinned to exactly Hungry, not just "≥ Hungry") ✅
- remove ARISTOCRACY + Netmenders (all food) → `fed[-1] == Starving` ✅
Assertions use directional band-index comparisons against real trajectories; the Hungry/Starving cases pin the *exact* settled band. Not vacuous.

### (c) The two shipped-test repairs — **both legitimate adaptation, not weakening**

**Repair 1 — fishery two-source redundancy → superseded by three-source `TestRedundancy` (HONEST).**
Spec v3 (lines 169–172) explicitly marks the fishery's two-source Redundancy Done-when as superseded by the pastoral three-source `TestRedundancy`. Git diff shows the old `test_fish_gone_hungry_never_starving` ("remove fish → Hungry") became `test_fish_gone_stays_fed` ("remove fish → Fed"). This is a real consequence of adding a third source: flocks now cushions the fish loss, so the city stays Fed. The change is *stricter* (demands Fed, not merely "not Starving"), and the companion "barley gone → Hungry" became "aristocracy gone → Hungry" which drops *two* sources (barley+flocks) — harder, not a dodge. Honest supersession.

**Repair 2 — `TestToilingReset` split (the most important call) — LEGITIMATE, proven independently.**
The old combined test asserted (a) flags reset AND (b) `public.fed` drifted strictly higher with committed Toil vs control, from `fed=50`. I re-derived the numbers on the standard loaded city:
- base `fed_target` = **76.31**; with the three estates toiling, boosted `fed_target` = **100.0**.
- From `fed=50`, drift is capped at `DRIFT_STEP=10`, so **both** runs land at exactly **60**. The old `results["toil"] > results["control"]` would now evaluate `60 > 60` → **False**.
The drifted-fed comparison is genuinely vacuous under three sources — not because the boost vanished, but because the drift cap hides it once the base target is well above fed+DRIFT_STEP. The split keeps the literal spec Done-when (`test_flags_false_after_run_cycle`: toiling False after `run_cycle`) and replaces the drifted comparison with a **source-level** check (`test_toil_boost_raises_fed_target`: `compute_chain` fed_target higher when estates toil, 76.31 → 100). This proves "Toil affects the cycle" *more* robustly (at the source, before the cap), and the broader Toil-matters property is independently covered by the unchanged `TestToilMatters` (committed Toil shallows a pinned-shortage trough). Verdict: honest adaptation to a regime shift, not a weakening.

## Deviations (from builder, all benign)
1. Pastoral math tested with the chain in isolation (`[PASTORAL]`) not full `CHAINS` — avoids harvest porridge noise from the mixed-estate Eumelidai; same assertions, cleaner `meat == raw`. Reasonable.
2. Renamed `TestLoader.test_loads_two_chains` → `test_loads_three_chains` — chain count moved 2→3. Mechanical.
3. `TestToilingReset` split (see Fidelity (c)). Legitimate.
- No engine change; no constant tuning (`FLOCKS_PER_LEVEL=1`, `MEAT_FED_PER_UNIT=1.0` satisfied all four redundancy bands first try).

## Demo / smoke
`py main.py --cycles 30 --seed 3`: completes, no crash. `THE PUBLIC: pop=26,388 fed=72 (Fed) happy=51 (Content) health=100`. Fed=72 sits at the **top of Fed** (band 46–75); population grew 20,000 → 26,388 (the treadmill engaged); the fish-slice ~20% lean is closed. Matches blueprint Final Step 3.

## Human sign-off required
- **[human-required]** "Watching the UI across a shortage: the needs read clearly (band words visible, change is noticeable when bands shift)" (spec Cycle integration). Carried forward from the barley build — **needs-human**. Not blocking automated sign-off.

## Failures
None. 455/455 automated tests green.

## Verdict
✅ **PASS** — all 6 pastoral automated Done-when items verified by committed tests; shipped items regression-clean (455 green); additive-guard / no-engine-change claim independently confirmed via git; redundancy test substantive; both shipped-test repairs judged legitimate adaptation, not weakening. One human-required UI item carries forward.
