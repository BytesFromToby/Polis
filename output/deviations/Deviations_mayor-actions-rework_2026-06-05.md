# Deviations — Mayor Actions Rework
Blueprint: Planning/blueprints/mayor-actions-rework_BP.md
Date: 2026-06-05

| Slice | Step | Deviation | Why |
|-------|------|-----------|-----|
| 1 | 1 | Pulled the `Sabotage` AP-cost entry (`"Sabotage": 1`) and `SABOTAGE_GOLD = 50` constant forward into Slice 1's `ACTION_COSTS` rewrite, rather than adding them in Slice 2. | Rewrote `actions.py` whole in Slice 1; adding the constant then avoided a second edit. No behavior — the resolver and `_ACTION_MAP` entry still landed in Slice 2. |
| 1 | 2 | Added `Sabotage` and `BuildProject` to `VALID_MAYOR_ACTIONS` in Slice 1 (blueprint deferred them to Slices 2–3). | We ran straight through all slices, so the intermediate allowlist is never separately inspected. Made `TestRosterIntegrity::test_valid_actions_is_exact_demo_set` go green at end of Slice 1 instead of Slice 3 — anticipated by the blueprint as acceptable. |
| 1 | 3 | Also removed `test_two_ap_action_spends_two` (TestAPSpending). | It exercised `BrokerADeal` (a cut action), and no 2-AP action remains in the demo roster, so the test is unrunnable and meaningless. Covered by the blueprint's intent to drop tests for cut actions. |
| 2 | 1 | Used the real faction field name `rating` (not the blueprint's `target.rank`) and halved health with integer floor (`health -= health // 2`) rather than `health - 0.50*health`. | `Faction.rating` is the actual rank field (`level = int(rating)`); `health` is an `int`. Same observable behavior (3.50→3.25, 100→50, 50→25), never reaches 0. |
| 3 | 1 | Briefly dropped, then restored, the engine `commission_project` export in `engine/projects/__init__.py`. | The **engine** function is still used by `tests/test_projects.py`; only the **API endpoint** of the same name is retired. Net: no change to the engine export. |
| 3 | 2 | Simplified the now-dead two-target composite-target logic in `mayor_act` (`BrokerADeal`/`PlantARumor` branch) to `target_id = req.target_id`. | Both actions that used a second target are cut; the branch was dead code. |
| 3 | 4 | Added an affordability pre-check in `mayor_build_or_repair` so a refused build (insufficient AP/gold) initiates **no** project. | `mayor_build_base` initiates first, then funds — a failed fund left an unpaid phantom `under_construction` site that would block the one-per-domain rule. The guard makes "refused" mean nothing happens, matching the spec's "deducts nothing" intent. Contained to the new consolidation function; `mayor_build_base` unchanged. |

## Outcome
- Full suite: **316 passed** (318 baseline − 15 cut-action tests + 14 new: Sabotage ×7, Build ×5, Roster ×2 — and treasury-runs ×1, minus net). Headless `py main.py --cycles 10`: exit 0, clean.
- All 15 `[automated]` spec Done-when items backed by committed tests; both `[human-required]` items evidenced (treasury controls absent from `VALID_MAYOR_ACTIONS`; only historical entrench/Block/collapse notes remain in the spec).
