# Spec: Game UI — Pottery Quadrant Layout

The main play screen (`GameView`) restyled into the **Geometric-pottery** art direction
(`../reference/ui-art-direction.md`) and relaid into a **quadrant**: a left rail split into
Factions (top) and Projects (bottom), and a wide main panel split into the Mayor command
dashboard (top) and an Active Events + Chronicle band (bottom). A top command bar carries the
POLIS logotype, the cycle, Run Cycle, the glaze (theme) toggle, and a Menu.

This supersedes the three-column demo-layout passes (faction/projects domain-grouping, the
surgical-correctness pass, the People pass) — that domain-grouping and stack behaviour is
**retained and re-homed** into the quadrant; what changes is the layout, the visual treatment
(now in scope — previously deferred), and the Mayor panel's contents. Pure frontend work over the
existing API plus the already-served active-events data; no engine or simulation change.

**Adopted:** 2026-06-17 (decision `../decisions/2026-06-17-pottery-ui.md`). Mockup iterated to v6
before speccing.

## Scope
- Does: restyle the play UI to the pottery design system (token swap + band-grammar chrome +
  Cinzel/Spectral type + the two-glaze theme toggle), per `../reference/ui-art-direction.md`;
  relayout `GameView` into the quadrant; rebuild the **Mayor command panel** (Treasury + Action
  Points + Take Action / Hold Audience, and the seven-scale **People** readout as a co-header;
  **drop** the Standing and World blocks from this panel); add an **Active Events** panel beside
  the Chronicle; add the command bar (logotype, Run Cycle, glaze toggle, Menu → settings/home).
- Does (small backend addition): **serialize the live `active_events` into the `/state` payload**.
  The session holds them (`api/sessions.py`) but `serialize_state` omits them (a known v1 gap), so
  the Active Events panel needs a `GameEvent` serializer (id, name, `cycles_remaining`, target, a
  disaster/boon flag) folded into the state snapshot. No new endpoint; no engine change.
- Does NOT: change engine/simulation behaviour or add backend **endpoints** (consumes the existing
  `/state`, `/mayor`, `/treasury`, `/projects`, `/logs`, `/mayor/act`); change the audience
  negotiation flow or Mayor-confirm (those are
  `audience_spec.md`); build the per-domain silhouette **emblems** or the **LLM-chronicler**
  in-character summaries (both deferred — the Highlight uses the existing dramatic-beat narrative);
  guarantee light (black-figure) mode polish — dark ships first, light follows.

---

## Feature: Art direction & band grammar

The whole play UI moves to the pottery design system. Implementation is a **primitive swap** in
`frontend/src/style.css` (semantic tokens keep their names; values change to the glaze/terracotta/
clay/oxblood primitives) plus reusable band-chrome classes (`.mdr` meander, `.zig` zigzag) applied
as panel/screen registers. Tokens, palette, patterns, two-glaze rule, and typography are defined
once in `../reference/ui-art-direction.md`.

**Done when:**
- `frontend/src/style.css` semantic tokens resolve to the pottery primitives (glaze grounds,
  terracotta accent, clay text, oxblood danger) — no verdigris/wine values remain in the live
  theme  `[human-required]`
- Panel and screen edges carry the meander register; content sections are separated by the zigzag;
  no ornament sits inside a content row  `[human-required]`
- Oxblood appears **only** on conflict beats (Breaks, broken deals, active disasters, damaged
  projects) — never as a general accent  `[human-required]`
- Titles/logotype render in Cinzel, body/readouts in Spectral; no faux-Greek display font appears  `[human-required]`
- The glaze toggle switches `data-theme` between red-figure (dark) and black-figure (light), and
  every visible element stays legible in both  `[human-required]`
- `npm run build` completes with exit code 0 after the restyle  `[automated]`

---

## Feature: Command bar (top)

A full-width bar above the meander register:
- **POLIS** logotype (Cinzel, wide tracking) + city name.
- **Cycle N** readout, the **glaze toggle** (red-figure · black-figure), the **Run Cycle** button
  (terracotta), and a **Menu** button at the far upper-right opening settings / return-to-home.

**Done when:**
- The command bar shows the POLIS logotype, the current cycle, Run Cycle, the glaze toggle, and a
  Menu button anchored at the far upper-right  `[human-required]`
