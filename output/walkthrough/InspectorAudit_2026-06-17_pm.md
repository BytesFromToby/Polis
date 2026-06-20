# Inspector Audit — Test-Backing Coverage (walkthrough pass)

**Date:** 2026-06-17 pm
**Scope:** `[automated]` Done-when items in the specs added/heavily-changed today — `public-needs_spec.md`,
`food-supply_spec.md`, `events_spec.md`, and the `[automated]`-only items of `game-ui_spec.md`.
**Lens:** is each automated criterion encoded in a *committed regression test that exercises the
specific property* — distinct from the per-feature build inspections, which already PASSED.
**Test baseline:** `556 passed` (full run, clean).

## Summary counts

| Classification | Count |
|---|---|
| **PROVEN** | 47 |
| **WEAK** | 4 |
| **UNBACKED** | 3 |
| **Total `[automated]` items audited** | 54 |

The core logic (the four new scales, the production wire, the food chains, the event band-gates +
flagships, cycle integration) is **densely and faithfully backed** — constants are imported not
copied, boundaries are hit on both sides, and the dynamics suite asserts real `run_cycle` state
rather than tautologies. The gaps are concentrated in (a) two clamp/edge properties stated in the
spec but not asserted, and (b) the **game-ui frontend** `[automated]` items, which have **no test
runner at all** (the frontend has no vitest/jest; `package.json` exposes only `dev`/`build`/`preview`).

The tautology the team already caught — the consumption PARITY mis-tune — now carries an explicit
anti-tautology regression (`TestStdCityRestsTempered`, asserting real run_cycle bands). No new
tautological/vacuous tests were found.

---

## UNBACKED items (core-logic first)

### U1 — game-ui: faction block must not present multi-decimal `rating` as its primary number
- **Spec:** `game-ui_spec.md` → Factions panel. *"The faction block does not present the
  multi-decimal `rating` as its primary number"* `[automated]`
- **Why unbacked:** this is a frontend (`.vue`) assertion. There is **no frontend test runner**
  (no `*.test.js`/`*.spec.js`, no test script in `frontend/package.json`). No backend test can see
  the rendered faction block. Currently verifiable only by a human/static grep — so it is not a
  regression test.
- **Suggested test:** add a minimal vitest component test (or a grep-based node script run in CI)
  asserting the faction-card template renders `int(rating)` / `level` and contains no
  `rating.toFixed`/raw-`rating` interpolation as the lead number.

### U2 — game-ui: `api.js` contains no `commission` reference; dashboard table has no `entrench` column
- **Spec:** `game-ui_spec.md` → Dashboard faction table & API cleanup. Two `[automated]`
  Done-whens: *"no `entrench` column/reference… leads each row with the integer level"* and
  *"`frontend/src/api.js` contains no `commission` reference"*.
- **Why unbacked:** same root cause — frontend source assertions with no runner. (The `npm run build`
  exit-0 half is a real check but does not assert *absence* of these strings.)
- **Suggested test:** a tiny CI grep gate — `! grep -q commission frontend/src/api.js` and
  `! grep -qi entrench frontend/src/components/<DashboardFactionTable>.vue` — or fold both into a
  vitest snapshot.

### U3 — game-ui: `npm run build` completes with exit code 0 (×2 occurrences)
- **Spec:** `game-ui_spec.md` → Art direction (*"`npm run build` completes with exit code 0"*) and
  Dashboard cleanup (*"`npm run build` exits 0"*).
- **Why unbacked:** not encoded as a committed automated test — it is a manual/CI build invocation,
  not part of `pytest`. The build was presumably run by the pottery-ui inspector live, but nothing
  re-runs it as a regression gate.
- **Suggested test:** add a CI step `cd frontend && npm run build` (exit-code gated). Low effort,
  catches template/import regressions the Python suite is blind to.

