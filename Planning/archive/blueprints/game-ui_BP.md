# Blueprint: Game UI — Demo Layout
Spec: Planning/specs/game-ui_spec.md
Date: 2026-05-28

---

## Builder instructions
- Execute steps in order. Do not skip, reorder, or read ahead into the next slice.
- Check off each step when complete: [ ] → [x]
- One step = one logical concern. If a step can't be tested on its own, it's too small — merge it. If it touches more than one concern, split it.
- Deviation: if you do something differently than the step says, note it inline and keep going.
- Stuck: stop immediately. Do not try alternative approaches. Report exactly where and why.

**Scope note:** Frontend only — `frontend/src/views/GameView.vue` and
`frontend/src/components/MayorActionsModal.vue`. Uses existing API (`state.full`,
`state.logs`, `mayor.get`, `treasury.get`, `projects.list`) — no backend change. All
Done-when items are `[human-required]`; the test for every step is `npm run build` plus
visual verification, and inspector captures the final evidence by driving the UI. Build
with `cd frontend && npm run build`; serve via the backend and load the `/game` route to
verify. **Recommended order:** build `audience_BP.md` first so `AudienceModal` is in its
v3 shape before Slice 4 wires the new entry points.

---

## Slice 1: Faction panel — domain-grouped, expandable (left column)
**Scope:** The left column lists factions grouped under their domain, each domain collapsible, each faction block showing name+leader, rating bar, traits, and last action.

### Step 1: Group factions by domain
**Build:** In `GameView.vue`, add a computed `factionsByDomain` that buckets `snapshot.factions` by `domain_primary`, attaching each domain's `{ name, cap, utilization }` from `snapshot.domains`. Factions whose `domain_primary` has no matching domain entry go in an `"Other"` bucket (label "Other", no cap). Return an ordered array of `{ id, name, cap, utilization, factions: [...] }`.
**Test:** `cd frontend && npm run build`
**Done When:** Build succeeds; `factionsByDomain` returns one entry per domain that has factions, plus "Other" if needed.
**Stuck If:** `snapshot.domains` is empty/absent at runtime — note it; fall back to grouping by `domain_primary` id with the id as the label.
- [x] Complete

