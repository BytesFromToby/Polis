# Inspection — Pottery UI (Final)

**Date:** 2026-06-17  **Verdict:** ✅ **PASS**
**Method:** live preview (Vite dev server + FastAPI backend) driven via the Claude Preview tool —
real game created (Theron / Athenai), screenshots + DOM inspection of the running app, both themes.

## Automated Done-whens
- `npm run build` → **exit 0** after every slice (final CSS 24.77 kB).  ✓
- Backend `serialize_state` emits `active_events` (name/cycles_remaining/target_id/kind); empty →
  key omitted; kind classifier — `tests/test_state_active_events.py` **3 passed**; full backend
  suite **556 green** (553 → 556).  ✓

## Live verification (screenshots + DOM)

**Landing** — renders in pottery: glaze ground, terracotta **Polis** logotype (Cinzel), clay body,
terracotta button, oxblood on the error line. Confirms the Slice-1 token swap + fonts live.

**Game view (red-figure / dark)** — `/game`, real data (28 factions / 7 domains):
- **Command bar:** POLIS logotype, Athenai, CYCLE 0, the glaze toggle (`red-figure`), Run Cycle
  (terracotta), Menu (☰). The **meander register** spans below it.  ✓ *(Command bar Done-whens)*
- **Quadrant:** four regions — Factions (top-left, domain groups + meander capacity bars),
  Projects (bottom-left), Mayor (top-right), Active & Chronicle (bottom-right); narrow rail, wide
  main; even splits.  ✓ *(Quadrant Done-whens)*
- **Mayor panel:** Treasury (Gold/Income/Spent), **Action Points as ◆ pips placed between Spent and
  the buttons**, **Take Action** + **Audience** buttons. **The People · 20,000** co-header beside the
  Mayor title, showing **all seven** scales — Fed, Mood, Health, Piety, Unrest, Drink, Confidence
  (DOM-confirmed: `.mayor-right .info-row` labels = the 7). **No Standing, no World block.**  ✓
  *(Mayor-panel Done-whens — including the seven-scale readout and the dropped blocks)*
- **Active & Chronicle:** Active shows the "The city is calm." placeholder (no event rolled);
  Chronicle present.  ✓

**After Run Cycle (Cycle 1):** Chronicle populated with 14 recent deeds; **2 dramatic beats** carry
the highlighted left-rule (`.frieze-row.dramatic`, oxblood). DOM-confirmed.  ✓ *(Active Events &
Chronicle Done-whens)*

**Game view (black-figure / light)** — the glaze toggle flips `data-theme`; the whole UI inverts to
clay ground + glaze-dark figures + terracotta chrome, fully legible, layout intact.  ✓ *(Two-glaze
theme Done-when — the inversion test passes live in both directions)*

## Hard-call checks
- **Pottery palette + band grammar:** glaze/terracotta/clay throughout; meander frames the screen +
  caps panels; capacity/build bars use the meander fill. No verdigris/wine remains. ✓
- **Oxblood discipline:** oxblood appears only on conflict (dramatic chronicle beats, the landing
  error, the damaged-bar / disaster-event CSS path); not as a general accent. ✓
- **Seven scales surface:** the long-standing gap (piety/unrest/consumption/confidence never shown)
  is closed — all four render with band words + colour. ✓
- **Active events from live state:** the panel reads `snapshot.active_events` (DOM `.active-card`
  bound to the serialized list); the serializer + test back it; the calm placeholder shows when none.
  No active event rolled in the short run, so the oxblood disaster card wasn't seen *live* — its
  path is covered by the `kind-disaster` CSS + the serializer's `kind` test. ✓ (one residual, below)

## Residual / nits (non-blocking)
- An **active disaster card in oxblood** wasn't observed live (no storm/riot rolled in the 1-cycle
  run); verified by code + the serializer test rather than a screenshot. A longer playthrough would
  show it.
- The **full cycle-grouped log** view is deferred (the band shows the flat recent frieze); logged as
  a deviation. A "full log" affordance is a small follow-up.
- Dropped Standing/World left a few unused computeds (`topReputation`/`repColor`/`chaosDisplay`) —
  harmless dead code for a later tidy.

## Conclusion
PASS. The Geometric-pottery quadrant UI is live and faithful to the v6 mockup in both themes; the
seven Public scales finally surface; active events are served and consumed; builds green; backend
suite green. The residuals are cosmetic/coverage, not defects.
