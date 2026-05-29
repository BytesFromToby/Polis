# Spec: Game UI — Demo Layout

The main play screen (`GameView`) restructured for demos so the Mayor and the LLM
faction audience — the project's standout features — are front and centre instead of
buried. Factions become a domain-grouped, expandable browser; the Mayor's standing
moves to a prominent centre-top window; the audience is reachable in one click from
either a faction card or a dedicated Mayor button. Pure frontend work over the existing
API — no engine or simulation behaviour changes.

## Scope
- Does: restructure `GameView` into a three-column demo layout (Factions left,
  Mayor window centre-top, Event Log centre-bottom, Projects right); group factions by
  domain with cap/fullness and click-to-expand; surface a faction block with name +
  leader, rating bar, traits, and last action; provide two audience entry points
  (per-faction-card button and a standalone Mayor button); remove "Meet with Faction"
  from the Mayor Actions grid.
- Does NOT: change the audience negotiation flow, the Mayor-confirm behaviour, or the
  debug controls — those live in `audience_spec.md`. Does NOT add or change backend
  endpoints (consumes existing `/state`, `/mayor`, `/treasury`, `/projects`, `/logs`).
  Does NOT cover a thematic/visual restyle (colours, fonts, Greek framing) — that is a
  separate later pass.

---

## Feature: Faction Panel — Domain-Grouped (Left Column)

Factions are listed in the left column, grouped under their `domain_primary`. Each
domain is a collapsible group; expanding it reveals its faction blocks.

- Input: `snapshot.factions` (keyed by id, each with `domain_primary`, `rating`,
  `leader`, `traits`) and `snapshot.domains` (each with `name`, `cap`, `utilization`)
  from `state.full`; the event log from `state.logs` (for last action).
- Output: a left-column list of domain group headers, each expandable to its factions.

Domain group header shows: domain name, its fill as `utilization / cap`, and a
proportional fill bar. Groups are **collapsed by default**; clicking a header toggles
its factions. A faction whose `domain_primary` has no matching domain entry falls under
an "Other" group rather than being dropped.

Each **faction block** (shown when its domain is expanded) contains:
- **Name** and **Leader** name (from `leader.name`)
- **Rating bar** — same fill-percentage and colour logic as the current card
- **Traits** — trait tags (as today; `trait.trait || trait`)
- **Last Action** — the narrative of the most recent event where that faction is the
  actor, derived client-side from the loaded logs; a placeholder ("No action yet") when
  the faction has not acted
- An **Audience** button (behaviour in the Audience Entry Points feature)

**Done when:**
- Every faction appears under its `domain_primary` group, each domain listed once, and a faction with an unknown domain appears under an "Other" group  `[human-required]`
- Each domain header shows `utilization / cap` and a fill bar proportional to that ratio  `[human-required]`
- Domain groups are collapsed on load; clicking a domain header expands/collapses just that group's factions  `[human-required]`
- A faction block shows name, leader name, rating bar, trait tags, and a last-action line  `[human-required]`
- The last-action line shows the most recent log narrative for that faction, and a placeholder when the faction has no events yet  `[human-required]`

---

## Feature: Mayor Window (Centre-Top)

The Mayor's standing moves out of the cramped right rail into a prominent window across
the top of the centre column. It carries everything the current right panel shows
**except Projects**.

- Input: `mayor` (action_points, action_cap, reputation), `treasury`, and
  `world` (chaos) from the existing endpoints.
- Output: a centre-top window with Treasury, Actions/AP, Reputation, and World, plus the
  audience and actions entry points.

Contents:
- **Treasury** — gold, income, spent, debt/invested (when present), max tax (as today)
- **Actions / AP** — action points `x / cap`; top reputation entries; exemptions summary
- **World** — chaos display (as today)
- A standalone **Meet with Faction (Audience)** button (see Audience Entry Points)
- An **Actions** button opening the cleaned-up `MayorActionsModal`

Projects do **not** appear in this window (they move to the right column).

**Done when:**
- The centre-top window shows Treasury (gold, income, spent, max tax), AP `x / cap`, a reputation summary, and World chaos  `[human-required]`
- No Projects section appears anywhere in the Mayor window  `[human-required]`
- The Mayor window contains a standalone Audience button and an Actions button, both opening their respective flows  `[human-required]`
- The `MayorActionsModal` no longer contains a "Meet with Faction" action in its grid  `[human-required]`

---

## Feature: Event Log (Centre, Below Mayor)

The event log keeps its current content and behaviour (cycle headers, newest-first,
dramatic highlighting) but relocates to fill the centre column beneath the Mayor window.

- Input: `state.logs` (as today).
- Output: the existing log rendering, positioned centre-bottom.

**Done when:**
- The event log renders in the centre column directly below the Mayor window, retaining cycle grouping, newest-first order, and dramatic-event highlighting  `[human-required]`

---

## Feature: Projects Panel (Right Column)

Projects move to a dedicated right column. In-progress (under-construction) projects are
listed first, each with a percent-complete; remaining projects follow.

- Input: `projects.list` (each with `status`, `health`, `name`, `domain`).
- Output: a right-column panel, under-construction projects on top with `%`, then the rest.

For an under-construction project, percent-complete is its `health` (build progress
0→100). Active and other projects follow, showing name and domain/status as today.

**Done when:**
- The right column lists under-construction projects first, each showing a percent-complete from its build progress (`health`)  `[human-required]`
- Active/other projects are listed after the in-progress ones, with name and domain/status  `[human-required]`
- An empty project list shows a "No projects" placeholder  `[human-required]`

---

## Feature: Audience Entry Points

Two ways to open the audience, both leading into the existing `AudienceModal` flow:

1. **Per-faction-card button** — the Audience button on a faction block opens the
   audience **pre-targeted** to that faction (no faction picker).
2. **Standalone Mayor button** — the Audience button in the Mayor window opens the
   audience with a **faction selector** (the user picks who to meet).

Both respect the existing rules surfaced by the backend (AP cost, cooldown, no audience
while a deal is active) — those errors surface in the audience flow, not here.

- Input: a faction id (card path) or a user selection (standalone path).
- Output: the `AudienceModal` opened for the chosen faction.

**Done when:**
- Clicking a faction card's Audience button opens the audience targeted to that faction, with no faction picker step  `[human-required]`
- The standalone Mayor audience button opens the audience with a faction selector  `[human-required]`
- Both paths reach the same audience conversation flow defined in `audience_spec.md`  `[human-required]`

---

## Open Questions
<!-- none -->
