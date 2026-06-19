# Inspector Audit — Coverage of Older Specs

**Date:** 2026-06-17
**Auditor:** fresh-eyes inspector (walkthrough coverage pass)
**Suite state:** 550 passed (green), `cd backend ; py -m pytest tests/ -q`
**Scope:** `[automated]` Done-when items in the older specs (the ones without a fresh 2026-06
inspector report). The withhold / piety-unrest / consumption / confidence Done-whens were
freshly inspected this month and are out of primary scope; spot-noted where relevant.

## Scope note — specs without inline `[automated]` items
- **`faction-behavior_spec.md`** and **`special-factions_spec.md`** carry **no inline
  `[automated]` Done-when items** — they are descriptive/reference specs. Their behavior is
  exercised indirectly (NPC weights via `test_toil`/`test_withhold`/`test_npc_and_eoc`; the
  Public via `test_special_factions`). No coverage obligation to audit.
- **`personality-system_spec.md`** and **`llm-system_spec.md`** are listed in the index but
  do not exist as files in `Planning/specs/` (their content lives inside faction-behavior /
  audience / the llm tests). Nothing to audit directly.

## Summary (rough counts across audited specs)

| Class | Count (approx) |
|---|---|
| **PROVEN** | ~95 |
| **WEAK** | 6 |
| **UNBACKED** | 5 |

The core-logic specs are in excellent shape. `actions_spec`, `mayor_spec`, `treasury_spec`,
`projects_spec`, `audience_spec`, `food-supply_spec`, `events_spec`, `player-identity_spec` all
have high-fidelity, forced-outcome tests that would fail if the feature broke. The real gaps
are concentrated in **`cycle-runner_spec`**, whose orchestration-level Done-whens are partly
unasserted: `test_cycle.py` is thin and several of its own stated criteria are not actually
checked.

---

## UNBACKED `[automated]` items (priority-ordered, core logic first)

### cycle-runner_spec — Step 1 Initiative
> "`initiative_order` is re-rolled every cycle — no ordering is carried over between
> `run_cycle` calls (no persistent initiative advantage)"
> "Every faction is placed in `initiative_order` each cycle"

**Why unbacked:** no test references `initiative_order` anywhere in `tests/`. `test_cycle.py`
has no initiative assertion; the field is never inspected. The "no persistent advantage"
property — explicitly called out twice in the spec — is entirely unproven.
**Suggested test:** in `test_cycle.py`, expose/capture `result.initiative_order` (or patch the
shuffle), assert it contains every faction id each cycle, and that two consecutive `run_cycle`
calls on a fixed seed-free run do not reuse the same order deterministically.

### cycle-runner_spec — Step 4 End of Cycle
> "`run_cycle` returns a `CycleResult` whose `events` is a list of `CycleEvent` and whose
> `faction_actions` is a non-negative count **that excludes `Skip` actions**"

**Why weak→unbacked:** `test_cycle.py::test_faction_actions_counted` only asserts
`result.faction_actions >= 0` (tautological — a count is trivially ≥ 0). The load-bearing
clause — that `Skip` turns are **excluded** from the count — is never exercised.
**Suggested test:** force the 5% skip branch (monkeypatch `behavior.random.random`/skip path)
for a one-faction city and assert `result.faction_actions == 0` while an event is still logged.

### cycle-runner_spec — Step 0 Treasury ordering
> "When `treasury` and `mayor` are provided, the treasury step and tax effects run **before the
> action loop** and their results are included in the cycle's results; when either is absent,
> `run_cycle` skips them and still completes"

**Why weak→unbacked:** the *absent* half is covered (`test_run_cycle_without_mayor_still_works`,
`test_deal_ticking` runs with `treasury=None`). The *ordering* half — treasury step runs
**before** the action loop and its results land in `CycleResult` — is not asserted anywhere.
`test_treasury_income_applied_each_cycle` proves income is applied, not that it precedes the
loop or appears in the cycle results.
**Suggested test:** run a cycle and assert a `TaxIncome` result is present in `result.events`/
results, and (ordering) that treasury gold reflects step-0 income before any faction action
could have touched it — e.g. via a sentinel mayor action sequenced after.

### cycle-runner_spec — Step 3 Project Ticks (via run_cycle)
> "After project ticking, every project's `build_actions_this_cycle` is 0"

**Why weak (borderline unbacked at the orchestration level):** `test_projects.py::
TestBuildActionsReset` proves `tick_projects(...)` resets the counter — but calls the tick
function **directly**, not through `run_cycle`. The runner's contract that it *invokes* the tick
each cycle is not asserted end-to-end. (Low severity — the unit is proven; only the wiring is
untested.)
**Suggested test:** set `build_actions_this_cycle = 2` on a project, pass it through `run_cycle`,
assert it is 0 afterward.

