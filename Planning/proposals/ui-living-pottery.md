# Proposal: Living Pottery — figures, vessels, the procession, and cracks

**Date:** 2026-07-06
**Status:** PROPOSAL — not built, not scheduled. Captured from a visual-design brainstorm.
Builds on the adopted chrome direction in `../reference/ui-art-direction.md` (tokens, band
grammar, two-glaze rule — unchanged by this doc). Promote via a Spec Impact section when
scheduled (see `README.md`).

The chrome reskin gives Polis pottery *framing*; the content inside the frames is still text
and numbers. This proposal is the next layer: the game's actors and events rendered in the
Geometric style itself — flat two-ink figures that scale, move, and wear.

## Problem

The UI is legible but visually inert — a dashboard. The engine produces the most dramatic
content in the game (clashes, betrayals, strikes, collapses) and renders it as log lines.
Meanwhile the chosen art period is uniquely cheap to execute: Geometric pottery is built
from repeatable primitives (triangle torsos, stick limbs, profile heads, bands, processions),
which means a solo developer can generate all of it from a small part kit — no artist, no
per-faction commissions.

## The four features

1. **Figure generator.** Every faction gets a procedurally assembled two-ink silhouette from
   a shared SVG part kit (pose × held object × mount × headgear). Traits drive the parts —
   aggressive holds a spear, corrupt a purse, defensive the big Dipylon shield, chain-role
   factions their tool (net, oar, crook). The faction `id` seeds all random choices, so a
   faction always looks like itself. Leaders are the same kit at portrait scale, always in
   profile; during an audience the leader's pose swaps with mood (receptive / guarded /
   bitter — 3–4 arm/stance variants per skeleton).

2. **Faction vessels.** Each faction card carries a vessel silhouette (amphora / krater /
   kylix by domain) with the faction's figure or domain emblem in its central register.
   The vessel is the faction's face everywhere the faction appears.

3. **The procession** — the event log becomes a horizontal frieze band. Cycle events enter
   as figures walking left-to-right: a builder for project work, two clashing silhouettes
   for Harm, a ship for harbor trade, a torch-bearer for Agitate. Calm events walk past;
   conflict beats stop mid-band and play. **Hover expands** the scene (scale transform) and
   **pulls the text** — the existing narrative line renders as a caption plaque beneath.
   Click focuses the relevant faction card or deal. The prose log remains available; the
   procession is its visual face, not a replacement for the data.

4. **Cracks and staples** — state as surface wear. A broken deal draws a permanent crack
   through that faction's vessel; a later reconciliation adds lead-staple marks straddling
   the crack (the historically real repair technique). Low faction health reads as paint
   wear (a hatching/erosion overlay tracking the health value). A long reign's whole
   betrayal history becomes readable in the chrome without opening a log.

**Motion is rationed like oxblood.** Routine events drift; only oxblood-class beats (Breaks,
broken deals, disasters, removal warnings) get real animation. If everything moves, nothing
does. The house entrance animation is stroke draw-on ("paints itself in") — nearly free via
`stroke-dashoffset`, and it *is* the fiction.

## Medium decision: SVG in the existing Vue frontend

**Chosen: SVG as the entire visual layer, inside the current Vue 3 app.** No framework change.

- **Scales infinitely.** The art is strokes and flat fills — resolution-independent by nature.
- **Themes via the existing tokens.** Every path uses `currentColor` / `var(--terra-500)` etc.
  — the red-figure/black-figure inversion test passes automatically, forever. No hardcoded
  fills anywhere in the kit.
- **Hover/click are DOM events.** Mouseover-expand and click-to-focus need no hit-testing
  math; Vue reactivity drives the SVG tree directly.
- **Stroke-renderable paths** make the draw-on entrance work on anything in the kit.