> Note: these three are the *only* game-ui `[automated]` items, and all three are frontend-side.
> The one game-ui automated item that **is** backend — `serialize_the_public` exposing
> `piety_band`/`unrest_band`/`consumption_band`/`confidence_band` — is **PROVEN** (asserted in
> `test_piety.py::TestSerialization`, `test_consumption.py::TestSerialization`,
> `test_confidence.py::TestSerialization`). And the two genuinely-backend game-ui items
> (`test_state_active_events.py`, `test_projects_api.py`) are **PROVEN** (see below).

---

## WEAK items

### W1 — public-needs (Cycle): audience system prompt contains the needs line *after a cycle*
- **Spec:** `public-needs_spec.md` → Cycle integration. *"After a cycle, the audience system prompt
  contains the needs line with the current band words…"* `[automated]`
- **Backing:** `test_audience_terms.py::test_prompt_contains_needs_line` — proves the prompt builder
  emits the needs line for a given `ThePublic`, and `test_needs_bands.py::TestNeedsLine` proves the
  string assembly.
- **Why weak (not unbacked):** the property is asserted at *prompt-build* time with a hand-built
  `ThePublic`, **not** against a Public that a real `run_cycle` just drifted. The "after a cycle"
  (current, post-drift band words) link is inferred, not asserted end-to-end. Adequate as a unit
  guarantee; not a true integration proof.
- **Suggested test:** run one `run_cycle`, then build the audience prompt from the *same* public and
  assert the needs line reflects the post-cycle band.

### W2 — unrest: `unrest_target` is clamped to [0, 100]
- **Spec:** `public-needs_spec.md` → Unrest. *"`unrest_target = clamp(unrest_pressure, 0, 100)`"*
  and the Done-when *"…clamped"*.
- **Backing:** `test_unrest.py::TestPressureTarget::test_all_sources_sum` sums the four terms
  (30+20+20+10 = 80) and `test_calm_city_zero` gives 0.
- **Why weak:** neither case actually exceeds 100 or goes below 0, so the **clamp itself is never
  exercised** — `min(100.0, …)` / `max(0.0, …)` in `scales.py:87` could be removed and both tests
  would still pass. The clamp is asserted in the *spec text* of the Done-when but not in a test.
- **Suggested test:** construct a state whose raw pressure > 100 (e.g. raise weights via the
  imported constants or stack terms) and assert `unrest_target == 100.0`; likewise a floor case.

### W3 — piety: `piety_target` clamp to [0, 100] (top end)
- **Spec:** `public-needs_spec.md` → Piety. `piety_target = clamp(100 × supply / (demand×PARITY), 0, 100)`.
- **Backing:** `test_piety.py::TestDriver::test_target_parity` picks population so supply maps to
  *exactly* 100; `test_zero_temples_zero_target` gives 0.
- **Why weak:** the parity test lands *on* 100 by construction, so the **over-100 clamp branch**
  (`min(100.0, …)` in `scales.py:47`) is not exercised — a city with supply above parity-demand
  would prove it. Borderline PROVEN, flagged for symmetry with W2.
- **Suggested test:** one assertion with supply > demand×PARITY → `piety_target == 100.0`.

### W4 — production wire: the EFF clamp `[EFF_MIN, EFF_MAX]`
- **Spec:** `public-needs_spec.md` → The Public→production wire. *"The efficiency multiplier is
  clamped to `[EFF_MIN, EFF_MAX]`"* `[automated]`
- **Backing:** `test_production_wire.py::TestEfficiency::test_clamped` asserts
  `production_efficiency(health=100,consumption=50) <= EFF_MAX` and
  `(health=10,consumption=100) >= EFF_MIN`.
- **Why weak:** the assertions use `<=`/`>=`, which pass even if **no clamping occurs** (the raw
  values for those inputs sit inside the band, e.g. Thriving = 1.0+2×0.05 = 1.10 < EFF_MAX 1.25). The
  clamp branch is not demonstrably hit; the test would pass with the clamp deleted. This is the
  closest thing to a tautological assertion in the wire suite.
- **Suggested test:** drive `production_efficiency` past a clamp bound (or unit-test the clamp on a
  constructed pre-clamp value) and assert **equality** with `EFF_MAX`/`EFF_MIN`, not inequality.

---