- The Menu button opens navigation to settings and the home screen  `[human-required]`
- Run Cycle advances a cycle and is disabled while a cycle is resolving  `[human-required]`

---

## Feature: Quadrant layout

`GameView` is a two-column grid under the command bar. The **left rail** (narrow) splits evenly
into **Factions** (top) and **Projects** (bottom). The **main panel** (wide, right) fills the rest
and splits evenly into the **Mayor command panel** (top) and the **Active Events & Chronicle** band
(bottom). The two columns share the horizontal midline.

**Done when:**
- The screen reads as four regions: Factions (top-left), Projects (bottom-left), Mayor (top-right),
  Active Events & Chronicle (bottom-right), with the left rail narrower than the main panel  `[human-required]`
- The left rail's two panels and the main panel's two panels are each divided evenly  `[human-required]`
- The layout holds at desktop/HD widths without horizontal scroll; panels scroll internally when
  their content overflows  `[human-required]`

---

## Feature: Factions panel (top-left)

Domain-grouped, expandable faction browser — **behaviour unchanged** from the prior pass (collapsible
domain headers with `utilization / cap` fill bar; faction blocks lead with integer **level**
`int(rating)`, leader name, traits, last action, and an Audience button), re-homed to the top-left
and restyled per the art direction (domain headers as group registers, capacity bar uses the
meander fill).

**Done when:**
- Factions render grouped by `domain_primary` with collapsible domain headers showing
  `utilization / cap` and a proportional (meander-filled) bar; unknown domain → "Other" group  `[human-required]`
- A faction block leads with the **integer level** (not the raw `rating` float), and shows leader,
  traits, last action, and an Audience button  `[human-required]`
- The faction block does not present the multi-decimal `rating` as its primary number  `[automated]`

---

## Feature: Projects panel (bottom-left)

The domain-grouped **base-project stack** panel — **behaviour unchanged** from the projects
domain-grouping pass (a group header per domain in faction-panel order; pooled `Name ×N` row plus an
optional in-flux front row for a building/damaged top; click opens the read-only details modal),
moved from the right column to the bottom-left and restyled (build bar = meander fill; a **damaged**
front row uses the oxblood bar).

**Done when:**
- The bottom-left shows a group header for every domain in faction-panel order ("Other" for an
  unmatched stack), each collapsible; an empty stack shows "No projects"  `[human-required]`
- A pristine pool shows `Name ×N`; a building top shows its build `progress`% bar; a damaged top
  shows its health `progress`% bar in **oxblood**, visually distinct from a build bar  `[human-required]`
- Clicking a stack opens the read-only details modal (progress/health bar, count, completed,
  domain, core fields)  `[human-required]`
- The projects API returns one stack per domain carrying `count`, `completed`, `progress` —
  `tests/test_projects_api.py`  `[automated]`

---

## Feature: Mayor command panel (top-right)

The Mayor dashboard, rebuilt as the command centre. Two columns inside the panel:

- **Left column** — the **Mayor — <leader>** title, then **Treasury** (gold, income, spent), then
  **Action Points** (`x / cap`, shown as pips between Spent and the buttons), then the two action
  buttons: **Take Action** (terracotta, opens `MayorActionsModal`) and **Hold Audience** (outline,
  opens the audience with a faction selector).
- **Right column** — **The People · <population>** as a co-header level with the Mayor title (it
  extends up the full panel height), then the **seven scale rows**: Fed, Mood (drunk marker), Health
  (sickly marker), **Piety**, **Unrest**, **Drink** (consumption), **Confidence** — each a band word
  coloured by state (clay = nominal, terracotta = notable, oxblood = danger). Band words/colours
  mirror `engine/needs/bands.py`; piety/unrest/consumption/confidence read the band keys the state
  already serialises (`piety_band`, `unrest_band`, `consumption_band`, `confidence_band`).

The **Standing** (per-faction reputation) and **World** (chaos) blocks are **removed** from this
panel (reputation surfaces via the audience / faction context; chaos is a later home).

**Done when:**
- The Mayor panel shows Treasury (gold, income, spent), Action Points as `x / cap` pips placed
  between Spent and the action buttons, and the **Take Action** + **Hold Audience** buttons  `[human-required]`
- The People readout shows **all seven** scales — Fed, Mood (drunk marker), Health (sickly marker),
  Piety, Unrest, Drink, Confidence — each as its band word, reading the serialised band keys  `[human-required]`
