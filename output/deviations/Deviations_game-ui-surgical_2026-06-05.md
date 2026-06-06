# Deviations — Game UI Surgical Correctness Pass
Blueprint: Planning/blueprints/game-ui-surgical_BP.md
Date: 2026-06-05

| Slice | Step | Deviation | Why |
|-------|------|-----------|-----|
| 1 | 1–3 | Rewrote `MayorActionsModal.vue` wholesale instead of editing rows in place. | The three Slice-1 steps (remove 8 rows, regroup, add 2 rows + gold) all reshape the same template/script region; one coherent rewrite was cleaner than piecemeal edits. Same observable result — verified by grep + build. |
| 2 | 3 | `onActed` now also refreshes the treasury (`treasuryApi.get`), not just mayor data. | The step explicitly required ensuring `onActed` refreshes treasury so the modal's gold prop reflects Sabotage/Build spends; it previously refreshed only mayorData. Implements the step. |
| 2 | 2 | Also relabelled the standalone audience picker header "Meet with…" → "Request audience with…". | Copy-only consistency with the relabelled button; beyond the literal step (button text), same behavior. |
| 3 | 1 | Replaced the **Rating** column header with **Level** and the **Entrench** column with **Health** (column count stays 5), and fixed a pre-existing `colspan="6"`→`5` on the "No factions" row. | The blueprint asked to drop entrench, lead with integer level, and keep health visible; swapping the two existing columns achieved all three without changing the table width. The colspan was already mismatched (6 vs 5 columns). |

## Outcome
- `py tools/check_game_ui.py`: **OK** (all 6 source invariants — modal roster + gold, GameView integer level + Request Audience + no MeetWithFaction, Dashboard no entrench + integer level, api.js no commission).
- `cd frontend && npm run build`: **exit 0**.
- Backend regression: `py -m pytest tests/ -q` → **316 passed** (frontend changes touched no backend behavior).
- All 7 `[automated]` Done-when items pinned (check script + build); 20 `[human-required]` items staged for inspector's Playwright pass.
