# Spec: Game UI — Demo Layout

The main play screen (`GameView`) restructured for demos so the Mayor and the LLM
faction audience — the project's standout features — are front and centre instead of
buried. Factions become a domain-grouped, expandable browser; the Mayor's standing
moves to a prominent centre-top window; the audience is reachable in one click from
either a faction card or a dedicated Mayor button. Pure frontend work over the existing
API — no engine or simulation behaviour changes.

**Surgical-correctness pass (2026-06-05):** the prior backend reworks (faction redesign,
projects-rework, mayor-actions-rework) left the UI showing dropped fields (`entrench`) and
offering removed/inert Mayor actions. This pass makes the existing UI *truthful* without
redesigning it: the Mayor Actions modal carries exactly the 8-lever demo roster (adding
**Sabotage** and **Build Project**, dropping the seven cut actions), gold is surfaced where
it is spent, faction readouts lead with the **integer level** (`int(rating)`, e.g. "3" not
"3.34"), deterministic Meet is dropped from the UI (the audience is the sole
faction-engagement path), and the dead `entrench` column and `commission()` call are removed.
A full thematic/visual play-UI redesign remains a separate, later pass.

## Scope
- Does: restructure `GameView` into a three-column demo layout (Factions left,
  Mayor window centre-top, Event Log centre-bottom, Projects right); group factions by
  domain with cap/fullness and click-to-expand; surface a faction block with name +
  leader, level/rating, traits, and last action; provide two audience entry points
  (per-faction-card button and a standalone Mayor button).
- Does: align the Mayor Actions modal with the 8-lever demo roster, surface gold there,
  lead faction readouts with integer level, drop deterministic Meet from the UI, and
  remove the dead `entrench` column and `commission()` call.
- Does NOT: change the audience negotiation flow, the Mayor-confirm behaviour, or the
  debug controls — those live in `audience_spec.md`. Does NOT add or change backend
  endpoints (consumes existing `/state`, `/mayor`, `/treasury`, `/projects`, `/logs`,
  and the generic `/mayor/act`). Does NOT cover a thematic/visual restyle (colours, fonts,
  Greek framing) or a play-UI redesign — those are separate later passes.

---

## Feature: Faction Panel — Domain-Grouped (Left Column)

Factions are listed in the left column, grouped under their `domain_primary`. Each
domain is a collapsible group; expanding it reveals its faction blocks.

- Input: `snapshot.factions` (keyed by id, each with `domain_primary`, `rating`,
  `health`, `leader`, `traits`) and `snapshot.domains` (each with `name`, `cap`,
  `utilization`) from `state.full`; the event log from `state.logs` (for last action).
- Output: a left-column list of domain group headers, each expandable to its factions.

Domain group header shows: domain name, its fill as `utilization / cap`, and a
proportional fill bar. Groups are **collapsed by default**; clicking a header toggles
its factions. A faction whose `domain_primary` has no matching domain entry falls under
an "Other" group rather than being dropped.

Each **faction block** (shown when its domain is expanded) contains:
- **Name** and **Leader** name (from `leader.name`)
- **Level** — the integer `int(rating)` shown as the primary rank readout (e.g. "Lv 3").
  The precise `rating` float may appear only as a de-emphasized secondary (small or
  parenthetical); the integer level leads. The existing rating bar (fill %/colour) stays.
- **Traits** — trait tags (as today; `trait.trait || trait`)
- **Last Action** — the narrative of the most recent event where that faction is the
  actor, derived client-side from the loaded logs; a placeholder ("No action yet") when
  the faction has not acted
- An **Audience** button (behaviour in the Audience Entry Points feature)

**Done when:**
- Every faction appears under its `domain_primary` group, each domain listed once, and a faction with an unknown domain appears under an "Other" group  `[human-required]`
- Each domain header shows `utilization / cap` and a fill bar proportional to that ratio  `[human-required]`
- Domain groups are collapsed on load; clicking a domain header expands/collapses just that group's factions  `[human-required]`
- A faction block shows name, leader name, the **integer level** as the lead rank readout (not the raw `rating` float), trait tags, and a last-action line  `[human-required]`
- The faction block does not present the multi-decimal `rating` as its primary number (the float is absent or visibly secondary)  `[automated]`
- The last-action line shows the most recent log narrative for that faction, and a placeholder when the faction has no events yet  `[human-required]`

