# Inspector Report — Consumption + the Public→production wire

**Feature:** Public scale `consumption` (U-shaped alcohol axis, subsumes `drunk`) + the first
Public→production efficiency wire on food output.
**Spec sources:** `public-needs_spec.md` (Consumption, The Public→production wire),
`food-supply_spec.md` (efficiency multiplier + `wine_happy`), `events_spec.md` (consumption gates +
flagships), `special-factions_spec.md` (field).
**Blueprint:** `Planning/blueprints/consumption_BP.md` · **Deviations:**
`output/deviations/Deviations_consumption_2026-06-17.md`
**Inspector:** fresh-eyes, read-only. Date: 2026-06-17.

---

## VERDICT: ❌ FAIL

The code is structurally correct and all 534 tests pass, but the shipped **standard city pins at
Sodden (consumption 90–100) within 4 cycles and stays there** — a direct violation of the
Consumption feature's explicit resting-band requirement ("`CONSUMPTION_PARITY` tuned so the
standard city sits in **Tempered**", stated in both `public-needs_spec.md` and `food-supply_spec.md`,
and re-asserted in the deviation log itself: "0.10 lands it in Tempered (48)"). The mis-tune is
real, it is in-scope for this slice (it is the consumption driver this slice introduced), and it is
**not caught by any test** because the one driver test is a tautology and no test asserts the std
city's resting consumption band. See "Showstopper" below.

---

## Suite result

- `cd backend ; py -m pytest tests/ -q` → **534 passed in 1.65s** (matches the deviation note).
- Targeted: `test_needs_dynamics.py + test_consumption.py + test_production_wire.py +
  test_consumption_events.py` → **33 passed**.
- Headless `py main.py --cycles 10` → clean, no crash.

So the build is green and runs. The failure is a **fidelity/tuning** defect, not a test break.

---

## Showstopper — the standard city is permanently Sodden (drunk) at rest

**Evidence (real runner, wire live, three seeds, 20 cycles each):**

```
seed101: consumption 45→Tempered→Tipsy→Tipsy→Sodden→Sodden… (stays 100) drunk=True
seed202: …→Sodden (90) drunk=True
seed303: …→Sodden (100) drunk=True
```

