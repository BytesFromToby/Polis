# Blueprint: Game UI — Projects Panel Domain-Grouping
Spec: Planning/specs/game-ui_spec.md  (Feature: "Projects Panel (Right Column) — Domain-Grouped")
Date: 2026-06-07

---

## Builder instructions
- Execute steps in order. Do not skip, reorder, or read ahead into the next slice.
- Check off each step when complete: [ ] → [x]
- One step = one logical concern. If a step can't be tested on its own, it's too small — merge it. If it touches more than one concern, split it.
- Deviation: if you do something differently than the step says, note it inline and keep going.
- Stuck: stop immediately. Do not try alternative approaches. Report exactly where and why.

**Scope note:** This blueprint covers ONLY the Projects Panel rewrite in
`frontend/src/views/GameView.vue`. Every other feature in `game-ui_spec.md` is already
built and must not change. This is pure frontend work over the existing `/projects`
endpoint — no backend or API change. The single `[automated]` Done-when item
(`tests/test_projects_api.py` — `build_progress` in the response) is already covered by
that pre-existing, passing test; no new test is written. All other Done-when items are
`[human-required]`.

---

## Slice 1: Projects grouped by domain

**Scope:** The right-column Projects panel renders one collapsible group per domain (every
domain shown, expanded by default), each listing that domain's projects as a flat list,
with the app building cleanly.

### Step 1: Add `projectsByDomain` computed
**Build:** In `frontend/src/views/GameView.vue`, add a computed `projectsByDomain` that
mirrors the existing `factionsByDomain` shape. Iterate over **every** domain in
`this.snapshot.domains` (so empty domains still produce a group), building a group
`{ id, name, projects: [] }` for each, in `snapshot.domains` iteration order (the same
order the faction panel uses). Then assign each project in `this.projectList` to the group
whose `id` matches the project's `domain`; a project whose `domain` has no matching domain
entry goes into an `"Other"` group (`{ id: 'other', name: 'Other', projects: [] }`),
appended last and only created if at least one project needs it. Return the array of groups.
If `this.snapshot?.domains` is absent, return `[]`.
**Test:** `cd frontend && npm run build` — exit code 0.
**Done When:** `projectsByDomain` exists and compiles; it returns one entry per domain in
`snapshot.domains` (including domains with zero projects) plus an `"Other"` group only when
some project's domain is unknown.
**Stuck If:** `snapshot.domains` is not an object keyed by domain id, or projects expose no
`domain` field (contradicts the spec/ProjectResponse) — stop and report.
- [x] Complete
**Deviation:** Removing the unused `buildingProjects`/`otherProjects` computeds (Step 4)
was folded into this step, since `projectsByDomain` replaced the same computed block.
`activeProjects` (already unused, never referenced) was removed at the same time — trivially
safe per Step 4's allowance. The template kept referencing the removed computeds until Step
3, but that only affects runtime, not the build; the Step 1 build still passed exit 0.

### Step 2: Add per-domain expand state (expanded by default) + toggle
**Build:** Add a data field `expandedProjectDomains: {}`. Add a method
`toggleProjectDomain(id)` that flips the stored value, treating **undefined as expanded**:
i.e. `this.expandedProjectDomains[id] = this.expandedProjectDomains[id] === false ? true : false`.
Do NOT reuse the faction panel's `expandedDomains`/`toggleDomain` (those are collapsed-by-
default and shared with the faction list). The "undefined = expanded" convention means no
pre-population is needed — groups start open.
**Test:** `cd frontend && npm run build` — exit code 0.
**Done When:** `expandedProjectDomains` and `toggleProjectDomain` exist; a never-toggled
domain is treated as expanded.
**Stuck If:** Toggling a project domain also collapses/expands the faction panel (state
leaked between the two) — stop and report.
- [x] Complete