---

## Feature: Mayor Window (Centre-Top)

The Mayor's standing sits in a prominent window across the top of the centre column.
It carries everything the current right panel shows **except Projects**.

- Input: `mayor` (action_points, action_cap, reputation), `treasury`, and
  `world` (chaos) from the existing endpoints.
- Output: a centre-top window with Treasury, Actions/AP, Reputation, and World, plus the
  audience and actions entry points.

Contents:
- **Treasury** — gold, income, spent, debt/invested (when present), max tax (as today)
- **Actions / AP** — action points `x / cap`; top reputation entries; exemptions summary
- **World** — chaos display (as today)
- A standalone **Request Audience** button (see Audience Entry Points). *This is the button
  formerly labelled "Meet with Faction ▸"; it opens the audience and is relabelled so it no
  longer implies the deterministic Meet action.*
- An **Actions** button opening the `MayorActionsModal`

Projects do **not** appear in this window (they move to the right column).

**Done when:**
- The centre-top window shows Treasury (gold, income, spent, max tax), AP `x / cap`, a reputation summary, and World chaos  `[human-required]`
- No Projects section appears anywhere in the Mayor window  `[human-required]`
- The Mayor window contains a standalone audience button **labelled "Request Audience"** (not "Meet with Faction") and an Actions button, both opening their respective flows  `[human-required]`
- No UI control invokes the deterministic `MeetWithFaction` action (the audience is the sole faction-engagement entry point)  `[automated]`

---

## Feature: Mayor Actions Modal — Demo Roster

`MayorActionsModal` surfaces exactly the demo's player-facing levers, dispatched through
the existing generic `mayor.act(userId, action, targetId, targetId2, cycles)` → `POST
/mayor/act`. The seven cut actions are removed; **Sabotage** and **Build Project** are added;
**gold** is surfaced so the cost-bearing levers show affordability.

- Input: `factions`, `domains`, `mayorData` (action_points, action_cap, deals), and the
  treasury **gold** balance (passed in from `GameView`).
- Output: a modal whose action rows are exactly the demo roster, each posting via `mayor.act`.

Rows, grouped:
- **Political** — Publicly Endorse (`act('PubliclyEndorse', factionId)`), Publicly Condemn
  (`act('PubliclyCondemn', factionId)`).
- **Economic** — Grant Tax Exemption (`act('GrantTaxExemption', factionId, '', cycles)`),
  **Sabotage** (`act('Sabotage', factionId)`), **Build Project** (`act('BuildProject', domainId)`).
- **Deals** — the existing Active Deals section with Break (`act('BreakADeal', dealId)`).

Removed entirely (no row): Broker a Deal, Request a Report, Plant a Rumor, Allocate Budget,
Withhold Resources, Issue a Decree, Appoint an Official, Turn a Blind Eye.

Costs & affordability:
- The modal header shows **gold** alongside AP.
- **Sabotage** — target faction; hint "rank −50% of margin, health −50%, rep −10 · 1 AP + 50
  gold"; the Act button is disabled when `ap < 1` **or** `gold < 50`.
- **Build Project** — target domain; hint "Break ground / fund a unit (50g) or repair (+25
  health, 30g) · 1 AP"; the Act button is disabled when `ap < 1`. Gold shortfalls are
  rejected by the backend and shown in the existing result/error banner.

- Input: a faction id (Sabotage, Endorse, Condemn, Exemption) or a domain id (Build Project).
- Output: the action result (outcome + narrative) shown in the existing result banner; AP
  (and gold) update from the response.

**Done when:**
- The modal renders rows for exactly: Publicly Endorse, Publicly Condemn, Grant Tax Exemption, Sabotage, Build Project, and a Break control in the Active Deals section — and none of the eight removed/old actions (Broker a Deal, Request a Report, Plant a Rumor, Allocate Budget, Withhold Resources, Issue a Decree, Appoint an Official, Turn a Blind Eye)  `[automated]`
- The Sabotage row posts `act('Sabotage', <factionId>)` and its Act button is disabled when gold < 50 or AP < 1  `[human-required]`
- The Build Project row posts `act('BuildProject', <domainId>)`  `[human-required]`
- The modal header displays the current gold balance alongside AP  `[automated]`
- Gold-short Build/Sabotage surfaces the backend rejection in the result/error banner without a client crash  `[human-required]`

