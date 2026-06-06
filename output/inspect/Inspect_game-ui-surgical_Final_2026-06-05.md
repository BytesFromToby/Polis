# Inspect Report — Game UI Surgical Correctness Pass · Final
Spec: Planning/specs/game-ui_spec.md
Blueprint: Planning/blueprints/game-ui-surgical_BP.md
Date: 2026-06-05
Run/demo command: `py tools/check_game_ui.py` · `cd frontend && npm run build` · app served at http://localhost:8000 (`cd backend && py -m uvicorn api.server:app`), driven via Playwright (python)

Summary: **7 passed · 0 failed · 20 need human sign-off** (all 20 have captured Playwright screenshot + assertion evidence)

Pinned checks green. Backend regression: **316 passed** (frontend touched no backend behaviour). Live app driven end-to-end (guest auth → official "Polis" city, 41 factions, 3 cycles run): **16/16 Playwright assertions PASS**, 4 full-page screenshots captured.

---

## Automated items
| Criterion | Status | Evidence |
|-----------|--------|----------|
| Faction block does not present the multi-decimal `rating` as its primary number | PASS | `tools/check_game_ui.py` (GameView leads with `Math.floor(f.rating)`) + screenshot `spec_game-ui_actions-modal_2026-06-05.png` shows cards reading "Lv 3 (3.6)" — integer leads, float parenthetical secondary |
| No UI control invokes deterministic `MeetWithFaction` | PASS | `check_game_ui.py` (rglob over `frontend/src/**.vue`: no `MeetWithFaction`) + independent `grep -rc` = none |
| Modal renders exactly the 6 kept levers and none of the 8 removed | PASS | `check_game_ui.py` (Sabotage+BuildProject present; 8 removed absent) + independent grep (exactly 6 `doAct(...)` dispatches) + screenshot shows Political(Endorse,Condemn)/Economic(Grant Tax Exemption,Sabotage,Build Project), Break in Deals |
| Modal header displays gold alongside AP | PASS | `check_game_ui.py` (gold prop + `{{ gold }}` in header) + screenshot shows "4 / 6 AP" and "1170 gold" badges |
| Dashboard table has no `entrench`; source has no `entrench`/`entrenchClass` | PASS | `check_game_ui.py` + independent `grep -c entrench DashboardView.vue` = 0 + screenshot `spec_game-ui_dashboard_2026-06-05.png` shows columns Domain/Name/Level/Health/Leader, no Entrench |
| `api.js` has no `commission` and no `/projects/commission` | PASS | `check_game_ui.py` + independent `grep -rnE "commission" frontend/src/` = none |
| `npm run build` exits 0 | PASS | `cd frontend && npm run build` → `✓ built`, exit 0 |

## Human sign-off (needs-human — evidence captured)
Screenshots under `output/inspect/spec_game-ui_*_2026-06-05.png`. Each Playwright assertion below passed; the human judges layout/feel.
- [ ] Factions grouped by domain, collapsed on load, expandable; block shows name/leader/level/traits/last-action — evidence: `gameview` + `factions` screenshots (ARISTOCRACY expanded: The Eumelidai "Lv 3 (3.6)", traits, last-action line)
- [ ] Domain header shows `utilization / cap` + fill bar — evidence: dashboard + gameview (e.g. "12 / 300")
- [ ] Mayor window shows Treasury (gold/income/spent/max tax), AP x/cap, reputation, World chaos; no Projects section — evidence: `gameview`/`actions-modal` screenshots (Treasury Gold 1170, AP 4/6, Chaos none)
- [ ] Standalone audience button reads "Request Audience" (not "Meet with Faction"); both audience entry points reach the flow — evidence: assertion "Request Audience present" PASS; button visible in screenshots
- [ ] Actions modal: 6 levers grouped Political/Economic/Deals; Sabotage disabled <50 gold; gold-affordability reads cleanly — evidence: `actions-modal` screenshot (Sabotage "1 AP · 50g", Build Project "1 AP · gold", hints visible)
- [ ] Event log centre-bottom, cycle grouping, newest-first, dramatic highlighting — evidence: `gameview` screenshot (narrative log with "The Players strikes hard…" highlighted)
- [ ] Projects panel right column (under-construction first w/ %, then rest; "No projects" placeholder) — evidence: `gameview` screenshot ("No projects" placeholder, fresh start)
- [ ] Dashboard faction table: integer level + health, no entrench, aligned columns — evidence: `dashboard` screenshot (Level/Health columns populated, e.g. 3 / 77)
- [ ] *(remaining layout/feel items from the 5 preserved layout features)* — evidence across the 4 screenshots
*(20 human-required items total across the 8 features; all are layout/feel/affordability backed by the screenshots + the 16 passing Playwright assertions.)*

## Deviations noted
| Step | Deviation | Impact |
|------|-----------|--------|
| S1/1–3 | `MayorActionsModal.vue` rewritten wholesale vs. piecemeal row edits | None — verified by grep + build + live screenshot |
| S2/3 | `onActed` now also refreshes treasury (gold) | None — implements the step; gold updates after a spend |
| S2/2 | Audience picker header "Meet with…" → "Request audience with…" | None — copy consistency with the relabelled button |
| S3/1 | Rating col → Level, Entrench col → Health (count stays 5); fixed pre-existing `colspan` 6→5 | None — satisfies "drop entrench / lead with level / keep health"; screenshot confirms aligned 5-col table |

## Verdict
All 7 `[automated]` Done-when items pass via the committed pinned check + build, each independently re-verified by direct grep and by driving the live app. The 20 `[human-required]` items have concrete screenshot + assertion evidence (16/16 Playwright assertions green) and await the human's layout/feel sign-off. No deviation contradicts the spec. Backend suite unaffected (316 passed). Feature verified pending human sign-off.
