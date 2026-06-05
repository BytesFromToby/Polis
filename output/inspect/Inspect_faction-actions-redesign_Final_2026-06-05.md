# Inspect Report — Faction + Actions Redesign · Final
Spec: Planning/specs/actions_spec.md (v5) · Planning/specs/cycle-runner_spec.md (v1.3) · Planning/specs/faction-behavior_spec.md (v4)
Blueprint: Planning/blueprints/faction-actions-redesign_BP.md
Date: 2026-06-05
Run/demo command: `cd backend && py -m pytest tests/ -q` · `cd backend && py main.py --cycles 10`

Summary: **24 passed · 2 failed · 0 need human sign-off**
(actions_spec: 15/15 pass · cycle-runner_spec: 9/11 pass · faction-behavior_spec: no Done-when items)

Full suite: **280 passed**. Headless `--cycles 10`: clean, level-ups fire, no faction removed.

---

## Results — actions_spec v5 (all PASS)

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Grow increases rank by 1/(level+1) | PASS | test_actions.py::TestResolveGrow::test_grows_by_one_over_level_plus_one |
| Crossing an integer raises level +1 with a Dramatic event | PASS | ::test_crossing_integer_levels_up_dramatically |
| Grow gives no gain when utilization ≥ cap | PASS | ::test_blocked_when_domain_full |
| rank never exceeds 10.0 | PASS | ::test_rank_never_exceeds_10, ::test_blocked_at_max |
| Protect raises health +50, cap 100 | PASS | TestResolveProtect::test_heals_self_50, ::test_capped_at_100 |
| Aid raises target health +25, cap 100 | PASS | TestResolveAid::test_heals_target_25, ::test_capped_at_100 |
| Aid only targets allies; may cross domains | PASS | cross-domain: TestResolveAid::test_allowed_across_domains; ally-only selection: test_npc_and_eoc.py::TestBehaviorRedesign::test_aid_picks_lowest_health_ally |
| Harm decisive −30 / partial −15 / fail 0 | PASS | TestResolveHarm::test_decisive_reduces_health_30, ::test_partial_reduces_health_15, ::test_fail_leaves_health_unchanged |
| Harm health floors at 0 | PASS | ::test_health_floors_at_0 |
| Harm cannot target level-1 | PASS | ::test_cannot_target_level_1 + behavior ::test_aggression_never_targets_level_1 |
| Harm same-domain only | PASS | ::test_blocked_across_domains |
| Steal decisive transfers 0.5/(atk_level+1); partial half | PASS | TestResolveSteal::test_decisive_transfers_full_amount, ::test_partial_transfers_half |
| Steal target rank ≥1.0, actor rank ≤10.0 | PASS | ::test_target_rank_never_below_1, ::test_actor_rank_never_exceeds_10 |
| Steal cannot target level-1 | PASS | ::test_cannot_target_level_1 |
| Steal same-domain only | PASS | ::test_blocked_across_domains |

## Results — cycle-runner_spec v1.3

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Treasury step runs when mayor+treasury provided; skipped when absent, still completes | PASS | absent: test_cycle.py::test_cycle_completes; provided: test_special_factions.py::test_public_processed_each_cycle, test_events_system.py::test_active_events_processed_each_cycle |
| Every faction placed in initiative_order each cycle | PASS (no committed test — verified directly) | direct run: `sorted(initiative_order)==faction keys` → True. **Gap: no pinned test.** |
| initiative_order re-rolled each cycle, no carryover | PASS (no committed test — verified directly) | direct run: 6 distinct orders over 20 cycles (3 factions = all 6 perms). **Gap: no pinned test.** |
| Each faction resolves one action per turn; effects live before next acts | PASS | test_cycle.py::test_faction_actions_counted; sequential-live design in resolution.py |
| Action bringing health to 0 triggers a Break that same turn | PASS | code path in resolution.run_sequential_actions (`resolve_break` on `health <= 0`); Break unit-tested in test_break.py. **Gap: no committed integration test of the in-loop trigger.** |
| **After project ticking, every project's build_actions_this_cycle is 0** | **FAIL** | Nothing in the engine resets it (only incremented in actions/faction.py:164). Direct check: counter stays 2 after `tick_projects`. **Pre-existing** (absent at HEAD~2; not changed by this redesign). No backing test. |
| Health reaches 0 → reset to 75, faction never removed | PASS | test_break.py::test_resets_health_to_75, ::test_faction_survives_break |
| **Break: one consequence; level-drop sets rank=(level−1).0; leader-death installs a `weakened` leader** | **FAIL (partial)** | level-drop + one-consequence PASS (test_break.py::test_forced_level_drop); leader-death installs `status="present"`, not `"weakened"` (::test_forced_leader_death_regenerates). Documented intentional deviation — spec text not yet reconciled. |
| Level-1 faction Break keeps level==1 | PASS | test_break.py::test_level_1_reprieve |
| Over many forced Breaks the split ≈75/25 | PASS | test_break.py::test_split_is_roughly_75_25 (3000 trials, 0.21<frac<0.29) |
| world.cycle +1 per call; N calls → cycle==N; utilization=Σ level; CycleResult shape + faction_actions excludes Skip | PASS | test_cycle.py::test_cycle_increments_world_cycle, ::test_multiple_cycles_run, ::test_domain_utilization_recalculated; direct check: util==Σ level (8==8), CycleResult/CycleEvent shape OK, faction_actions non-negative excluding Skip. **Gap: Σ-level value and Skip-exclusion only weakly asserted by committed tests.** |

---

## Failures

1. **build_actions_this_cycle is never reset** (cycle-runner_spec "Done when" §3 / line 135).
   Expected: 0 after project ticking. Observed: retains its incremented value (verified 2→2 after `tick_projects`). No reset logic exists anywhere in `engine/`. **Pre-existing** — also absent at `HEAD~2`, not introduced or touched by this redesign (projects are a parked subsystem). Impact: `Project.defense_bonus()` (capped +2) would not clear between cycles. Route to builder/foreman as a projects-area fix, or carry as known debt until the projects rework.

2. **Break leader-death installs a `present` leader, not `weakened`** (cycle-runner_spec line 114).
   Expected (spec text): new leader `weakened` for one cycle. Observed: `status="present"`. This is a deliberate, documented deviation (the existing `weakened`→`absent` leadership escalation would turn the recovery window into a leadership crisis — see Deviations_faction-actions-redesign_2026-06-05.md §2). The *behavior* is sound; the **spec Done-when wording is stale**. Recommend an `architect` pass to update cycle-runner_spec line 114 to `present` (preferred), rather than changing code.

---

## Coverage gaps (foreman/builder misses — `[automated]` items with no/weak pinned test)

These were verified directly by inspector this once, but lack a committed regression test:
- initiative_order covers all factions each cycle
- initiative_order re-rolled each cycle (no carryover)
- in-loop Break trigger (integration, as opposed to the `resolve_break` unit)
- utilization == Σ level (committed test only asserts ≥ 0)
- faction_actions excludes Skip (committed test only asserts ≥ 0)
- build_actions_this_cycle reset (and it currently fails — see Failures)

---

## Verdict

The **faction + actions redesign itself is fully verified** — all 15 actions_spec criteria and all behavior assertions pass, suite is 280-green, headless run clean. Sign-off is held by two cycle-runner_spec items: one stale spec wording (weakened→present, needs an architect edit) and one pre-existing, out-of-scope projects defect (build_actions reset). Neither is a flaw in the code built in this pass. Recommend: reconcile the spec line, file the build_actions reset for the projects rework, and add pinned tests for the listed gaps.
