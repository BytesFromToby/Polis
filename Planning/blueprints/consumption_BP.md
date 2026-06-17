# Blueprint — Consumption + the Public→production wire

**Spec:** `public-needs_spec.md` (Features: Consumption, The Public→production wire),
`food-supply_spec.md` (efficiency multiplier + `wine_happy`), `events_spec.md` (consumption gates
+ 2 flagships), `special-factions_spec.md` (field). **Decision:**
`decisions/2026-06-16-consumption-and-production-wire.md`. **Test:** `cd backend && py -m pytest tests/ -q`

Three slices, all `[inspect]`. New constants importable. Each slice ends green. Integration point
is again `engine/needs/drift.py::apply_needs` + `engine/needs/chain.py::compute_chain`.

---

## Slice 1 — Consumption scale (subsumes `drunk`)  `[inspect]`

**Build**
1. **Model** (`engine/models.py`): `ThePublic.consumption: int = 45`.
2. **Serialize** (`serializer.py`): add `consumption` (default 45) + `consumption_band`.
3. **Bands** (`engine/needs/bands.py`): `CONSUMPTION_BANDS` (Dry/Sober/Tempered/Tipsy/Sodden,
   20/40/60/80) + `consumption_band(v)`.
4. **ChainOutput refactor** (`engine/needs/chain.py`): replace the `drunk: bool` field with
   `wine_happy: float`; stop computing `drunk` (remove `DRUNK_THRESHOLD` use); set
   `wine_happy` (the accumulated wine happiness) on the output. Keep `wine_happy` at its
   **pre-efficiency** value (it drives the consumption scale, not the food the people get).
   - Update reader `engine/llm/prompt_builder.py:279` → read `public.drunk` instead of
     `compute_chain(...).drunk`.
5. **scales.py** (`engine/needs/scales.py`): `consumption_target(wine_happy, population)` =
   `clamp(100 × wine_happy / (demand × CONSUMPTION_PARITY), 0, 100)`; constants
   `CONSUMPTION_PARITY` (tune so the standard city sits Tempered), `CONSUMPTION_DRY_HEALTH = -2`.
6. **apply_needs** (`engine/needs/drift.py`): after the piety block, before unrest —
   - drift `consumption` toward `consumption_target(out.wine_happy, population)`;
   - set `public.drunk = consumption_band(consumption) in ("Tipsy", "Sodden")` (replaces the old
     `public.drunk = out.drunk`);
   - Dry band → `public.health += CONSUMPTION_DRY_HEALTH` (clamped).
   - (Unrest already reads `public.drunk` — now fed by consumption.)

**Test** (`tests/test_consumption.py` new; update `tests/test_needs_chain.py` drunk test)
- Round-trip consumption (default 45) + `consumption_band` boundaries → *needs-state DW*.
- `consumption_target` rises with `wine_happy` per demand; zero wine → 0; drift by DRIFT_STEP, no
  overshoot → *Consumption DW1*.
- `public.drunk` true iff band Tipsy/Sodden (sweep consumption values) → *Consumption DW2*.
- Dry city loses `CONSUMPTION_DRY_HEALTH` health/cycle; Tempered does not → *Consumption DW3*.
- **Coupling:** `test_needs_chain.py`'s old `.drunk` threshold test (L133–134) is reframed — the
  chain reports `wine_happy`; the *drunk* assertion moves to the consumption scale (wine drives
  consumption → Tipsy/Sodden → drunk). Reframe, don't delete the property.

**Stuck if:** removing `ChainOutput.drunk` reveals a reader beyond `prompt_builder` /
`apply_needs` / the one chain test — surface it (grep first).

---

## Slice 2 — The Public→production wire  `[inspect]`

**Build**
1. **scales.py:** `production_efficiency(public)` = `clamp(1.0 + health_bonus − consumption_penalty,
   EFF_MIN, EFF_MAX)`; constants `HEALTH_OUTPUT = 0.05` (Robust +1×, Thriving +2×),
   `CONSUMPTION_OUTPUT = 0.10` (Tipsy −1×, Sodden −2×), `EFF_MIN = 0.5`, `EFF_MAX = 1.25`. Read
   from the Public's **current** health/consumption bands.
