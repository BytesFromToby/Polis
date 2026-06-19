# Blueprint — Pottery UI (quadrant relayout + Geometric-pottery restyle)

**Spec:** `game-ui_spec.md`. **Reference:** `reference/ui-art-direction.md`. **Decision:**
`decisions/2026-06-17-pottery-ui.md`.
**Build cmd:** `cd frontend && npm run build` (exit 0). **Run:** `cd backend && py -m uvicorn
api.server:app --reload` → http://localhost:8000. **Backend test:** `cd backend && py -m pytest tests/ -q`.

A UI build: most Done-when items are `[human-required]` (the inspector drives the app with
**playwright** and captures screenshots per CLAUDE.md). Each slice ends with `npm run build` green;
the backend suite must stay green where a slice touches Python (Slice 4 only).

Four slices, all `[inspect]`. Slice 1 reskins the whole app cheaply; 2 relays out; 3 rebuilds the
Mayor panel; 4 adds Active Events (the one slice with a backend touch).

---

## Slice 1 — Pottery token swap + band chrome + fonts  `[inspect]`

**Build**
1. **Tokens** (`frontend/src/style.css`): remap the `:root` semantic tokens to the pottery
   primitives per `reference/ui-art-direction.md` — keep every token *name*, change values:
   `--bg`→glaze-900, `--bg-raised`/`--surface`→glaze-800/700, `--border`→glaze-line,
   `--accent`/`--accent-strong`/`--accent-weak`→terra-500/400/600, `--on-accent`→glaze-900,
   `--accent2`→terra-400, `--danger`→oxblood, `--text`→clay-100, `--muted`→clay-400. Update the
   header comment (drop "Wine-Dark").
2. **Two-glaze theme:** add a `:root[data-theme="light"]` block (black-figure: clay ground, glaze
   figures) overriding the same token names. Default (no attr / `dark`) is red-figure.
3. **Fonts:** add Cinzel + Spectral (via `index.html` `<link>` to Google Fonts, or an `@import`);
   set `body` to Spectral, `h1/h2/h3` and a new `.logotype`/`.cinzel` util to Cinzel.
4. **Band chrome utilities:** add reusable `.mdr` (meander strip) and `.zig` (zigzag) classes using
   the SVG data-URI patterns from the reference, plus a `.bar`/`.bar-fill` meander bar-fill and an
   `.bar-fill--ox` oxblood variant. These are applied in later slices.

**Test / evidence**
- `npm run build` exits 0; the dev server renders the app fully in pottery colours (no verdigris/
  wine anywhere) — screenshot.  → *Art-direction Done-whens*.
- Toggle `data-theme="light"` on `<html>` (devtools) and confirm both themes stay legible — screenshot.

