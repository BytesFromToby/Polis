# Blueprint — Confidence (the 7th scale's band-consequences)

**Spec:** `public-needs_spec.md` (Feature: Confidence), `faction-behavior_spec.md` (posture
modifier), `events_spec.md` (gates + 3 flagships). **Decision:**
`decisions/2026-06-17-confidence-consequences.md`. **Test:** `cd backend && py -m pytest tests/ -q`

Two slices, both `[inspect]`. **No new state field** — confidence reads `support`. Small slice.

---

## Slice 1 — Confidence bands + faction posture  `[inspect]`

**Build**
1. **Bands** (`engine/needs/bands.py`): `CONFIDENCE_BANDS` over the **−50..+50** range —
   `[(-30,"Hostile"), (-10,"Suspicious"), (10,"Neutral"), (30,"Favorable"), (50,"Beloved")]` +
   `confidence_band(support)` using the existing `_band` helper. (Note: a value above +30 → Beloved
   via the `table[-1]` fallback; `_band` already handles the top band.)
2. **Serializer** (`serializer.py`): add `confidence_band` to `serialize_the_public`'s derived
   display keys (off `support`). No new persisted field.
3. **Behavior** (`engine/npc/behavior.py`): constants `CONFIDENCE_EMBOLDEN_WEIGHT = 10`,
   `CONFIDENCE_COOP_WEIGHT = 10`. In Step 3 (beside the unrest→crime block, where `public` is in
   scope): read `confidence_band(public.support)` —
   - Hostile/Suspicious → `Harm += EMBOLDEN`, `Steal += EMBOLDEN`;
   - Favorable/Beloved → `Harm -= COOP`, `Steal -= COOP`;
   - Neutral → no change. `public is None` → no effect.

**Test** (`tests/test_confidence.py` new)
- `confidence_band` at −30/−10/+10/+30 → Hostile/Suspicious/Neutral/Favorable/Beloved → *Confidence DW1*.
- Captured weights: Hostile public lifts Harm+Steal by `EMBOLDEN`; Beloved damps them by `COOP`;
  Neutral unchanged; `public=None` → unchanged → *Confidence DW2 + behavior row*.
- `serialize_the_public` exposes `confidence_band` off `support`.

**Stuck if:** the band helper mis-handles the negative range (e.g. a value of exactly −30 vs −29) —
re-derive against the spec's boundary table before adjusting.

---

## Final Slice — Confidence events  `[inspect]`

**Build**
1. **Gates** (`engine/events/event_system.py`): add `min_/max_confidence_band` to `_NEED_GATE_KEYS`
   + the band-index checks in `_matches_need_gates` (use `CONFIDENCE_BANDS`/`confidence_band` on
   `public.support`, same pattern as the other bands).
2. **Templates** (`backend/data/events.json`):
   - **The Removal Coalition** — `max_confidence_band: "Hostile"`; effects: a faction `rating +0.3`
     + that domain's `chaos +1`. duration 1.
   - **Effigy in the Agora** — `max_confidence_band: "Suspicious"`; effects: a faction `rating +0.2`
     + the_public `support −2`. duration 1.
   - **Acclamation** — `min_confidence_band: "Beloved"`; effect: the_public `support +5`. duration 1.

**Test** (`tests/test_confidence_events.py` new)
- `min_/max_confidence_band` gate sentinels at the boundary → *events DW*.
- The Removal Coalition eligible only at Hostile, raises the faction's rating + its domain chaos → *events DW*.
- Acclamation eligible only at Beloved, raises Public support → *events DW*.
- Effigy fires at Hostile/Suspicious (rating up + support down) → *events DW*.
- Headless `py main.py --cycles 10` survives; full suite green.

**Stuck if:** a confidence event needs to add a faction *trait* (no event-effect machinery for
that) — keep to `rating`/`chaos`/public-`support` fields; the standing behavior modifier carries
the emboldened posture.

---

## Inspector
Fresh-eyes subagent. Hard calls: (a) the confidence bands map the −50..+50 `support` range
correctly at the boundaries (not the 0–100 pattern); (b) the posture modifier emboldens at
low / damps at high / no-ops at Neutral and with no public; (c) the three events gate on the
correct confidence bands and fire their stated effects; (d) **no new persisted field** — confidence
is purely a view over `support` (round-trip unaffected). Stamp the blueprint; report to `output/inspect/`.
