# Inspect Report — Game UI Projects Panel (Domain-Grouped) · Final
Spec: Planning/specs/game-ui_spec.md (Feature: "Projects Panel (Right Column) — Domain-Grouped")
Blueprint: Planning/blueprints/game-ui-projects-domain-grouping_BP.md
Date: 2026-06-07
Run/demo command: `cd backend && py -m uvicorn api.server:app` → http://localhost:8000 (built frontend served from frontend/dist)

Summary (after re-inspection): 2 passed · 0 failed · 5 need human sign-off  (1 automated, 6 human-required)
Finding #2 remains open as a human decision (not a code defect introduced by this slice).

**Re-inspection 2026-06-07 09:24** — Finding #1 (domain order) FIXED: `projectsByDomain` now
derives its order from `factionsByDomain`, then appends faction-less domains. Re-captured
`..._01_panel_default.png` shows both panels in identical order: Aristocracy, Temples,
Military, Harbor, Trade, Guilds, The Professions, Academy. The ordering criterion now PASSES.

--- Original run (FAIL) below ---
Summary: 1 passed · 1 failed · 5 need human sign-off  (1 automated, 6 human-required)

Evidence seeded deterministically via the API (singleton guest session): one domain
funded to completion (Estate / Aristocracy → active) and one broken-ground (Workshop /
Guilds → 25% under construction); the other six domains left empty.

## Results
| Criterion | Status | Evidence |
|-----------|--------|----------|
| Group header for every domain in `snapshot.domains`, **in the faction-panel order**, plus an "Other" group for unmatched domains | **FAIL** (ordering) | `..._01_panel_default.png` — all 8 domain headers present (header-for-every-domain ✓), but order does NOT match the faction panel. Factions: Aristocracy, Temples, Military, Harbor, Trade, Guilds, The Professions, Academy. Projects: Aristocracy, Guilds, Trade, The Professions, Temples, Military, Academy, Harbor. ("Other" group not exercised — no unknown-domain project; code path present.) |
| Each group collapsible and expanded on load; header click toggles just that group | needs-human | `..._01_panel_default.png` (all expanded, carets ▾) + `..._02_group_collapsed.png` (Aristocracy collapsed to ▸, its Estate row hidden, all other groups unchanged) |
| A domain with no projects shows a "No projects" placeholder | needs-human | `..._01_panel_default.png` — Trade, The Professions, Temples, Military, Academy, Harbor each show "No projects" under their header |
| Projects appear under their domain group as a flat list, no build-status split inside the group | needs-human | `..._01_panel_default.png` — Estate (active) under Aristocracy, Workshop (building) under Guilds; no status-based subsections |
| Under-construction rows show a build-progress %; others show a status label and no per-row domain text | needs-human | `..._01_panel_default.png` — Workshop shows "25%", Estate shows "Active"; no per-row domain text |
| Clicking a project row opens the details modal (progress/health bar + core fields); advancing a cycle while open keeps it in sync | needs-human (partial) | `..._03_details_modal.png` — Estate modal: Health 100% bar, Status Active, Domain Aristocracy, Type base, Upkeep 10 gold/cycle, Initiated by Mayor. **Cycle-sync sub-claim NOT evidenced** — see Findings #2. |
| The projects API response includes `build_progress` — `tests/test_projects_api.py` | PASS | `py -m pytest tests/test_projects_api.py -q` → 2 passed; asserts `build_progress` in `ProjectResponse.model_fields` and survives serialization |

## Findings (failures / gaps)
1. **Domain order mismatch (FAIL).** The spec requires the projects panel be in "the same
   order the faction panel uses." It isn't. `projectsByDomain` iterates
   `Object.entries(snapshot.domains)` (dict key order), while the faction panel's
   `factionsByDomain` orders domains by first-faction-appearance. The blueprint (Slice 1,
   Step 1) assumed these were the same order — a faulty assumption. Fix: order
   `projectsByDomain` to follow `factionsByDomain`'s domain sequence, then append any
   faction-less domains, then "Other". (Builder fix — inspector does not edit code.)
2. **"Advance a cycle while modal open" is unreachable via the UI (gap).** The project
   details modal renders a full-screen `.modal-overlay`; it intercepts the "Run Cycle"
   button, and the overlay's `@click.self` closes the modal. So a user cannot advance a
   cycle with the modal open, and the `refresh()` re-sync code (carried over, unchanged by
   this slice) has no UI trigger. `..._04_modal_after_cycle.png` shows the forced click
   closing the modal rather than stepping the cycle. This predates the slice (the modal
   wiring was untouched). Flagging for the human: either accept the criterion as
   code-present-but-not-UI-reachable, or treat as a separate fix.

## Human sign-off
Review each, tick when verified:
- [ ] Collapsible + expanded-on-load + per-group toggle — `..._01_panel_default.png`, `..._02_group_collapsed.png`
- [ ] Empty-domain "No projects" placeholder — `..._01_panel_default.png`
- [ ] Flat list per group (no status split) — `..._01_panel_default.png`
- [ ] Under-construction % / status label / no per-row domain text — `..._01_panel_default.png`
- [ ] Row opens details modal with core fields — `..._03_details_modal.png`
- [ ] (decision) Cycle-sync-while-modal-open — accept code-present, or fix UI reachability (Finding #2)

## Failures
- Domain order does not match the faction panel — expected faction-panel order
  (Aristocracy, Temples, Military, Harbor, Trade, Guilds, The Professions, Academy),
  observed snapshot.domains order (Aristocracy, Guilds, Trade, The Professions, Temples,
  Military, Academy, Harbor). Evidence: `..._01_panel_default.png`. Fix in Finding #1.