**Stuck if:** a component hard-codes a colour instead of reading a token (it won't reskin) — grep
the `.vue` files for raw hex; log any offenders for a follow-up (don't chase them all in this slice).

---

## Slice 2 — Command bar + quadrant relayout  `[inspect]`

**Build** (`frontend/src/views/GameView.vue` — template + scoped CSS)
1. **Command bar:** replace the current top controls with the bar — POLIS **logotype** (Cinzel),
   city name, **Cycle N**, the **glaze toggle** (sets `document.documentElement.dataset.theme`),
   **Run Cycle**, and a **Menu** button at far-right (opens a menu → settings + home via `router`).
2. **Quadrant grid:** restructure `.game-layout`/`.panels` from the 3-column (`panel-left`/
   `-center`/`-right`) into: a narrow **left rail** (flex column: Factions panel top, Projects panel
   bottom, evenly) + a wide **main** (flex column: Mayor panel top, Active Events & Chronicle
   bottom, evenly). Re-home the existing Factions (was left) and Projects (was right) panels into the
   rail; keep their internal markup/behaviour. Frame screen + panels with `.mdr`.
3. Meander/zigzag registers on panel titles + section breaks.

**Test / evidence**
- `npm run build` exits 0; the app shows the four-region quadrant (Factions/Projects rail · Mayor ·
  Events) at HD width, no horizontal scroll — screenshot.  → *Quadrant + Command-bar Done-whens*.
- The glaze toggle flips the theme live; the Menu opens settings/home.

**Stuck if:** the existing panels' scoped CSS assumes the old column ids — rename/rescope rather than
duplicating; keep faction/project behaviour identical (this slice is layout, not behaviour).

---

## Slice 3 — Mayor command panel rebuild  `[inspect]`

**Build** (`GameView.vue` Mayor panel + `MayorActionsModal` entry)
1. **Two-column panel:** left = `Mayor — <leader>` title, **Treasury** (gold/income/spent), **Action
   Points** as `x / cap` pips placed **between Spent and the buttons**, then **Take Action**
   (terracotta → opens `MayorActionsModal`) + **Hold Audience** (outline → audience w/ selector).
2. **The People co-header:** right column, `The People · <population>` header level with the Mayor
   title, then **seven** band rows — Fed, Mood (drunk marker), Health (sickly marker), **Piety**,
   **Unrest**, **Drink** (`consumption_band`), **Confidence** — reading the band keys from
   `the_public` (`piety_band`/`unrest_band`/`consumption_band`/`confidence_band`); colour each
   clay/terra/oxblood by band via a `bandColor()` helper mirroring `engine/needs/bands.py`.
3. **Remove** the Standing (reputation) and World (chaos) blocks from this panel.

**Test / evidence**
- `npm run build` exits 0; the Mayor panel shows Treasury + AP pips + the two buttons (left) and all
  **seven** People scales (right), People as a co-header; no Standing/World block — screenshot.
  → *Mayor-panel Done-whens*.
- Take Action opens the actions modal; Hold Audience opens the audience selector.

**Stuck if:** a band key is missing from the snapshot for a scale — confirm `serialize_the_public`
emits all four new `_band` keys (it does as of v0.3.0); if a save predates them, default to the
neutral band rather than crashing.

---

## Final Slice — Active Events & Chronicle  `[inspect]`  *(backend touch)*

**Build**
1. **Serialize active events** (`backend/serializer.py` + `api/routes/state.py`): add
   `serialize_game_event(ev)` → `{id, name, cycles_remaining, target_id, kind}` where `kind` is
   `disaster` (withhold/health/chaos-negative effects) | `boon` | `neutral`; include the session's
   `active_events` list in the full-state snapshot returned by `get_state` (the session already
   carries them — `api/sessions.py`). New test `tests/test_state_active_events.py`: a session with
   an active `GameEvent` yields it in the serialized state with the four fields.
2. **Active Events panel** (`GameView.vue`, bottom-right left register): render the serialized
   active events — beat glyph + name + `cycles_remaining`; **oxblood** left-rule for `kind==disaster`,
   terracotta for `boon`; calm placeholder when empty.
3. **Chronicle register** (right): the highlight beats of `state.logs` newest-first (reuse the
   existing dramatic-event narratives), Breaks/betrayals in oxblood. The full cycle-grouped log
   stays reachable (existing component / a "full log" affordance).

**Test / evidence**
- `tests/test_state_active_events.py` passes; **full backend suite green** (553 + 1).
- `npm run build` exits 0; with an active storm in play, the panel shows it in oxblood with its
  remaining cycles; the Chronicle shows recent highlights — screenshot.  → *Active Events Done-whens*.

**Stuck if:** the `kind` classification needs effect-introspection that's awkward client-side — do it
in the serializer (it has the `GameEvent.effects`), not the Vue.

---

## Inspector
Fresh-eyes inspector after the Final slice, driving the app with **playwright** (per CLAUDE.md):
load a game, screenshot each region, and check the `[human-required]` Done-whens (quadrant reads as
four regions; pottery palette + meander/zigzag chrome; oxblood only on conflict; seven People scales
present; AP pips between Spent and buttons; Menu/Run Cycle/glaze toggle; Active Events from live
state in oxblood/terra). Verify the two `[automated]` items (`npm run build` exit 0; the active-events
serializer test + full suite). Stamp the blueprint; report + screenshots to `output/inspect/`.

✅ Inspector: PASS — 2026-06-17 — live preview (real game, both themes): pottery quadrant faithful to the v6 mockup; seven People scales surface; AP pips between Spent & buttons; no Standing/World; Active/Chronicle band (2 dramatic beats oxblood-ruled); two-glaze toggle inverts cleanly; npm build green; active-events serializer + 556 backend green. Residuals: live oxblood disaster card unobserved (covered by test), full-log view deferred.
