# Proposal: UI Art Direction — Geometric Pottery

**Date:** 2026-06-10
**Status:** PROPOSAL — not built, not scheduled. Captured from a design discussion before a
development pause. The current UI is a dev instrument and is slated for a full redo; this is
the candidate visual direction for that redo.

## Relationship to the existing design system

`docs/Polis Design/colors_and_type.css` already defines a complete token set: **Wine-Dark /
Papyrus** (verdigris + bronze + wine, Cinzel / Spectral / Cormorant Garamond). This proposal is
a *different direction*, not an extension. What transfers and what breaks:

| Wine-Dark element | Pottery verdict |
|---|---|
| Cinzel (inscriptional caps, display) | **Keep** — exactly right for the logotype/headers |
| Spectral (body serif) | **Keep** — readable body text is orthogonal to theme |
| Wine/oxblood as danger | **Keep** — maps directly to the deep red accent below |
| Bone / papyrus neutrals | **Nearly keep** — they're one nudge from clay-slip cream |
| Verdigris as signature accent | **Break** — pottery has no green; this is the fork in the road |
| Ink (wine-tinted black) neutrals | **Replace** with glaze brown-blacks (warmer, browner) |

Open question (the real decision when this is picked up): full replacement, or merge — keep the
Wine-Dark token *architecture* (primitives → semantic tokens, `data-theme` switch) and swap the
primitive values. The architecture is good; reuse it either way.

## The reference

Geometric-period Attic pottery, ~8th c. BC — the Dipylon kraters and amphorae (funerary vessels
with procession friezes). **Not** the later black-figure/red-figure mythological scenes; the
Geometric style is the UI-friendly one:

- Composition is **stacked horizontal bands**, each with one job: ornament border, figure
  frieze, solid ground. That is panel chrome, dividers, and content rows — already a layout system.
- Figures are **flat silhouettes** — i.e. affordable, scalable, in-house-drawable iconography.
- Ornament density lives at the **edges**; the figure bands stay legible. Same discipline a
  data-dense sim needs: decorate the chrome, keep content calm.
- A procession frieze is a timeline. The Event Log *is* a procession of deeds.

Source material: The Met's open-access collection (CC0) has high-res Geometric vessels —
motifs can be traced/redrawn directly and legally. Wikimedia Commons likewise.

## The two-glaze theme rule

The two historical techniques are the two UI themes, same motifs with the inks swapped:

- **Red-figure → dark mode (default):** terracotta figures on glaze brown-black ground.
- **Black-figure → light mode:** glaze-black figures on clay ground.

**The inversion test:** every visual element must survive having its inks swapped. Decide this
now even if only dark ships first — it constrains all color choices and is the design conceit
reviewers will notice.

## Palette (two inks + ground + one accent — resist a fifth color)

Values from the conversation mockup; refine on real screens, keep the *structure*:

```css
/* glaze (dark ground) */
--glaze-900: #1d130e;   /* page ground            */
--glaze-800: #211712;   /* panel                  */
--glaze-700: #2a1c14;   /* raised band / highlight row */
--glaze-line: #3a2417;  /* hairline borders        */

/* terracotta (the figure ink in dark mode) */
--terra-500: #c4744a;   /* primary accent, buttons, emblems */
--terra-400: #d98a54;   /* bright variant, chips/links      */
--terra-600: #8a5a3a;   /* muted ornament, secondary glyphs */

/* clay slip (light ground / dark-mode text) */
--clay-100: #e8cfa8;    /* primary text on glaze; light-mode ground ~#e0bd8d */
--clay-400: #a98a6a;    /* secondary text on glaze */

/* oxblood (the single permitted accent — danger/conflict beats only) */
--oxblood: #8a3324;     /* Breaks, broken deals, removal warnings */
```

The discipline is the period's: terracotta, glaze-black, clay ground — and oxblood as the one
deviation, reserved for conflict. If a screen needs a fourth hue, the design is wrong, not the
palette.

## Band grammar (the layout rule)

