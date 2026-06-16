# Deviations — Piety + Unrest

Blueprint: Planning/blueprints/piety-unrest_BP.md
Date: 2026-06-16

| Slice | Step | Deviation | Why |
|-------|------|-----------|-----|
| 1 | 5 | Crisis-blame scales only the **negative** component of the combined fed+happy support delta (positive deltas pass through unscaled), via a sign-split before applying. | Matches the spec ("negative support deltas"); the clean seam is to split `neg`/`pos` before routing through the mayor/public path. |
| 1 | — | Both `piety` *and* `unrest` fields + serialization added in Slice 1 (not split across slices). | One serialization change is cleaner than two; unrest behavior still lands in Slice 2. |
| 2 | 3 | `guard_paid` surfaced as `Treasury.guard_paid_this_cycle`, set in `process_treasury_step0` (`paid >= guard_cost`), read by the runner and passed to `apply_needs`. | The payroll already ran by item 5b; a flag is the clean seam (blueprint's "Stuck if" anticipated this). |
| Final | 1 | Public-targeted effects clamp `support` to a **−50** floor (other fields to 0); skipped silently when `public is None`. | `support` is the only −50..+50 scale; the rest are 0..100. None-safety keeps every other `process_active_events` caller working. |
| Final | 3 | **The Mob Marches** chaos effect targets a fixed domain (`guilds`) and reuses the existing `chaos` effect path; the riot's bite is chaos + Public `health` (re-specced earlier, away from project-progress damage). | Avoids new project-effect machinery; reuses what exists. Public-health uses the new public-targeted effect. |

**Capability added:** events can finally touch `ThePublic` (fields piety/unrest/support/fed/happy/
health) — the long-standing gap noted in the roadmap. `process_active_events` now threads `public`.

**Tests:** `test_piety.py` (14), `test_unrest.py` (10), `test_public_scale_events.py` (9) = 33 new.
Result: full suite **507 green** (474 → 488 → 498 → 507); headless `main.py --cycles 10` clean.
