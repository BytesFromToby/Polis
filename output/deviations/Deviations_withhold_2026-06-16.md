# Deviations — Withhold

Blueprint: Planning/blueprints/withhold_BP.md
Date: 2026-06-16

| Slice | Step | Deviation | Why |
|-------|------|-----------|-----|
| 1 | 5–6 | The behavior entry point is `select_faction_action`, not `decide_action` (the blueprint's informal name). `mayor` plumbed through it + `run_sequential_actions` + `run_cycle`. | Naming only; the plumbing path is exactly as planned. |
| 1 | 7 | `withholding` reset lives in the runner's end-of-cycle loop next to `toiling` (not in `Faction.reset_cycle_state`, which only handles `unstable_stacks`). | Mirrors exactly how `toiling` is already reset — same site, same timing. |
| Final | — | **Spec correction made mid-build:** the events_spec / public-needs Done-when originally read "force-withholding *two* Food sources → Starving." Corrected to "*one* source → never Starving; *all* sources → Starving," matching the actual 3-source redundancy the shipped removal tests encode (`test_aristocracy_gone` = barley+flocks = two sources = **Hungry**; only all-three = Starving). | The "two → Starving" figure was a stale carry-over from the 2-source (fish-era) goal. Aligned spec + test to the real property rather than coding to a wrong number. |
| Final | 2 | Only `process_active_events` moved before the needs step; `roll_for_random_events` left after it (verified the two are separate calls). | This is the whole point of the split — effects felt this cycle, rolls still see this cycle's bands. The ordering test pins both halves. |

**Tests added:** `tests/test_withhold.py` (11 — resolver, chain ×0 incl. Withhold-beats-Toil,
anger weights, committed, Withhold-matters integration) + `tests/test_withhold_events.py` (7 —
event sets flag, resolves, felt-same-cycle, recovery, redundancy one/all, gate-sees-post-needs-band).

Result: full suite **474 green** (456 → 467 after Slice 1 → 474 after Final); headless
`main.py --cycles 8` survives. Cycle reorder is needs-neutral for non-withhold effects (the entire
prior event/cascade suite still passes unchanged).
