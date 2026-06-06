# Blueprint: Game UI — Surgical Correctness Pass
Spec: Planning/specs/game-ui_spec.md
Date: 2026-06-05

---

## Builder instructions
- Execute steps in order. Do not skip, reorder, or read ahead into the next slice.
- Check off each step when complete: [ ] → [x]
- One step = one logical concern. If a step can't be tested on its own, it's too small — merge it. If it touches more than one concern, split it.
- Deviation: if you do something differently than the step says, note it inline and keep going.
- Stuck: stop immediately. Do not try alternative approaches. Report exactly where and why.

### Context the builder needs
- **Stack:** Vue 3, Options API, Vite. **No JS test runner** in the project — the `[automated]` Done-when items are pinned as (a) a committed Python source-assertion script `tools/check_game_ui.py` written in the Final slice, and (b) `npm run build` exit 0. Per-slice **Test** lines use inline greps for immediate feedback; the Final slice consolidates them into the committed script.
- **Build:** `cd frontend && npm run build` (must exit 0; rebuild after `.vue`/`.js` changes). Repo root is `H:\Polis`; `tools/` is at the root; frontend source is `frontend/src/`.
- **Dispatch:** all Mayor actions go through the existing generic `mayor.act(userId, action, targetId, targetId2, cycles)` → `POST /mayor/act`. Sabotage = `act('Sabotage', factionId)`; Build Project = `act('BuildProject', domainId)`. No new api.js functions needed.
- **Existing modal mechanics (keep):** the `doAct(action, targetId, targetId2, cycles)` method, the result/error banner, the Active Deals/Break section, and the `targetFaction` / `targetDomain` / `exemptFaction` / `exemptCycles` selects.
- **GameView modal binding** (≈ line 166): `<MayorActionsModal :factions :domains :mayor-data @close @acted />` — a `:gold` prop is added in Slice 2. `treas.gold` is the gold source; `onActed` is the post-action refresh hook.

---

## Slice 1: Mayor Actions Modal — demo roster + gold
**Scope:** `MayorActionsModal` shows exactly the demo levers (Endorse, Condemn, Grant Tax Exemption, Sabotage, Build Project, Break), none of the eight removed actions, with gold in the header.

### Step 1: Remove the eight cut-action rows and their dead state
**Build:** In `frontend/src/components/MayorActionsModal.vue`, delete the action rows for Broker a Deal, Request a Report, Plant a Rumor, Allocate Budget, Withhold Resources, Issue a Decree, Appoint an Official, Turn a Blind Eye. Remove the now-dead `data()` fields (`brokerA`, `brokerB`, `rumorTarget`, `rumorAbout`) and the `leaderlessFactions` computed. Keep `targetFaction`, `targetDomain`, `exemptFaction`, `exemptCycles`, `doAct`, the result/error banner, and the Active Deals/Break section.
**Test:** `grep -nE "BrokerADeal|RequestAReport|PlantARumor|AllocateBudget|WithholdResources|IssueADecree|AppointAnOfficial|TurnABlindEye" frontend/src/components/MayorActionsModal.vue` → no matches.
**Done When:** None of the eight removed action strings appear in the file.
**Stuck If:** A removed `data()` field or computed is still referenced by a kept row.
- [x] Complete

### Step 2: Add Sabotage and Build Project rows in an Economic group
**Build:** Regroup the modal into **Political** (Endorse, Condemn), **Economic** (Grant Tax Exemption, then the two new rows), **Deals** (existing Active Deals/Break). Add:
- **Sabotage** row — `targetFaction` select; hint `rank −50% of margin, health −50%, rep −10 · 1 AP + 50 gold`; Act button `:disabled="ap < 1 || gold < 50 || busy"`, `@click="doAct('Sabotage', targetFaction)"`.
- **Build Project** row — `targetDomain` select; hint `Break ground / fund a unit (50g) or repair (+25 health, 30g) · 1 AP`; Act button `:disabled="ap < 1 || busy"`, `@click="doAct('BuildProject', targetDomain)"`.
Remove the old Information/Authority/Resource group labels; use Political/Economic/Deals.
**Test:** `grep -nE "doAct\('Sabotage'|doAct\(\"Sabotage|Sabotage|BuildProject" frontend/src/components/MayorActionsModal.vue` shows both Sabotage and BuildProject dispatch.
**Done When:** The file contains a Sabotage row dispatching `act('Sabotage', targetFaction)` and a Build Project row dispatching `act('BuildProject', targetDomain)`, grouped under Economic.
**Stuck If:** `doAct`'s signature can't carry these calls as-is (it can: `doAct(action, targetId)`).
- [x] Complete