**Root cause.** At the std roster the harvest chain yields **9 wine units → `wine_happy = 9 × 0.6
= 5.4`**; `demand = 20`, so `wine_happy / demand = 0.27`. With `CONSUMPTION_PARITY = 0.10`,
`consumption_target = 50 × 0.27 / 0.10 = 135 → clamp 100 (Sodden)`. The deviation log states it
measured `wine_happy/demand ≈ 0.097` (≈ 3.2 wine units) and tuned `0.10` to land Tempered — but the
as-built roster produces ~2.7× that wine (9 units, not ~3), so `0.10` lands the city deep in
**Sodden**, not Tempered. (The measurement appears to predate a roster/level change; `wine_happy` is
the same with or without the wire, so this is not the wire's doing — it is a stale `CONSUMPTION_PARITY`.)

**Why it matters (knock-on, all live in the shipped runner):**
1. **Spec violation, direct.** Consumption Done-when + the driver note in two specs require the std
   city to sit Tempered; it sits Sodden.
2. **The wire stops being "a nudge."** Sodden → `production_efficiency` clamps to **0.9** *every
   cycle at rest* — a standing −10% food drag is the default state, exactly the "regime change, not
   a nudge" the decision doc rules out.
3. **`drunk` is permanently True** → a standing +`UNREST_DRUNK` (10) pressure term, and the
   prompt/UI always says the city is drunk.
4. **The Drunken Riot's Sodden half-gate is always satisfied at rest**, so the "only fires when the
   city is already on edge" compound-gate design degrades to a pure unrest gate.

**Why no test caught it.** `test_consumption.py::TestDriver::test_parity_maps_to_midpoint` is a
**tautology**: it asserts `consumption_target(CONSUMPTION_PARITY * demand, pop) == 50`, which is
true for *any* value of `CONSUMPTION_PARITY` by construction — it proves the formula's algebra, not
that the std roster's actual `wine_happy` lands Tempered. There is no test that runs the std city
and asserts its resting consumption band (the analogue of the `fed`-band stability test exists for
food but not for consumption).

**Repair items (for the builder, fix mode):**
- Re-tune `CONSUMPTION_PARITY` against the **actual** std-roster `wine_happy/demand ≈ 0.27` so the
  resting city lands Tempered (≈ `0.27` puts the midpoint at 50; pick by feel for ~Tempered, same
  empirical method the deviation intended).
- Add a **non-tautological** regression test: run the std city headless ~15 cycles and assert the
  resting consumption band is Tempered (mirror `TestStability` for fed). This is the missing
  guardrail that would have caught the mis-tune.
- Re-confirm afterward that `production_efficiency` at rest is **1.0** (Healthy/Tempered), restoring
  the "nudge" invariant, and that the Drunken Riot is not perpetually half-armed.

---

## The 4 hard fidelity calls (re-derived independently)

**1. Consumption is wine-driven, NO misery→drink loop, `drunk` derives SOLELY from its band — PASS
(code) / the *value* mis-tunes (see showstopper).**
- `scales.py::consumption_target(wine_happy, population)` depends only on `wine_happy` and
  `population` — no `happy`/`unhappiness`/`support` term. Confirmed by reading L97–103.
- `drift.py::apply_needs` L101–105: drifts consumption toward
  `consumption_target(out.wine_happy, population)`, then `public.drunk = is_drunk(public.consumption)`
  (band-derived), then the Dry health drain. No chain `drunk` anywhere.
- Grep for `\.drunk|DRUNK_THRESHOLD|out\.drunk` across `engine/` → only `scales.py:84`
  (`unrest_target` reads `public.drunk`), `prompt_builder.py:279` (reads `public.drunk`),
  `drift.py:103` (sets it). The old chain `drunk`/`DRUNK_THRESHOLD` is gone (`ChainOutput` now
  carries `wine_happy: float`, chain.py L26). The consumption→drunk→unrest chain is coherent.

**2. The efficiency multiplier is 1.0 at Healthy+Tempered, scales food output ONLY, is clamped, and
preserves unit conservation + `wine_happy` — PASS.**
- `production_efficiency` (scales.py L121–125): `clamp(1.0 + HEALTH_OUTPUT·{Robust:1,Thriving:2} −
  CONSUMPTION_OUTPUT·{Tipsy:1,Sodden:2}, 0.5, 1.25)`. Healthy+Tempered → both lookups miss → exactly
  `1.0`. Verified live: `production_efficiency(ThePublic(health=50,consumption=50)) == 1.0`.
- `compute_chain` (chain.py L121–122): efficiency multiplies `fed_supply` / `happy_supply` **inside
  the target calc only**, NOT `raw`, `units`, or `wine_happy`. Confirmed live:
  `efficiency=0.6` vs `1.0` leave `raw`, `units`, and `wine_happy` byte-identical
  (`test_efficiency_does_not_touch_raw_units_or_wine`). `efficiency=1.0` default → un-wired output.
- Clamp `[EFF_MIN, EFF_MAX] = [0.5, 1.25]` present and tested (`test_clamped`).

**3. The shipped redundancy + dynamics hold with the wire LIVE — PASS for the tested properties;
but the wire's resting magnitude is NOT genuinely "a nudge" (see showstopper).**
- `test_needs_dynamics.py` (stability/legibility/recoverability/Toil-matters) + `TestRedundancy`
  (three-source) all pass with `runner.py` applying `efficiency=production_efficiency(public)`
  (runner L153–155). 33/33 in the combined run.
- **Judgment against the "nudge" bar: it fails.** Because the std city pins Sodden, resting
  efficiency is clamped to **0.9 every cycle**, a standing −10% drag — not the Healthy/Tempered ×1.0
  the decision doc promises. `fed` still sits **Fed (74)** so the food *dynamics* tests stay green,
  which is exactly why this slipped through: the wire's drag is absorbed by headroom, but the
  resting regime is wrong. The builder's claim that "the std city sits Tempered" is **false** as
  built (it sits Sodden).

**4. The Drunken Riot's compound gate requires BOTH — PASS (gate logic) / degraded at rest (see
showstopper).**
- `events.json` `drunken_riot.trigger_conditions = {min_consumption_band: "Sodden",
  min_unrest_band: "Restless"}`. `_matches_need_gates` (event_system.py L96–133) is an AND of all
  declared gates. Verified by `test_compound_gate_needs_both`: Sodden+Restless eligible;
  Sodden+Placid not; Tempered+Restless not.
- Caveat: because the std city is perpetually Sodden, the consumption half is always satisfied at
  rest, so in practice the riot waits only on unrest — a side effect of the tuning defect, not a
  gate-logic bug.

---

## Other checks