**Rejected alternatives (recorded so this isn't relitigated):**

| Option | Verdict |
|---|---|
| Canvas / PixiJS as the base layer | Buys performance we don't need at this element count; costs the CSS-token theming, DOM hover, and Vue integration we already have. Kept as a **surgical escape hatch** (see Performance boundary). |
| Game engine (Godot etc.) | Abandons the decoupled web UI + API architecture the engine was built around; massive migration for zero mechanical gain. |
| Raster sprite sheets | Fixed resolution, rectangular occlusion, per-theme re-exports. SVG paths occlude only where painted and re-ink from tokens. |
| Custom glyph/tile font ("ASCII-ish") | Charming and cheap, but an SVG `<symbol>` sprite gives the same reuse with less tooling pain. Revisit only if a text-mode build is ever wanted. |

## Why layering works (the fundamentals, for the record)

Three SVG properties carry the whole design:

1. **Painter's model.** Document order is stacking order — later elements paint on top.
   There is no z-index in SVG; "move this figure in front" is a list reorder, which in Vue
   is template/`v-for` order.
2. **Paths occlude only where painted.** No bounding-box backgrounds: everything outside a
   drawn path is transparent, so a spear-carrier passing a ship covers it only where his
   silhouette actually is, pixel-perfect at any scale.
3. **Group transforms nest and compose.** Each figure is a `<g>` with its own CSS transform
   animation, independent of every other group; an arm swings relative to a torso, the torso
   bobs relative to the figure, the figure walks relative to the band — each animation
   written as if the others didn't exist. Seven figures moving in seven directions is seven
   groups with seven animations.

Animate **CSS transforms and opacity only** (GPU-composited); never animate geometry
attributes (`x`, `d`, `points`) in the hot path.

## Architecture

- **`figures.svg` part-kit sprite** — one file of `<symbol>`s: torsos, arm poses, heads,
  held objects, mounts (ship, chariot), vessel shapes, crack paths, staple glyphs, ornament
  units. Every figure in the game is a handful of `<use>` references.
- **`factionFigure(faction) → part list`** — a pure function plus a trait→part manifest
  table. Seeded by faction `id` (stable across sessions). Feeds faction cards, leader
  portraits, procession actors, and (later) the crowd band from one kit.
- **`FactionVessel` component** — three layers: vessel shape, emblem/figure register,
  damage overlay slot. Cracks come from a library of ~6 hand-drawn/traced jagged paths,
  masked to the vessel; each broken deal appends one, chosen by hash of the deal `id`
  (deterministic, permanent). Staples are paired-dot glyphs placed along the crack path.
- **`ProcessionBand` component** — a horizontal SVG strip mapping structured events to
  scene templates (walker / clash pair / ship / torch-bearer / …). Entrance = draw-on +
  CSS translate walk. A `severity` switch selects drift-past vs stop-and-play.
- **Structured event emission (the one engine touchpoint).** The current log is narrative
  strings; a sentence can't be animated. The engine already knows the structure at the
  moment it writes the prose — emit it alongside, additively:

  ```json
  { "type": "harm", "actor": "quaymen", "target": "saltroad_houses",
    "outcome": "success", "severity": "conflict", "narrative": "The Quaymen strikes hard…" }
  ```

  Snapshot-friendly, additive, testable. The narrative line becomes the hover payload.

## Performance boundary

SVG-in-DOM is comfortable to roughly 1–2k live nodes. The procession (a dozen scenes × ~6
elements) and 28 vessels don't approach it. The only future feature that could is the
**crowd band** (hundreds of tiny Public figures); if it lands, render that one strip to a
`<canvas>` stamping the same part-kit shapes, and keep everything else SVG. Hybrid at the
component boundary — never a rewrite.

## Build order (each step independently shippable)

1. **Token reskin** — pottery palette values into `frontend/src/style.css` (already specced
   in `ui-art-direction.md`; everything looks wrong until the ground is glaze).
2. **Part kit + generator playground** — a standalone page rendering all 28 factions from
   their real JSON, to judge silhouette readability before any wiring.
3. **`FactionVessel`** into the existing faction cards — first visible payoff, no layout change.
4. **Structured event emission** (backend) → **`ProcessionBand`**, initially alongside the
   text log, replacing it when it proves itself.
5. **Cracks/staples** — small, cheap, ships whenever.

## Adjacent ideas captured, not scoped here

From the same brainstorm, deliberately out of this proposal's scope — each is a candidate
follow-on once the part kit exists:

- **Crowd band** — the Public as a persistent frieze of tiny figures whose density/posture
  encode the seven scales (standing/seated/prone, arms raised, facing the temple register).
- **Map as wraparound frieze** — the city in stacked registers (acropolis / agora / walls /
  harbor) rendering live state; bands double as domain filters. No top-down map.
- **Interstitial panels** — one composed full-screen "museum piece" per big beat (election,
  coup, title climb, death); highest feel-per-pixel available.
- **Museum frame** — the run as an excavated krater; game over writes the placard
  (pairs with the unreliable-Chronicle idea in the gameplay brainstorm).
- **Ostraka notifications** — toasts as pottery shards; pre-builds the visual system for a
  future ostracism mechanic.
- **The pot spins** — Run Cycle rotates the vessel; one revolution = one cycle; scrubbing
  back re-reads past cycles (deterministic snapshots make true re-render possible).
- **State-driven glaze swap** — black-figure interstitials for deaths; theme inversion
  during stasis/civil war.
- **Sound** — sparse aulos/lyre stings; the Public's ambient murmur mixed live from the
  scales.

## Spec Impact (rough — finalize when scheduled)

- `specs/game-ui_spec.md` — new sections: faction vessel rendering, procession band
  (hover-expand, pull-text, click-to-focus), damage overlays. Done-when items for hover
  payload correctness and deterministic figure stability.
- `reference/ui-art-direction.md` — v2 appendix: part-kit inventory, motion-rationing rule,
  crack/staple grammar.
- `specs/cycle-runner_spec.md` (or `events_spec.md`) — the structured-event emission
  contract (additive alongside narrative lines).
- No changes to engine mechanics, data models, or the LLM layer.

## Open questions

- Vessel shape assignment: by domain (7 fixed shapes) or per-faction variety within a domain?
- Does the procession show *every* event or a curated cut (routine consolidations collapsed
  into a single walker)? Curated is likely right; the full log stays one click away.
- Crack permanence across a fulfilled-after-broken relationship arc — do staples ever fully
  "heal" at maximum reputation, or is wear strictly append-only? (Append-only is the more
  honest metaphor and the simpler code.)
- Where does the playground page live — a dev-only route in the Vue app, or a static page
  under `docs/Polis Design/`?