2. **compute_chain** (`engine/needs/chain.py`): add `efficiency: float = 1.0` param; scale the
   **food output** by it — apply to `fed_supply` and `happy_supply` when computing targets (NOT to
   raw or `wine_happy`, preserving unit conservation and the consumption driver). `efficiency=1.0`
   → byte-identical to today.
3. **runner** (`engine/cycle/runner.py`): `eff = production_efficiency(public) if public else 1.0`;
   pass `efficiency=eff` to `compute_chain`.

**Test** (`tests/test_production_wire.py` new)
- `production_efficiency`: Healthy+Tempered → 1.0; Thriving → >1.0 (and = 1+2×HEALTH_OUTPUT with
  Tempered); Sodden → <1.0; clamped to `[EFF_MIN, EFF_MAX]` at extremes → *wire DW1, DW2*.
- `compute_chain` with `efficiency<1` yields strictly lower fed/happy targets than `=1`, and
  `>1` strictly higher; `wine_happy` and `raw`/unit conservation are unchanged by efficiency → *wire DW1*.
- **The shipped dynamics + redundancy suites still pass** with the wire live in the runner; adjust
  only the anticipated coupling (re-tune a constant or a fixture, never mask a regression). Run the
  full `test_needs_dynamics.py` + redundancy and record any property that shifts → *wire DW3*.

**Stuck if:** the wire pushes the standard city out of its shipped band envelope by more than a
re-tune can absorb — stop and report (the magnitudes are meant to nudge, not dominate; if they
must dominate to matter, the spec needs revisiting).

---

## Final Slice — Events: consumption gates + flagships  `[inspect]`

**Build**
1. **Gates** (`engine/events/event_system.py`): add `min_/max_consumption_band` to
   `_NEED_GATE_KEYS` + the band-index checks in `_matches_need_gates` (reuse the piety/unrest pattern).
2. **Templates** (`backend/data/events.json`):
   - **The Wells Sicken** — `max_consumption_band: "Dry"`, target the_public, `health −4`, duration 2.
   - **The Drunken Riot** — `min_consumption_band: "Sodden"` AND `min_unrest_band: "Restless"`,
     effects: chaos +2 (a domain) + the_public `health −3`, duration 1.

**Test** (`tests/test_consumption_events.py` new)
- `min_/max_consumption_band` gate sentinels at the boundary → *events DW*.
- The Wells Sicken eligible only at Dry, drains Public health → *events DW*.
- The Drunken Riot requires BOTH Sodden consumption AND Restless+ unrest (neither alone fires),
  raises chaos + lowers Public health on fire → *events DW*.
- Headless `py main.py --cycles 10` survives; full suite green.

---

## Inspector
Fresh-eyes subagent (retry now that the limit reset). Hard calls: (a) consumption is wine-driven
with NO misery→drink loop, and `drunk` derives solely from its band; (b) the efficiency multiplier
is 1.0 at Healthy+Tempered, scales food output only, clamped, and preserves unit conservation +
`wine_happy`; (c) the shipped redundancy/dynamics still hold with the wire live; (d) the Drunken
Riot's compound gate (consumption AND unrest). Stamp the blueprint; report to `output/inspect/`.

❌ Inspector: FAIL — 2026-06-17 — code/tests sound (534 green) + all 4 hard calls correct as code, BUT std city pins Sodden/drunk at rest (wine_happy/demand≈0.27 vs CONSUMPTION_PARITY=0.10 → target clamps to 100), violating the spec's "sits Tempered"; wire becomes a standing −10% drag, Drunken Riot half-gate perma-armed. Repair: (1) re-tune CONSUMPTION_PARITY against the real ≈0.27; (2) add a std-city resting-consumption-band regression test (current parity test is a tautology). See output/inspect/Inspect_consumption_Final_2026-06-17.md.

✅ Inspector: PASS (post-fix) — 2026-06-17 — FAIL repaired: CONSUMPTION_PARITY 0.10→0.27 (fresh wine/demand=0.27, not the mis-measured 0.097) so the std city rests Tempered (0 Sodden cycles, resting efficiency 1.0); non-tautological resting-band regression added; 537 green. Re-verified by main agent (SendMessage unavailable to continue the subagent).
