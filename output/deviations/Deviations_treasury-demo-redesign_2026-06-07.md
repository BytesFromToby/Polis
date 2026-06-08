# Deviations — Treasury Demo Redesign (v3)
Blueprint: Planning/blueprints/treasury-demo-redesign_BP.md
Date: 2026-06-07

| Slice | Step | Deviation | Why |
|-------|------|-----------|-----|
| 1 | 2 | 6 existing tests failed as expected income-model fallout; reconciled to v3 in Step 3 | Old auto-tax assertions + flat-base shifting "broke" scenarios (test_mayor.py income/guard/investment + integration, test_projects_cap maintenance). Confirmed not regressions. |
| 1 | 3 | Reworded `test_guard_payroll_skipped_if_broke` → `test_guard_payroll_paid_from_base_income` | Under flat +20 base income, guard (20) is always covered at gold 0; the old "skipped when broke" scenario is unreachable. |
| 2 | 4 | Also updated 4 theme-data tests (test_theme_data.py ×3, test_seed_official.py ×1) | Adding the `civic` domain makes 9 domains; tests hardcoded "exactly 8 Greek domains". Updated to check the 8 Greek faction domains explicitly + civic as the faction-less lane. |
| 3 | 1 | No 3-cycle bankruptcy ladder existed in code to remove | v2 only ever did per-line "skip when broke"; reworked that to charge-in-full + clamp-at-0 + insolvency damage. |
| 3 | 2 | Renamed/rewrote 2 maintenance-broke tests to the insolvency model | `test_projects.py` and `test_projects_cap.py` asserted the old ProjectMaintenance "fail" outcome, which v3 replaces with the Insolvency result. |
| Final | — | Refreshed the official Polis template row in polis.db to include `civic` | seed_official_cities skips existing rows and /city/load copies the template verbatim; without this, new demo games would lack the civic domain. Same class of data fix as the earlier cap-freeze refresh. |

No source-behaviour deviations from the blueprint's intent — all of the above are test reconciliations to the v3 model plus the template data refresh.
