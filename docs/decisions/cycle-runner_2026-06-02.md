# Decisions: Cycle Runner — Done-when retrofit
Spec: Planning/specs/cycle-runner_spec.md
Date: 2026-06-02

Context: acting on the 2026-06-02 walkthrough's HIGH recommendation — the engine specs predating
the Plumbline alignment carry no tagged acceptance criteria. This adds them to cycle-runner, the
first (entry-point) spec. No behavior changed; only criteria were added.

## Decisions

- **Criteria scoped to runner-owned orchestration only.** Done-when items cover what `run_cycle`
  itself guarantees — cycle completion + result contract, the cycle counter, initiative selection,
  block-check mechanics, the `build_actions_this_cycle` reset, domain-utilization recalculation,
  and block-log visibility. Subsystem behavior (treasury math, trait evolution, chaos, collapse,
  events, project completion, Mayor ticking) was **deliberately not given Done-when here** — those
  belong to their own specs (treasury, faction-behavior, events, projects, mayor). Rejected the
  alternative of restating subsystem criteria in the runner spec: it would duplicate contracts and
  drift. The runner's contract is only that those subsystems *run, in order, once per cycle*.

- **Did not restructure the spec into `## Feature:` blocks.** The retrofit was kept minimally
  invasive — Done-when blocks were attached to the existing Step/section structure. Converting the
  step-based spec to feature blocks would be a redesign, which was explicitly out of scope.

- **All 14 criteria tagged `[automated]`** — each is machine-checkable. Tagging them automated
  (rather than leaving them untyped) is what lets `surveyor`/`foreman`/`inspector` see the
  test-backing gaps below as actionable, instead of hiding them.

## Criterion → test mapping (as of this retrofit)

**Backed by an existing test:**
- Treasury present/absent path → `test_cycle.py` (absent) + `test_mayor.py` (present)
- Block decisive / partial / fail / consumed → `test_actions.py` (+ `test_harm_block_steal.py`)
- `world.cycle` +1 per call → `test_cycle.py::test_cycle_increments_world_cycle`
- N cycles → `world.cycle == N` → `test_cycle.py::test_multiple_cycles_run`
- `CycleResult` contract (events list, faction_actions ≥ 0) → `test_cycle.py::test_result_has_events`,
  `test_faction_actions_counted` (Skip-exclusion partially via `test_npc_and_eoc.py`)

**No backing test yet (the gaps this retrofit surfaces — for `foreman`/`builder`):**
1. Initiative excludes `destroyed` factions
2. Initiative is re-rolled each cycle (no persistent order)
3. Two blocks on the same target → only the first in initiative order fires; the other stays armed
4. `build_actions_this_cycle` is reset to 0 after project ticking
5. Block public-log entry names no target; target revealed only when the block fires

**Weak (exists but under-asserts):**
- Domain-utilization recalculation — `test_domain_utilization_recalculated` only asserts `>= 0`,
  not that the value is recomputed from current weights. Worth strengthening.

## Next
Run `foreman` on this spec to plan committed tests for the 5 gaps (and the weak one), then
`builder` to write them, then `inspector` to stamp the spec proven.