- The People block sits as a co-header beside the Mayor title (not stacked below Treasury)  `[human-required]`
- **No** Standing block and **no** World/chaos block appear in the Mayor panel  `[human-required]`
- `serialize_the_public` exposes `piety_band`, `unrest_band`, `consumption_band`, `confidence_band`
  (the data the readout consumes) — `tests/test_*` (backend, already covered)  `[automated]`
- Take Action opens `MayorActionsModal`; Hold Audience opens the audience with a faction selector  `[human-required]`

---

## Feature: Active Events & Chronicle (bottom-right)

A wide band split into two registers:
- **Active Events** (left) — the events **currently in play** from the live event deck, each a card
  with a beat glyph, name, and **cycles-remaining**; a disaster/conflict event (storm, riot, removal
  coalition) carries the **oxblood** left-rule, a boon/festival the terracotta rule. Sourced from
  the active-events the state serialises; empty → a quiet "The city is calm" placeholder.
- **Chronicle** (right) — the highlight beats of the running log (the existing dramatic-event
  narratives), newest first; Breaks/betrayals in oxblood. (This replaces the old centre-bottom Event
  Log; the full cycle-grouped log remains reachable, the band shows the highlights.)

**Done when:**
- The Active Events register lists the cycles' in-play events from the live deck, each with a name
  and cycles-remaining, and shows the calm placeholder when none are active  `[human-required]`
- A disaster/conflict active event is marked in oxblood; a boon/festival in terracotta  `[human-required]`
- The Chronicle register shows the recent highlight narratives newest-first, with Breaks/betrayals
  in oxblood  `[human-required]`
- The `/state` snapshot serialises `active_events` — each carrying `name`, `cycles_remaining`,
  target, and a disaster/boon flag — so the panel renders live events, not a client-side invention
  (`tests/test_state_active_events.py`)  `[automated]`

---

## Feature: Audience entry points

**Unchanged** from the prior pass — two ways into the `AudienceModal`: the per-faction-card Audience
button (pre-targeted, no picker) and the Mayor panel's **Hold Audience** button (with a faction
selector). Both respect the backend rules (AP cost, cooldown, no audience while a deal is active),
surfaced in the audience flow.

**Done when:**
- A faction card's Audience button opens the audience targeted to that faction (no picker)  `[human-required]`
- The Mayor panel's Hold Audience button opens the audience with a faction selector  `[human-required]`
- Both reach the same audience flow defined in `audience_spec.md`  `[human-required]`

---

## Feature: Dashboard faction table & API cleanup

**Unchanged / retained** from the surgical pass: `DashboardView`'s faction table has no `entrench`
column and leads with integer level; `frontend/src/api.js` has no `commission`/`/projects/commission`.

**Done when:**
- The dashboard faction table has no `entrench` column/reference and leads each row with the integer
  level  `[automated]`
- `frontend/src/api.js` contains no `commission` reference; `npm run build` exits 0  `[automated]`

---

## Feature: Frontend test harness

The frontend's `[automated]` Done-when items had no runner — only `dev`/`build`/`preview`. A minimal
**vitest** harness (`npm run test`) now backs them, so a regression (a re-added `commission`, a raw
`rating` float leaking into the lead readout, a broken band-colour map) fails CI instead of slipping
through. The harness tests two surfaces: **pure component logic** (Options-API methods are plain
functions — `Component.methods.fn.call(...)` runs them without mounting) and **source guards** (read
the `.vue`/`.js` source and assert/deny patterns). The `npm run build` exit-0 item stays a CI build
step (compile-level, not a unit test).

- Input: `frontend/src/` (components, `api.js`).
- Output: `npm run test` (vitest) — green = the criteria below hold.

**Done when:**
- `npm run test` runs the vitest suite and passes  `[automated]`
- A test asserts `frontend/src/api.js` has **no** `commission` / `/projects/commission`, and (the
  surgical-pass item) the source guards integer-level lead — `f.rating` only appears in a
  de-emphasized secondary, never as the primary readout  `[automated]`
- A test exercises `GameView`'s `bandClass()` — danger bands → `danger`, notable → `accent`, nominal
  → `''` — so the seven-scale colour map is regression-guarded  `[automated]`
- A test exercises the projects-stack helpers (`poolCount`, `frontKind`) for pristine/building/damaged
  tops  `[automated]`
