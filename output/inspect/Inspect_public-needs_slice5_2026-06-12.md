# Inspection Report — public-needs, Slice 5 (Cycle integration + live plumbing)

**Date:** 2026-06-12
**Inspector:** fresh-eyes subagent (ran everything independently; trusted nothing claimed)
**Blueprint:** `Planning/blueprints/public-needs_BP.md` — Slice 5 `[inspect]`
**Spec:** `Planning/specs/public-needs_spec.md` (feature "Cycle integration" — slice 5 items only;
event gating and audience prompt items belong to Slice 6 / Final Slice and were not judged)

**Verdict: PASS (5/5 items), with one test-fidelity concern recorded below.**

---

## Item 1 — Needs step runs inside run_cycle, after the action loop, before event processing: PASS

Code (`backend/engine/cycle/runner.py`): the "Item 5b" block (lines 140–144) executes
`compute_chain` + `apply_needs` after `run_sequential_actions` (line 123) and `tick_deals`
(line 138), and before `process_active_events` (line 147) and `roll_for_random_events`
(line 170). Ordering matches the spec's "after state updates, before active/new event
processing."

Command: `py -m pytest tests/test_needs_cycle.py -v`

```
tests/test_needs_cycle.py::TestNeedsStepRuns::test_fed_moves_toward_chain_target PASSED
tests/test_needs_cycle.py::TestNeedsStepRuns::test_without_public_nothing_breaks PASSED
5 passed in 0.07s
```

The first test proves the needs step actually mutated `public.fed` toward the chain target
during a full `run_cycle`; the second proves `public=None` callers are unaffected.

## Item 2 — toiling reset + committed Toil affects the chain same-cycle: PASS (behavior), test weaker than claimed

Code: reset loop at runner.py lines 192–195 (`f.toiling = False` for all factions, just before
`CycleResult` is built — after the needs step consumed the flags, comment cites
cycle-runner_spec).

Command: `py -m pytest tests/test_needs_cycle.py -v`

```
tests/test_needs_cycle.py::TestToilingReset::test_flags_false_after_run_cycle_and_boost_consumed PASSED
```

The reset half is solidly encoded: `assert all(f.toiling is False ...)` runs in both the toil
and control runs.

**Fidelity concern — the "boost consumed" half of this test is vacuous.** The fixture starts
`fed=0` and asserts `results["toil"] >= results["control"]`. With both chain targets far above
`DRIFT_STEP=10`, both runs drift exactly 0→10, so the assertion compares 10 >= 10 and would
pass even if the Toil boost never reached the chain. Verified by direct drive:

```
start_fed=0:  toil fed=10, control fed=10    <- the committed fixture: indistinguishable
start_fed=50: toil fed=60, control fed=50    <- inspector probe: boost IS measurable
```

The `start_fed=50` probe (same seed 42, same committed-Toil setup as the test) proves the
behavior itself is correct — a committed Toil raises the chain target the same cycle and fed
drifts further. So the **behavior passes by direct inspection**, but the committed test does
not encode the blueprint's own test description ("fed target higher than a no-Toil control
run"). Recommended fix (small): start the fixture at `fed=50` and assert strictly `>`.

Note: the spec's slice-5-scope `[automated]` item is only "`Faction.toiling` is always false
for every faction after `run_cycle` returns" — that IS properly encoded. The stronger
"Toil matters" dynamics item belongs to the Final Slice. Hence PASS with concern, not FAIL.

## Item 3 — Snapshot round-trip; absent key → None; restore substitutes loader defaults: PASS

Command: `py -m pytest tests/test_needs_cycle.py -v`

```
tests/test_needs_cycle.py::TestSnapshotRoundTrip::test_public_survives_serialize_state PASSED
tests/test_needs_cycle.py::TestSnapshotRoundTrip::test_snapshot_without_public_restores_none PASSED
```

The round-trip test goes through a real `json.dumps`/`json.loads` and checks all five fields
(support 5, health 77, population 23456, fed 41, happy 66) survive. Absent `the_public` key →
`deserialize_state` returns `None` (serializer.py line 461). Restore substitution confirmed in
code: `api/routes/sim.py` `_restore_session` lines 70–71 — `if public is None: public =
load_the_public()` — same pattern as the pre-existing mayor/treasury back-compat defaults.

## Item 4 — Live paths pass the public (headless + API): PASS

Command: `py main.py --cycles 5 --seed 11` (from `H:\Polis\backend`) — completed, summary line
present:

```
  THE PUBLIC: pop=20,000 fed=50 (Fed) happy=66 (Content) health=100
```

`main.py` builds `public = load_the_public(...)` and `chains = load_chains(...)` and passes
both into every `run_cycle` call (lines 78–79, 101–103); `print_summary` prints the line
(lines 31–35). `data/world_state.json` carries the `special_factions.the_public` block
(support 0, health 100, population 20000, fed 60, happy 50) as specified.

API (`api/routes/sim.py`, read directly):
- `start_sim`: `public = load_the_public()` (line 199), stored on `SimSession`, passed to the
  cycle-0 `_save_cycle` (lines 237–239).
- `step_sim`: `run_cycle(..., public=session.public, chains=_CHAINS)` (lines 292–295);
  `_save_cycle(..., public=session.public)` (lines 299–302).
- `run_n`: same pair (lines 351–354, 358–361).
- `_save_cycle` forwards `public=` into `serialize_state` (line 120). `_CHAINS` loaded once at
  module level (line 27).

## Item 5 — Full suite green: PASS

Command: `py -m pytest tests/ -q`

```
419 passed in 1.34s
```

---

## Deviation notes under Slice 5 — judged how-not-what: CONFIRMED

1. *Step 1: `chains` defaults to `[]` in `run_cycle`, no implicit loader call.* How-not-what —
   the blueprint's own step text demanded "do NOT file-read inside the engine," and all live
   callers pass chains explicitly; behavior identical for every real path.
2. *Step 2: reset at end of `run_cycle`, not `end_of_cycle.py`.* How-not-what — the blueprint
   step text itself corrected the placement mid-step; the observable contract (toiling false
   after `run_cycle` returns, consumed after the needs step) is exactly what the spec states.
3. *Step 3: `start_sim` uses `load_the_public()` engine defaults rather than the city template;
   `_CHAINS` at module level.* How-not-what for slice 5's claims — no slice-5 Done-when
   requires per-city public state; the gap is honestly attributed to city-generation. Worth
   remembering when city templates gain a `the_public` block.

Minor unrecorded deviation (cosmetic): blueprint wrote loader signatures as
`load_the_public(data_dir="data")`; as built they take a file `path` with module-level
defaults (`loaders.py` lines 206, 215). Pure how; callers all consistent.

---

## Sign-off

Slice 5 PASS. One follow-up recommended (not blocking): strengthen
`TestToilingReset` — start the fixture at `fed=50` and assert strict `>` so the
boost-consumed claim is actually encoded rather than vacuously satisfied.