### Step 3: Add the gold prop and show it in the header
**Build:** Add `gold: { type: Number, default: 0 }` to `props`. In the header, next to the AP badge, render a gold badge (e.g. `{{ gold }} gold`). The Sabotage row's disabled binding already reads `gold`.
**Test:** `grep -nE "gold" frontend/src/components/MayorActionsModal.vue` shows the prop declaration and a header reference; `cd frontend && npm run build` exits 0.
**Done When:** `gold` is a declared prop, appears in the modal header, and the project builds.
**Stuck If:** `npm run build` fails with a template/compile error in the modal.
- [x] Complete

---
⛔ End of Slice 1. Run **inspector** on this slice before continuing.

---

## Slice 2: GameView — readout, relabel, gold pass-through
**Scope:** The faction blocks lead with integer level, the standalone button reads "Request Audience", and the modal receives gold.

### Step 1: Lead the faction block with integer level
**Build:** In `frontend/src/views/GameView.vue` (faction block ≈ line 49), change the primary readout from `{{ f.rating.toFixed(1) }}` to the integer level `Lv {{ Math.floor(f.rating) }}`. Keep the precise `rating` only as a small/parenthetical secondary (e.g. a muted `({{ f.rating.toFixed(1) }})`), not the lead number. The rating bar (fill/colour) stays.
**Test:** `grep -nE "Math.floor\(f.rating\)|Lv " frontend/src/views/GameView.vue` shows the integer-level readout.
**Done When:** The faction block leads with `int(rating)` as "Lv N"; the multi-decimal value is absent or visibly secondary.
**Stuck If:** `f.rating` is not present on the faction object in the snapshot (it is — verify).
- [x] Complete

### Step 2: Relabel the standalone audience button
**Build:** At ≈ line 75, change the button text `Meet with Faction ▸` to `Request Audience ▸`. Leave its `@click="openStandaloneAudience"` handler unchanged. Confirm no element dispatches the deterministic `MeetWithFaction` action anywhere in the file.
**Test:** `grep -n "Request Audience" frontend/src/views/GameView.vue` matches; `grep -rn "MeetWithFaction" frontend/src/` → no matches.
**Done When:** The button reads "Request Audience ▸" and no UI source dispatches `MeetWithFaction`.
**Stuck If:** A second control also references the old label/handler unexpectedly.
- [x] Complete

### Step 3: Pass gold into the actions modal
**Build:** On the `<MayorActionsModal ...>` tag (≈ line 166), add `:gold="treas?.gold ?? 0"`. Ensure the post-action hook `onActed` refreshes the treasury (re-fetch or update `treas`) so the modal's gold reflects spends from Sabotage/Build; if `onActed` already refreshes full state/treasury, no change needed — confirm it does.
**Test:** `grep -n ":gold" frontend/src/views/GameView.vue` matches the modal binding; `cd frontend && npm run build` exits 0.
**Done When:** The modal receives `:gold`, and after an action the displayed gold updates (treasury refreshed in `onActed`).
**Stuck If:** `onActed` does not refresh treasury and there's no obvious treasury-refresh call to reuse.
- [x] Complete

---
⛔ End of Slice 2. Run **inspector** on this slice before continuing.

---

## Slice 3: DashboardView + api.js cleanup
**Scope:** The dashboard table drops the dead entrench column and leads with integer level; the dead `commission()` API call is gone.