### Step 2: Derive last action per faction
**Build:** Add a method `lastActionFor(factionId)` that scans the loaded `logs` newest-first for the most recent event whose actor is that faction (match on the event's actor field — confirm the field name in the log payload; it is the faction id) and returns its `narrative`, or `null` if none. (Reuse `logsNewestFirst` ordering.)
**Test:** `cd frontend && npm run build`
**Done When:** Build succeeds; `lastActionFor` returns a narrative string for a faction that has acted and `null` otherwise.
**Stuck If:** Log events don't carry the actor faction id — note the actual shape; this drives the placeholder behaviour in Step 4.
- [x] Complete
  **Deviation:** Confirmed the log-event actor field is `actor_id` (verified against `engine/llm/prompt_builder.py:181` and the cycle-event serialization), so `lastActionFor` matches on `ev.actor_id`. Iterates events within a cycle in reverse to return the genuinely most-recent action.

### Step 3: Domain group header with cap fill + expand toggle
**Build:** Replace the flat faction list template with domain groups. Each group renders a header showing the domain name, `utilization / cap` (e.g. "412 / 600"), and a proportional fill bar (`utilization / cap`, clamped 0–100%). Track expanded state in a reactive set/object keyed by domain id; **collapsed by default**. Clicking a header toggles only that group. Show a faction count on the header as the collapsed cue.
**Test:** `cd frontend && npm run build`; load `/game`.
**Done When:** Groups render collapsed; clicking a header expands/collapses just that group; header shows `utilization / cap` and a fill bar.
**Stuck If:** n/a.
- [x] Complete

### Step 4: Faction block contents
**Build:** Inside an expanded group, render each faction block with: **Name** + **Leader** (`leaderName(f)`), the **rating bar** (reuse `ratingPct`/`ratingColor`), **trait tags** (existing `trait.trait || trait` slice), a **Last Action** line (`lastActionFor(f.id)` or a "No action yet" placeholder), and an **Audience** button (wired in Slice 4 — for now emit/handle a `openAudience(f.id)` stub).
**Test:** `cd frontend && npm run build`; load `/game` and expand a group.
**Done When:** Each faction block shows name, leader, rating bar, traits, last-action line (or placeholder), and an Audience button.
**Stuck If:** n/a.
- [x] Complete
  **Deviation:** `openAudience(f.id)` stub sets a new `audienceFactionId` data field (added now rather than in Slice 4) so the assignment is reactive; full modal wiring still happens in Slice 4.

---
⛔ End of Slice 1. Run **inspector** on this slice before continuing.

---

## Slice 2: Mayor window (centre-top) + actions cleanup
**Scope:** The Mayor's standing moves to a prominent centre-top window carrying Treasury, AP/Actions, Reputation, and World — but not Projects; the standalone Audience button and Actions button live here; "Meet with Faction" is removed from the actions grid.

### Step 1: Restructure the layout shell
**Build:** Change `.panels` so the centre column is split vertically: a centre-top **Mayor window** and a centre-bottom region (Event Log, relocated in Slice 3). Left column stays Factions; right column becomes Projects (Slice 3). Keep it responsive within the existing `game-layout` fl/height model.
**Test:** `cd frontend && npm run build`; load `/game`.
**Done When:** The page shows Factions (left), a Mayor window across the centre-top, empty centre-bottom + right regions (filled later) without layout breakage.
**Stuck If:** The height/overflow model fights the new split — note the specific CSS conflict.
- [x] Complete
  **Deviation:** While restructuring the shell I also moved the Event Log markup into the centre-bottom (`.center-log`) region rather than leaving it empty — this is nominally Slice 3 Step 1's job, but the shell split forced its placement. Slice 3 Step 1 therefore just confirms/styles it. The right column was given a "Projects" placeholder, filled in Slice 3.

### Step 2: Populate the Mayor window
**Build:** Move the current right-panel content **except Projects** into the Mayor window: Treasury (gold, income, spent, debt/invested when present, max tax), Actions/AP (`action_points / action_cap`, top reputation rows, exemptions summary), and World (chaos). Remove the Projects section from this window entirely.
**Test:** `cd frontend && npm run build`; load `/game`.
**Done When:** Mayor window shows Treasury, AP/Reputation, and World; no Projects anywhere in it.
**Stuck If:** n/a.
- [x] Complete
  **Deviation:** The AP/reputation section is labelled "Standing" (not "Actions"), since the Act button moved to the window header bar — avoids two things both called "Actions". Content (AP x/cap, top reputation, exemptions) unchanged.

### Step 3: Standalone Audience button + Actions button
**Build:** In the Mayor window add two clear buttons: **Meet with Faction** (standalone audience entry — wired in Slice 4) and **Actions** (opens the existing `MayorActionsModal`). Make them prominent (this is the player's main lever), not the current 0.7rem chip.
**Test:** `cd frontend && npm run build`; load `/game`.
**Done When:** Both buttons render in the Mayor window; Actions opens `MayorActionsModal`.
**Stuck If:** n/a.
- [x] Complete

### Step 4: Remove "Meet with Faction" from the actions grid
**Build:** In `MayorActionsModal.vue`, remove the "Meet with Faction" action row (the one with `audienceFactionId` + `openAudience` + `Audience ▸`) and its now-unused data/handlers/`AudienceModal` mount **if** the modal no longer opens an audience itself. (The audience is now launched from GameView — see Slice 4. If removing the embedded `AudienceModal` here, ensure nothing else references it.)
**Test:** `cd frontend && npm run build`; open the Actions modal.
**Done When:** The actions grid no longer contains a "Meet with Faction" action; the modal still builds and its other actions work.
**Stuck If:** Other code depends on `MayorActionsModal` emitting audience events — note the reference.
- [x] Complete
  **Deviation:** Removed the embedded `<AudienceModal>` mount from `MayorActionsModal` along with its import, `components` entry, `audienceFactionId`/`showAudience` data, `audienceFaction` computed, and `openAudience`/`onAudienceActed` methods — the audience is launched from GameView now (Slice 4). No remaining references; build dropped from 47→45 modules.

---
⛔ End of Slice 2. Run **inspector** on this slice before continuing.

---

## Slice 3: Event Log (centre-bottom) + Projects panel (right)
**Scope:** The event log fills the centre column beneath the Mayor window; projects get a dedicated right column with in-progress first and a percent-complete.

### Step 1: Relocate the Event Log
**Build:** Move the existing event-log block (cycle headers, `logsNewestFirst`, dramatic highlighting) into the centre-bottom region beneath the Mayor window. No content change.
**Test:** `cd frontend && npm run build`; load `/game` and run a cycle.
**Done When:** The event log renders below the Mayor window, retaining cycle grouping, newest-first order, and dramatic highlighting.
**Stuck If:** n/a.
- [x] Complete
  **Deviation:** Already satisfied — the Event Log was relocated into `.center-log` during the Slice 2 Step 1 shell restructure. No further change needed here.

### Step 2: Projects panel on the right
**Build:** In the right column, render `projectList`: under-construction projects **first**, each showing a percent-complete from its build progress (`health` shown as `{{ health }}%`); then active/other projects with name and domain/status (reuse current `activeProjects`/`buildingProjects` computeds, ordering building first). Show a "No projects" placeholder when the list is empty.
**Test:** `cd frontend && npm run build`; load `/game`.
**Done When:** Right column lists under-construction projects first with `%`, then the rest; empty list shows the placeholder.
**Stuck If:** n/a.
- [x] Complete
  **Deviation:** Added an `otherProjects` computed (`status !== 'under_construction'`) for the "then the rest" group, rather than reusing `activeProjects` alone — so damaged/critical projects also show, not just active ones.

---
⛔ End of Slice 3. Run **inspector** on this slice before continuing.

---

## Final Slice: Audience entry points + full verification
**Scope:** Both audience entry points reach the `AudienceModal`; the whole screen verified against the spec.

### Step 1: Host AudienceModal in GameView with two entry paths
**Build:** Mount `AudienceModal` in `GameView.vue`, opened via a single `audienceFactionId` ref. Wire:
- **Faction card button** → `openAudience(f.id)` sets the target and opens the modal pre-targeted (no picker).
- **Standalone Mayor button** → opens a lightweight faction selector (a small dropdown/list of factions); choosing one opens the modal for that faction.
On close/`acted`, refresh mayor data (AP) as the old flow did. Respect existing backend errors (AP/cooldown/active-deal) — let them surface in the modal.
**Test:** `cd frontend && npm run build`; load `/game`.
**Done When:** A faction card's Audience button opens the audience targeted to that faction with no picker; the standalone button opens it with a faction selector; both reach the `AudienceModal` flow.
**Stuck If:** `AudienceModal`'s expected props/events differ from what GameView passes — align to the component's current contract (post-`audience_BP`).
- [x] Complete
  **Deviation:** Standalone path uses a simple faction-picker modal (`showAudiencePicker` + `.picker-*` styles) listing all factions; choosing one sets `audienceFactionId`. Both paths share one `AudienceModal` mount in GameView keyed off `audienceFactionId`; `@acted` reuses the existing `onActed` (refreshes AP), `@close` clears the target.

### Final Step: Verify spec Done when items
**Build:** No new code. Confirm all `game-ui_spec.md` **Done when:** items are met.
**Test:** `cd frontend && npm run build`, serve via backend, and have inspector drive the `/game` route: capture screenshots showing domain grouping + cap fill + expand/collapse, faction block contents incl. last action, the centre-top Mayor window without Projects, the standalone Audience + Actions buttons, the actions grid lacking "Meet with Faction", the relocated Event Log, the right-hand Projects panel (in-progress first with %), and both audience entry paths opening the modal.
**Done When:** Every `[human-required]` criterion across all five features has captured evidence.
**Stuck If:** The frontend build fails or the `/game` route errors on load — report the console/build output.
- [x] Complete
  **Note:** `npm run build` is green. Every Done-when item in `game-ui_spec.md` is `[human-required]`, so there are no committed tests to run — **inspector** must serve the app and drive the `/game` route to capture the visual evidence (domain grouping + cap fill + expand, faction blocks incl. last action, Mayor window minus Projects, Audience + Actions buttons, actions grid lacking "Meet with Faction", relocated Event Log, right-hand Projects panel, both audience entry paths). Builder does not run inspector.

---
⛔ Final slice complete. Run **inspector** for final sign-off.