### Step 3: Rewrite the right-panel template to domain groups
**Build:** Replace the right panel body (the `<div class="panel panel-right">` block,
currently the `v-if="projectList.length"` list with `buildingProjects`/`otherProjects` loops
and the single "No projects." fallback) with a loop over `projectsByDomain`. For each group
render a collapsible header (reuse the faction panel's `domain-header`/`domain-caret`
classes for visual consistency): a caret showing `▾` when
`expandedProjectDomains[g.id] !== false` else `▸`, the domain `name`, and the project count
`g.projects.length`; clicking the header calls `toggleProjectDomain(g.id)`. When the group
is expanded (`expandedProjectDomains[g.id] !== false`), render its projects as a **flat
list** (no building-first split): for each project a `project-row` (keep `building` class
when `p.status === 'under_construction'`) that opens the details modal on click
(`@click="selectedProject = p"`), showing `p.name` and — when under construction — a
`project-pct accent` of `{{ projectPct(p) }}%`, otherwise a `project-domain muted` showing
`{{ projectStatusLabel(p.status) }}` (a status label, NOT the domain — domain is now the
header). When `g.projects.length === 0`, show a "No projects" placeholder under the header.
Keep the panel title "Projects". Do not touch the project details modal block.
**Test:** `cd frontend && npm run build` — exit code 0; then load the play screen
(`cd backend && py -m uvicorn api.server:app --reload`) and confirm the right panel shows a
header per domain, expanded, with project rows under their domain.
**Done When:** Every domain shows a header; groups are expanded on load and a header click
toggles only that group; projects sit under their domain as a flat list; empty domains show
"No projects"; under-construction rows show `%`, others show a status label and no per-row
domain text.
**Stuck If:** Clicking a project row no longer opens the details modal, or a cycle advance
desyncs the open modal (that wiring lives in `refresh()` and must remain intact) — stop and
report.
- [x] Complete
**Deviation:** Live play-screen confirmation deferred to inspector (which captures
screenshot evidence for the `[human-required]` items). The build passes exit 0; the
`@click="selectedProject = p"` wiring and `refresh()` modal-sync were left untouched.

### Step 4: Remove the now-unused project computeds
**Build:** Delete the `buildingProjects` and `otherProjects` computed properties (no longer
referenced after Step 3). Leave `activeProjects` decisions out of scope unless its removal
is trivially safe; if you find `activeProjects` is also unused, you may remove it and note
the deviation. Do not remove `projectPct`, `projectStatusLabel`, `domainName`,
`initiatorName`, or `selectedProject` — the details modal still uses them.
**Test:** `cd frontend && npm run build` — exit code 0; grep the file confirms no remaining
reference to `buildingProjects`/`otherProjects`.
**Done When:** The file builds and contains no references to the removed computeds.
**Stuck If:** A removed computed turns out to be referenced elsewhere — stop and report.
- [x] Complete
**Deviation:** Executed as part of Step 1 (see that step's deviation). Post-build grep
confirms no remaining `buildingProjects`/`otherProjects`/`activeProjects` references.

---
⛔ End of Slice 1. Run **inspector** on this slice before continuing.

---

## Final Slice: Verify spec Done when items

**Scope:** Confirm the full Projects Panel feature meets its Done-when items and the suite is green.

### Final Step: Verify spec Done when items
**Build:** No new code. Confirm each `**Done when:**` item of the "Projects Panel (Right
Column) — Domain-Grouped" feature is met:
- (human) Group header for every domain in `snapshot.domains`, in faction-panel order, plus
  an "Other" group for any project with an unmatched domain.
- (human) Each group collapsible and expanded on load; header click toggles just that group.
- (human) Empty domain shows a "No projects" placeholder.
- (human) Projects are a flat list per group (no build-status split).
- (human) Under-construction rows show a build-progress `%`; others show a status label and
  no per-row domain text.
- (human) Clicking a row opens the details modal; advancing a cycle while open keeps it in sync.
- (automated) `tests/test_projects_api.py` — projects response includes `build_progress`.
**Test:** Run the automated item: `cd backend && py -m pytest tests/test_projects_api.py -q`
(and the full suite `py -m pytest tests/ -q` to confirm nothing regressed). Run
`cd frontend && npm run build` for a clean build. For the `[human-required]` items, capture
play-screen evidence (screenshots via the playwright python inspector) for inspector/human review.
**Done When:** `test_projects_api.py` passes, the full suite is green, `npm run build` exits
0, and every `[human-required]` item has captured evidence.
**Stuck If:** `test_projects_api.py` fails (it should already pass — investigate whether the
panel change touched anything it shouldn't have) or a human-required item can't be evidenced.
- [x] Complete
**Note:** `tests/test_projects_api.py` passes (2 passed); full suite green (324 passed);
`npm run build` exits 0. `[human-required]` evidence to be captured by inspector.

---
⛔ Final slice complete. Run **inspector** for final sign-off.

❌ Inspector: FAIL — 2026-06-07 09:20 — see output/inspect/Inspect_game-ui-projects-domain-grouping_Final_2026-06-07.md
   (domain order does not match the faction panel — Finding #1; Finding #2: cycle-sync-while-modal-open not UI-reachable)
✅ Inspector: PASS (re-inspection) — 2026-06-07 09:24 — Finding #1 fixed (projectsByDomain now follows faction-panel order); all automated PASS, human-required items evidenced. Finding #2 left as an open human decision (pre-existing modal behavior, untouched by this slice).