Every panel is a stack of horizontal registers, like the vessel:

```
meander border        (ornament band, ~14px, SVG pattern)
title band            (inscriptional caps + meta)
zigzag divider        (secondary ornament, ~10px)
content frieze(s)     (the actual UI — calm, minimal ornament)
meander border        (closing band)
```

This makes screens design themselves: new screen = decide its registers. Section breaks inside
content use the zigzag; panel edges use the meander; never ornament inside a content row.

## Pattern specs (all CSS/SVG — no artist required for chrome)

Meander (Greek key), 16×14 repeating unit, stroke `--terra-500` at 1.6px:

```svg
<pattern id="meander" patternUnits="userSpaceOnUse" width="16" height="14">
  <path d="M2 12 V3 H14 V12 H8 V7" fill="none" stroke="#c4744a" stroke-width="1.6"/>
</pattern>
```

Zigzag divider, 10×10 unit, stroke `--terra-600` at 1.2px:

```svg
<pattern id="zig" patternUnits="userSpaceOnUse" width="10" height="10">
  <polyline points="0,8 5,2 10,8" fill="none" stroke="#8a5a3a" stroke-width="1.2"/>
</pattern>
```

Same patterns double as **bar fills** (domain capacity, build progress): patterned band over a
solid `--glaze-700` track, terracotta overlay at ~0.55 opacity for the filled portion.

## Silhouette emblems (domains and glyphs)

- Two inks only, flat fills, no outlines-with-fills, no gradients ever.
- Built from primitives (circles, triangles, simple paths) or traced from CC0 Geometric
  vessels. Period motif vocabulary: horse, ship (Harbor), shield/concentric circles (Military),
  amphora (Trade), tripod (Temples), lyre (Academy), meander fragment, mourner figure.
- One emblem per **domain** (8), not per faction (41). Faction identity = domain emblem +
  name + color treatment. Leader portraits, if ever, are post-revenue.
- Event-log beat glyphs come from the same set, small (~22px), single ink.

## The Chronicle (event log treatment)

The log is renamed/styled as a frieze: each entry a row in the procession. Ordinary deeds in
`--clay-400`; **dramatic beats** (level-ups, Breaks, broken deals) get the highlighted-band
treatment — `--glaze-700` row, 3px left rule, leading glyph, brighter text. Breaks and
betrayals use `--oxblood`. This is also where the LLM-chronicler idea lives (see discussion in
`crisis-and-stance.md` adjacency: 3-line in-character cycle summaries, stub fallback to plain log).

## Typography

- **Display / titles:** Cinzel (already selected in Wine-Dark) — inscriptional capitals,
  letter-spaced. The POLIS logotype: Cinzel, wide tracking.
- **Body:** Spectral (already selected). UI labels can stay a clean sans if mixing reads better.
- **Hard rule — the toga-party trap:** no faux-Greek display fonts (anything where E mimics Σ),
  no Lithos, no Papyrus-the-font, no laurel clip-art, no marble columns. The Geometric style is
  austere; trust it. If it would fit a gyro shop menu, it's out.

## Budget implication

This direction moves all UI chrome + the 8 domain emblems to in-house SVG work. The remaining
commission shortlist: **Steam capsule/key art only** (~$300–800) — and "flat Geometric pottery
procession" is a cheap, tight brief because the style is flat and references are public domain.
Music is separately covered.

## Open questions

- Replace Wine-Dark wholesale, or port pottery primitives into its token architecture?
  (Lean: keep architecture, swap primitives — `colors_and_type.css` structure is sound.)
- Light mode ground: pure clay (#e0bd8d-ish) may be too warm for long reading sessions —
  test a desaturated slip.
- Texture: a faint clay grain on panel grounds could sell it — or violate the flat discipline.
  Prototype once, decide once.
- The audience screen: pottery figures are always in profile — two facing silhouettes framing
  the conversation is the obvious composition. Worth a dedicated mock before committing.
- Exact motif → domain mapping (8 assignments) — do alongside `reference/theming.md`.
