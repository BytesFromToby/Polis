# Reference: UI Art Direction — Geometric Pottery

As-built design tokens and layout grammar for the play UI. Cited by `specs/game-ui_spec.md`;
not itself testable. Promoted from `proposals/ui-pottery-art-direction.md` (2026-06-10) when the
direction was adopted (decision `decisions/2026-06-17-pottery-ui.md`).

The reference is Geometric-period Attic pottery (~8th c. BC, Dipylon style): stacked horizontal
bands, flat silhouettes, ornament at the edges, calm content in the middle.

## Token architecture

Keep the existing semantic-token layer in `frontend/src/style.css` (`--bg`, `--surface`,
`--accent`, `--danger`, `--text`, `--muted`, …) — only the **primitive values** change
(verdigris→terracotta, ink→glaze-brown, bone→clay, wine→oxblood). Components read the semantic
tokens, so the reskin is a value swap, not a structural rewrite.

## Palette (two inks + ground + one accent — resist a fifth colour)

```css
/* glaze — the dark ground (red-figure / default) */
--glaze-900:#1d130e;  /* page ground            */
--glaze-800:#211712;  /* panel                  */
--glaze-700:#2a1c14;  /* raised band / row hi   */
--glaze-line:#3a2417; /* hairline borders       */
--glaze-row:#26190f;  /* zebra / group header   */
/* terracotta — the figure ink */
--terra-500:#c4744a;  /* primary accent, buttons, emblems */
--terra-400:#d98a54;  /* bright variant, titles/links     */
--terra-600:#8a5a3a;  /* muted ornament, secondary glyphs */
/* clay slip — text on glaze (light-mode ground) */
--clay-100:#e8cfa8;   /* primary text */
--clay-400:#a98a6a;   /* secondary/meta text */
--clay-mut:#8a5a3a;   /* faint meta */
/* oxblood — the one permitted accent, conflict only */
--oxblood:#8a3324;    /* the rule (left-rule on Breaks/disasters) */
--oxblood-txt:#d9694f;/* oxblood text on glaze */
```

Oxblood is reserved for **conflict beats only** — Breaks, broken deals, active disasters, damaged
projects, removal warnings. If a screen wants a fourth hue, the design is wrong, not the palette.

## Two-glaze theme rule

The two historical techniques are the two themes, same motifs, inks swapped (`data-theme` switch,
reusing the existing architecture):
- **Red-figure → dark (default):** terracotta figures on glaze brown-black ground.
- **Black-figure → light:** glaze-black figures on clay ground.

Inversion test: every element must survive having its inks swapped. Dark ships first; light may
follow, but colour choices are constrained by the swap now.

## Band grammar (the layout rule)

Every panel is a stack of horizontal registers, like the vessel:

```
meander border   (ornament band ~13px, repeating SVG)
title band       (inscriptional caps + meta)
content frieze   (the actual UI — calm, minimal ornament)
[zigzag divider] (between content sections)
meander border   (closing band, screen edges)
```

Decorate the chrome; keep content rows calm. Meander frames panel/screen edges; zigzag separates
sections inside content; never ornament inside a content row.

## Patterns (CSS/SVG — no artist needed for chrome)

Meander (Greek key), 16×14 unit, stroke `--terra-500` ~1.5px:
`M2 12 V3 H14 V12 H8 V7`. Zigzag divider, 10×10 unit, stroke `--terra-600` ~1.2px:
`polyline 0,8 5,2 10,8`. The same meander doubles as a **bar fill** for capacity/build/progress
bars: meander pattern over a `--glaze-700` track, terracotta at ~0.5 opacity for the filled
portion (oxblood fill for a damaged/health bar).

## Typography

- **Display / titles / logotype:** Cinzel — inscriptional capitals, wide tracking. POLIS logotype
  is Cinzel at ~0.34em tracking.
- **Body / readouts:** Spectral (serif). UI labels use Cinzel small-caps for register titles.
- **Hard rule — the toga-party trap:** no faux-Greek display fonts (E-as-Σ), no Lithos, no
  Papyrus-the-font, no laurel/column clip-art. The Geometric style is austere; trust it.

## Emblems (later)

One flat two-ink silhouette per **domain** (7 domains now, several faction-less → ~6 emblems;
the proposal's "8" predates the roster restructure). Built from primitives or traced from CC0
Geometric vessels. Faction identity = domain emblem + name + colour treatment. Deferred until the
chrome reskin lands; not required for the layout.