- **Needs-state round-trip / defaults — PASS.** `serializer.py` writes/reads `consumption`
  (default 45) and `drunk` (default False); `consumption_band` is a derived display key.
  `test_absent_defaults_45` confirms legacy saves load. `models.py` `ThePublic.consumption: int = 45`.
- **Band tables — PASS.** `CONSUMPTION_BANDS`/`HEALTH_BANDS` at 20/40/60/80; boundary test green.
  `HEALTH_BANDS` (Plague/Sickly/Healthy/Robust/Thriving) added for the wire; `is_sickly` unchanged
  (sub-40), consistent with the deviation.
- **Dry health drain — PASS.** `apply_needs` applies `CONSUMPTION_DRY_HEALTH (−2)` only in the Dry
  band; `test_dry_drains_health` / `test_tempered_no_drain`.
- **Event capability + flagships — PASS.** `_apply_single_event_effect` clamps `the_public` field
  deltas; Wells Sicken (Dry → health −4, duration 2) and Drunken Riot (chaos +2 + health −3) fire
  as specced (`test_consumption_events.py`).
- **Test fidelity — MIXED.** Tests import spec constants (no baked copies); `test_needs_chain`'s
  drunk-threshold test was correctly reframed to `TestWineHappy`. **But** `test_parity_maps_to_midpoint`
  is a tautology (flagged above), and there is **no `[automated]` backing for the std-city-sits-Tempered
  intent** — the gap that hid the showstopper.
- **Piety pins Zealous (deviation note) — out of scope, confirmed pre-existing.** The std city's
  piety pinning at Zealous (zealot tax always on) is from the prior piety slice
  (`PIETY_PER_LEVEL`/`PIETY_PARITY`), not this feature. Noted, not fixed — correct call by the
  builder. (It is, however, the *same class* of mis-tune as the consumption defect: a resting band
  that pins to an extreme with no test guarding the resting band.)

---

## Nits (non-blocking)

- The deviation log's "measured `wine_happy/demand ≈ 0.097`" is stale by ~2.7× vs the as-built
  roster (0.27); whatever changed the roster after that measurement is what broke the tune.
- `drunken_riot` template has `target_type: "domain"` with `target_id: "the_public"`; it works only
  because each effect carries its own `target_id` (`guilds` for chaos, `the_public` for health) and
  the chaos branch keys off `eff.field == "chaos"`. Harmless but slightly confusing; the template
  `target_id` is effectively unused here.

---

## Summary

Structurally the feature is sound and fully wired; all 534 tests pass; the four hard calls are
correct **as code**. It FAILs because the as-built standard city is **permanently Sodden/drunk** at
rest — violating the spec's Tempered requirement, turning the "nudge" wire into a standing −10% food
drag, and perma-arming half the Drunken Riot gate — and **no test guards the resting band**, so the
mis-tune shipped green. Fix `CONSUMPTION_PARITY` against the real `wine_happy/demand ≈ 0.27` and add
a std-city resting-band regression test.

---

## Addendum — builder fix + re-verification (2026-06-17)

The FAIL above stands as the record. The builder fixed exactly the two named repair items:
- **`CONSUMPTION_PARITY` 0.10 → 0.27.** Root cause confirmed by direct measurement: the *fresh*
  std city's `wine_happy/demand = 0.2700` (the earlier 0.097 was measured from an evolved roster
  with shrunk Winepressers). PARITY = 0.27 → fresh-city target = 50 (Tempered).
- **Non-tautological regression test** `TestStdCityRestsTempered` (3 cases): the fresh city opens
  Tempered for 5 cycles; across seeds 101/202/303 it logs **0 Sodden cycles** over 30 cycles;
  resting `production_efficiency(Healthy+Tempered) == 1.0` (the standing drunk-drag is gone).

**Re-verification (by the main agent, not the fresh subagent — SendMessage unavailable to continue
the original; honest independence caveat, same as the piety slice):** measured the trajectory
across 3 seeds (opens Tempered, drifts to Sober/Dry as the population treadmill outpaces wine —
legitimate emergent dynamics, not a pin), confirmed resting efficiency 1.0, ran the dynamics +
consumption + wire suites (31 passed) and the full suite (537 passed). The showstopper is resolved.

**Residual note (not a defect):** seed 101 drifts to **Dry** by ~cycle 40 (wine lags a growing
city) → the bad-water health drain engages. This is intended U-shaped behavior (both ends bite),
now reachable because the city is correctly centered. The **piety-pins-Zealous** observation
remains open for a future tuning pass (prior slice, out of scope).

**Post-fix verdict:** ✅ PASS.