## Spot-check: items confirmed PROVEN (representative, not exhaustive)

- **Scales serialization / defaults** — round-trip + legacy-default for piety/unrest/consumption
  (20000/60/50/50/10/45) — `test_piety.py`, `test_consumption.py`, `test_needs_bands.py`.
- **All band boundaries** (fed/happy/piety/unrest/consumption/confidence at their stated cut points)
  — `test_needs_bands.py`, `test_piety.py`, `test_consumption.py`, `test_confidence.py`.
- **Piety driver/crisis-blame/zealot-tax** — supply temple-only, Toil×1.5 / Withhold×0, the
  negative-delta-only blame scaling with exact `PIETY_BLAME["Godless"]` factor, +positive-unscaled,
  the −1 zealot tax — `test_piety.py` (strong, exact-value assertions).
- **Unrest pressure sum, asymmetric memory (DRIFT_STEP up / UNREST_EASE down), Guard suppress +
  heavy-handed support cost, unrest→Steal** — `test_unrest.py` (exact deltas).
- **Confidence posture modifier** (embolden/damp/neutral, public-absent no-op) — `test_confidence.py`.
- **Consumption driver, drunk-iff-band, Dry health drain, std-city-rests-Tempered anti-tautology** —
  `test_consumption.py`.
- **Production wire scaling** (Thriving > neutral > Sodden output; ×1.0 default; raw/units/wine
  untouched) — `test_production_wire.py`.
- **Food chains** — per-level raw, split/porridge, per-chain conservation, fishery & pastoral
  faction-keyed producers, Toil/Withhold modifiers, additive-guard (HPL/FPL byte constants),
  three-source redundancy dynamics, Withhold-matters — `test_needs_chain.py`,
  `test_needs_dynamics.py`, `test_withhold.py`.
- **Drift / shortage / plenty** — exact-step drift, health & support band deltas, population
  ±2% + floor + demand-scales-with-pop, drunk-city fixture — `test_needs_drift.py`.
- **Cycle integration** — needs-step-before-event-roll same-cycle gate, toiling-reset-after-cycle,
  snapshot round-trip — `test_needs_cycle.py`, `test_needs_event_gates.py`.
- **Event band-gates + flagships** — every new gate key (piety/unrest/consumption/confidence) at its
  boundary via sentinels; Mob Marches, Ignored Omen, Wells Sicken, Drunken Riot (compound gate),
  Removal Coalition, Effigy, Acclamation — effects AND gating asserted; public-targeted effect
  clamping to the −50..+50 support range — `test_public_scale_events.py`,
  `test_consumption_events.py`, `test_confidence_events.py`.
- **Withhold events + cycle reorder** — withholding set each active cycle, felt same cycle, restores
  after, redundancy via flag, post-needs band gating — `test_withhold_events.py`.
- **game-ui backend bits** — active_events serializer (name/cycles_remaining/target/kind) +
  empty-omitted; projects-API stack contract — `test_state_active_events.py`,
  `test_projects_api.py`.

## Tautological / vacuous tests

None outright tautological. **W4** (production-wire clamp via `<=`/`>=`) and **W2/W3** (clamp
branches never crossed) are the *vacuous-assertion* risks — each passes even if the clamp code is
deleted. Tighten to equality-at-bound assertions. The previously-tautological consumption-PARITY
check is already remediated by `TestStdCityRestsTempered`, which is explicitly documented as the
anti-tautology regression.

## Recommendations (for the walkthrough list)

1. **Add a frontend test/CI gate** (highest leverage): a vitest run or grep-gate covering U1
   (no-raw-rating), U2 (no-commission / no-entrench), and U3 (`npm run build` exit 0). Three spec
   `[automated]` items currently have zero automated backing because the frontend has no runner.
2. **Tighten the four clamp assertions** (W2 unrest, W3 piety, W4 efficiency, + add EFF lower-bound
   crossing) to *equality at the bound* with inputs that actually exceed the range.
3. **Strengthen W1** to an end-to-end run_cycle→prompt assertion so the "after a cycle / current
   bands" wording is genuinely proven, not inferred.