---

## WEAK `[automated]` items

### cycle-runner_spec — Step 4
> "Domain `utilization` is recalculated as Σ faction level each cycle — no stale value carries
> over"

**Why weak:** `test_cycle.py::test_domain_utilization_recalculated` asserts only
`utilization >= 0` — vacuous. It does not prove the value equals Σ level, nor that a stale
value is overwritten.
**Suggested test:** seed `domains["political"].utilization = 999`, run a cycle, assert it equals
Σ `int(rating)` of that domain's factions (not 999).

### mayor_spec — Treasury runs but is not surfaced
> "A multi-cycle headless run shows treasury gold changing from passive tax income / maintenance
> with no player treasury action issued"

**Status:** PROVEN but worth a fidelity note — `test_treasury_runs_without_player_action`
relies on a seeded `civic` Tax Office to make gold net-positive; without it base income (20) =
guard payroll (20) and gold would not move. The test is correct, just sensitive to the constant
balance; fine as is.

### food-supply_spec — "shipped dynamics still pass under re-tuned constants"
> "The shipped harvest dynamics (stability, legibility, recoverability, Toil-matters) still
> pass under the re-tuned constants and the added fish source"

**Why weak:** this is a meta-criterion ("the other tests still pass") rather than a discrete
assertion. It is effectively covered by the suite staying green, but there is no single test
that encodes "stability/legibility/recoverability" by name — they live in `test_needs_dynamics`
/ `test_needs_drift` under generic names. Acceptable, but the mapping from this Done-when to its
proving tests is implicit, not labelled.

---

## Tautological / vacuous tests flagged

1. **`test_cycle.py::test_faction_actions_counted`** — `assert result.faction_actions >= 0`.
   A count is always ≥ 0; this asserts nothing about the Skip-exclusion the spec requires.
2. **`test_cycle.py::test_domain_utilization_recalculated`** — `assert utilization >= 0`.
   Passes regardless of whether recalculation happened or is correct.
3. **`test_cycle.py::test_result_has_events`** — `assert isinstance(result.events, list)`.
   Type-only; would pass on an always-empty list. (Low concern — the type half of the spec
   item is legitimately covered; just note it proves nothing about contents.)

These three are the weakest tests in the audited set and all sit in `test_cycle.py`, which
reads as a smoke-test stub that never grew into real orchestration coverage.

---

## Specs in good shape (no action needed)
- **actions_spec** — Grow/Protect/Aid/Harm/Steal/Toil/Withhold all forced-outcome tested with
  exact deltas, floors/caps, level-1 gates, cross-domain blocks. High fidelity.
- **mayor_spec** — Sabotage (cost/refund/fractional-rank/health-halving/no-break/rep/level-1),
  Build Project (all 4 context branches + refund), roster integrity (exact set + removed-action
  rejection). Strong.
- **treasury_spec** — income scaling, building-top exclusion, no-faction-income, expenditure,
  insolvency clamp + non-civic damage + destruction + no-ladder. Strong.
- **projects_spec** — cap derivation, build model, initiation refusal, sabotage front-only +
  destruction grace, repair, maintenance. Strong.
- **audience_spec** — active-AI gate (400s, AP), term prompt content, target guards, parser,
  budget-allocation drop, conclude/finalize confirmation flow, training-log capture. Strong.
- **food-supply_spec** — pure-function determinism, conservation per chain, Toil ×1.5 /
  Withhold ×0, three-source redundancy (Fed/Hungry/Starving), constants-not-literals. Strong.
- **events_spec** — chaos-scaled rolls, active-event processing, cascades, band gates (fed/
  happy/sickly + sentinel-per-band), flagships, public-targeted clamped effects, withhold-event
  ordering-before-needs. Strong (much of this freshly inspected).
- **player-identity_spec** — capture/defaults/blank-fallback/persistence/round-trip + prompt
  threading (city/player/title present, "Mayor" absent). Strong.
- **break resolution (cycle-runner)** — forced level-drop / leader-death / level-1 reprieve /
  health-reset-75 / 75-25 split over 3000 trials. Strong.

## Recommendation for the walkthrough list
Add **one focused task: harden `test_cycle.py`.** Replace the three vacuous asserts and add the
four missing orchestration checks (initiative re-roll + full membership, faction_actions excludes
Skip, treasury-step-before-loop with results present, build-counter reset via `run_cycle`,
utilization = Σ level). This single file is where nearly all the audited gaps live; everything
else is solidly proven.