### Step 1: Remove the entrench column and lead with integer level
**Build:** In `frontend/src/views/DashboardView.vue`: delete the entrench `<td>` (≈ line 162) and its matching `<th>`/header cell; delete the `entrenchClass()` method (≈ line 372). Change the rating cell (≈ line 161) from `{{ f.rating.toFixed(2) }}` to the integer level `{{ Math.floor(f.rating) }}`. Ensure `health` is shown for each faction (add a column if the table doesn't already have one). Fix the `colspan` on the "No factions" row to match the new column count.
**Test:** `grep -nE "entrench|entrenchClass" frontend/src/views/DashboardView.vue` → no matches; `grep -n "Math.floor\(f.rating\)" frontend/src/views/DashboardView.vue` matches.
**Done When:** No `entrench`/`entrenchClass` remains; the faction row shows integer level and health; colspan matches the column count.
**Stuck If:** The table header/column structure is ambiguous enough that the right colspan/health placement isn't clear from the file.
- [x] Complete

### Step 2: Remove the dead commission() API call
**Build:** In `frontend/src/api.js`, delete the `commission:` function (≈ line 160) that posts to `/projects/commission`. Verify nothing imports/calls it (`grep`).
**Test:** `grep -rnE "commission|projects/commission" frontend/src/` → no matches.
**Done When:** No `commission` function or `/projects/commission` reference remains in `frontend/src/`.
**Stuck If:** A component still calls `api...commission(...)`.
- [x] Complete

### Step 3: Build after cleanup
**Build:** None.
**Test:** `cd frontend && npm run build`.
**Done When:** Build exits 0.
**Stuck If:** A removed symbol is still referenced (build error names it).
- [x] Complete

---
⛔ End of Slice 3. Run **inspector** on this slice before continuing.

---

## Final Slice: Pin the automated checks + full verification
**Scope:** A committed source-assertion script encodes the automated invariants; build is green; human-required items staged for inspector.

### Step 1: Write the committed check script
**Build:** Create `tools/check_game_ui.py` (pure Python, no deps) that reads the frontend source files and asserts, exiting non-zero with a clear message on any failure:
1. `MayorActionsModal.vue` contains `Sabotage` and `BuildProject`, and **none** of the eight removed action strings (BrokerADeal, RequestAReport, PlantARumor, AllocateBudget, WithholdResources, IssueADecree, AppointAnOfficial, TurnABlindEye).
2. `MayorActionsModal.vue` declares a `gold` prop and references `gold` in its header.
3. `GameView.vue` contains `Request Audience` and `Math.floor(f.rating)`, and `frontend/src/` contains no `MeetWithFaction`.
4. `DashboardView.vue` contains no `entrench` and no `entrenchClass`, and contains `Math.floor(f.rating)`.
5. `api.js` contains no `commission` and no `projects/commission`.
Print `OK` and exit 0 when all pass.
**Test:** `py tools/check_game_ui.py` → prints OK, exit 0.
**Done When:** The script passes against the current tree and fails (non-zero) if any invariant is violated (spot-check by reasoning, not by breaking the tree).
**Stuck If:** A path differs from the assumed `frontend/src/...` layout.
- [x] Complete

### Final Step: Verify spec Done when items
**Build:** No new code. Confirm all `**Done when:**` items in `game-ui_spec.md` are met. The 7 `[automated]` items map to: `tools/check_game_ui.py` (the 6 source invariants across the modal/GameView/Dashboard/api.js) + `npm run build` exit 0. The 20 `[human-required]` items are layout/feel/affordability — inspector captures Playwright screenshots of the running app (dev server: `cd backend && py -m uvicorn api.server:app --reload` → http://localhost:8000) and assertions for element presence.
**Test:** `py tools/check_game_ui.py` (exit 0) and `cd frontend && npm run build` (exit 0). Capture both. Backend regression sanity: `cd backend && py -m pytest tests/ -q`.
**Done When:** The check script passes, the frontend builds, the backend suite is still green, and every `[human-required]` item has captured Playwright evidence.
**Stuck If:** An automated check fails and the cause is not clear from the output.
- [x] Complete

---
⛔ Final slice complete. Run **inspector** for final sign-off.

✅ Inspector: PASS — 2026-06-06 07:13 (final sign-off; 7/7 automated, 16/16 Playwright assertions, 4 screenshots)