---

## Feature: Event Log (Centre, Below Mayor)

The event log keeps its current content and behaviour (cycle headers, newest-first,
dramatic highlighting) but sits in the centre column beneath the Mayor window.

- Input: `state.logs` (as today).
- Output: the existing log rendering, positioned centre-bottom.

**Done when:**
- The event log renders in the centre column directly below the Mayor window, retaining cycle grouping, newest-first order, and dramatic-event highlighting  `[human-required]`

---

## Feature: Projects Panel (Right Column)

Projects sit in a dedicated right column. In-progress (under-construction) projects are
listed first, each with a percent-complete; remaining projects follow.

- Input: `projects.list` (each with `status`, `health`, `build_progress`, `name`, `domain`).
- Output: a right-column panel, under-construction projects on top with `%`, then the rest.

For an under-construction project, percent-complete is its **build progress** —
`round(build_progress / 4 × 100)` (4 work units = complete), **not** `health` (which stays 0
during construction). Active and other projects follow, showing name and domain/status.

Clicking any project row opens a details modal: a progress bar (build progress while
under construction, structural health once active) plus status, domain, type, tax level
(if any), upkeep, and initiator. While the modal is open, advancing a cycle keeps it in
sync with the refreshed project data.

**Done when:**
- The right column lists under-construction projects first, each showing a percent-complete derived from build progress (advances as work units are added)  `[human-required]`
- Active/other projects are listed after the in-progress ones, with name and domain/status  `[human-required]`
- An empty project list shows a "No projects" placeholder  `[human-required]`
- Clicking a project row opens a details modal showing its progress/health bar and core fields  `[human-required]`
- The projects API response includes `build_progress` for each project — `tests/test_projects_api.py`  `[automated]`

---

## Feature: Audience Entry Points

Two ways to open the audience, both leading into the existing `AudienceModal` flow:

1. **Per-faction-card button** — the Audience button on a faction block opens the
   audience **pre-targeted** to that faction (no faction picker).
2. **Standalone Mayor button** — the "Request Audience" button in the Mayor window opens
   the audience with a **faction selector** (the user picks who to meet).

Both respect the existing rules surfaced by the backend (AP cost, cooldown, no audience
while a deal is active) — those errors surface in the audience flow, not here.

- Input: a faction id (card path) or a user selection (standalone path).
- Output: the `AudienceModal` opened for the chosen faction.

**Done when:**
- Clicking a faction card's Audience button opens the audience targeted to that faction, with no faction picker step  `[human-required]`
- The standalone Mayor "Request Audience" button opens the audience with a faction selector  `[human-required]`
- Both paths reach the same audience conversation flow defined in `audience_spec.md`  `[human-required]`

---

## Feature: Dashboard Faction Table (DashboardView)

The overview table in `DashboardView` is brought in line with the faction model: the dead
`entrench` column is removed and each faction's **integer level** leads.

- Input: `snapshot.factions` grouped by domain (each with `rating`, `health`, `leader`).
- Output: a per-faction row showing name, integer level, health, and leader — no `entrench`.

**Done when:**
- The dashboard faction table has no `entrench` column and the source contains no `entrench` / `entrenchClass` reference  `[automated]`
- Each faction row shows its integer level (`int(rating)`, e.g. "3") as the rank value, not the multi-decimal `rating`, and shows `health`  `[human-required]`
- The table column count/`colspan` placeholders are consistent after the column removal (no empty/misaligned cells)  `[human-required]`

---

## Feature: API cleanup & build

The retired build path is removed and the app still builds.

- Input: `frontend/src/api.js`.
- Output: no client call to the retired `/projects/commission` endpoint; build succeeds.

**Done when:**
- `frontend/src/api.js` contains no `commission` function and no reference to `/projects/commission`  `[automated]`
- `npm run build` completes with exit code 0  `[automated]`
