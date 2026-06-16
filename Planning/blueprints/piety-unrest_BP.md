# Blueprint — Piety + Unrest (two Public scales)

**Spec:** `public-needs_spec.md` (Features: Piety, Unrest), `events_spec.md` (gates + 2 flagships),
`faction-behavior_spec.md` (unrest→Steal), `special-factions_spec.md` (fields + support catalog).
**Decision:** `decisions/2026-06-16-piety-unrest.md`. **Test cmd:** `cd backend && py -m pytest tests/ -q`

Three slices, all `[inspect]`. All new constants importable (tests read, never copy). Each slice
ends with the full suite green.

Integration point is `engine/needs/drift.py::apply_needs` (called from `runner.py` item 5b after
`compute_chain`). It currently takes `(public, out, mayor)`; this build widens it to see
`factions` (temple + guard levels) and the guard-payroll status.

---

## Slice 1 — Piety  `[inspect]`

**Build**
1. **Model** (`engine/models.py`): `ThePublic` gains `piety: int = 50` and `unrest: int = 10`
   (both now — one serialization change). Comments mark them owned by public-needs.
2. **Serialize** (`serializer.py`): `serialize_the_public` adds `piety`, `unrest`, `piety_band`,
   `unrest_band`; `deserialize_the_public` reads them defaulting 50/10 (existing saves load).
3. **Bands** (`engine/needs/bands.py`): add `piety_band(v)` → Godless/Lax/Observant/Devout/Zealous
   and `unrest_band(v)` → Placid/Quiet/Restless/Agitated/Boiling, both on 20/40/60/80 boundaries.
   Add ordered band lists for `band_index` use (like `FED_BANDS`).
4. **Piety driver** (new `engine/needs/scales.py` or in `drift.py`): pure
   `piety_target(factions, population)` — `Σ PIETY_PER_LEVEL × level` over `domain_primary ==
   "temples"`, honoring `withholding` (×0) then `toiling` (×TOIL_MULT) exactly as the food chain;
   `target = clamp(100 × supply / (demand × PIETY_PARITY), 0, 100)`. Constants `PIETY_PER_LEVEL=4`,
   `PIETY_PARITY=1.0`, `PIETY_BLAME = {Godless:1.5, Lax:1.25, Observant:1.0, Devout:0.75,
   Zealous:0.75}`.
5. **apply_needs** (`engine/needs/drift.py`): widen signature to `(public, out, factions=None,
   mayor=None)`. After fed/happy drift+consequences:
   - **Crisis-blame:** scale the **negative** part of `support_delta` by `PIETY_BLAME[piety_band]`
     before applying (positive deltas unscaled). (Compute fed/happy support delta, split sign.)
   - **Piety drift:** `public.piety = clamp(_drift_toward(piety, piety_target(factions,pop)))`.
   - **Zealot tax:** if new piety band == Zealous, support −1 (through the same mayor/public path).
6. **Plumb factions** into `apply_needs` from `runner.py` (item 5b call).

**Test** (`tests/test_piety.py` new)
- Round-trip piety/unrest (defaults 50/10; absent-field saves load) → *needs-state DW*.
- `piety_band` boundaries 20/40/60/80 → the five words → *needs-state DW*.
- `piety_target`: temple-only sum; zero temple levels → 0; a Toiling temple ×1.5, a withholding
  temple 0 → *Piety DW1*.
- Piety drifts by `DRIFT_STEP` when far, no overshoot when near → *Piety DW2*.
- Crisis-blame: a Starving **Godless** city's support drop = 1.5× the same city at Observant;
  positive deltas unscaled → *Piety DW3*.
- Zealot tax: support −1/cycle at Zealous, none at Observant → *Piety DW4*.

**Stuck if:** the crisis-blame split (scaling only negative deltas) collides with the
mayor-reputation path such that the sign is ambiguous — surface rather than guessing.

---

## Slice 2 — Unrest + the City Guard lever  `[inspect]`

**Build**
1. **Unrest target** (`scales.py`): pure `unrest_target(public)` from band-keyed pressure —
   `UNREST_HUNGER=30` (half at Hungry), `UNREST_IMPIETY=20` (half at Lax), `UNREST_CONFIDENCE=20`
   scaled by `-support/50` when `support<0`, `UNREST_DRUNK=10` when `public.drunk`; clamp 0–100.
2. **Asymmetric drift + Guard** (`apply_needs`): after piety —
   - rise toward a higher target by `DRIFT_STEP`, ease toward a lower one by `UNREST_EASE=4`.
   - **Guard suppression:** if `factions["city-guard"]` present (level≥1) and `guard_paid` true,
     `removed = min(unrest, GUARD_SUPPRESS × level)`, `GUARD_SUPPRESS=3`; `unrest -= removed`.
   - **Heavy-handed cost:** if `removed >= GUARD_HEAVY_THRESHOLD (15)`, support −`GUARD_HEAVY_SUPPORT
     (2)` (mayor/public path).
3. **Guard-paid signal** (`engine/mayor/treasury.py`): in `process_treasury_step0` set
   `treasury.guard_paid_this_cycle = (paid >= guard_cost)`. Add the field to `Treasury`
   (default True). Plumb `treasury` (or the bool) into `apply_needs` via `runner.py`.
4. **Behavior** (`engine/npc/behavior.py`): Step-3 — Public `unrest` band ≥ Restless →
   `Steal += UNREST_CRIME_WEIGHT (15)`, +1 step at Agitated, +2 at Boiling. `public` absent → none.

**Test** (`tests/test_unrest.py` new)
- `unrest_target` equals the summed pressure terms for a constructed state (Starving + Godless +
  support −50 + drunk) → *Unrest DW1*.
- Asymmetric drift: +`DRIFT_STEP` toward a higher target, −`UNREST_EASE` toward a lower → *DW2*.
- Guard: present + `guard_paid` → unrest reduced by `GUARD_SUPPRESS×level`; unpaid or no guard →
  not → *DW3*.
- Heavy-handed: a suppression ≥ threshold applies −`GUARD_HEAVY_SUPPORT`; a light one does not → *DW4*.
- Behavior: Restless+ lifts `Steal` weight (captured weight dict), scaling by band → *DW5*.

**Stuck if:** the guard-paid status isn't cleanly knowable at item 5b (treasury step already ran)
— if so the `guard_paid_this_cycle` flag is the seam; don't reach back into gold.

---

## Final Slice — Events: gates + flagships + public-targeted effects  `[inspect]`

**Build**
1. **Public-targeted effects** (`engine/events/event_system.py`): `_apply_single_event_effect`
   handles `tid == "the_public"` with `eff.field` in `{piety, unrest, support, fed, happy, health}`
   → clamp-apply to `ThePublic`. Plumb `public` into `process_active_events` (and its callers in
   `runner.py`). (Closes the long-standing "events can't touch ThePublic" gap.)
2. **Band gates** (`event_system.py` `_matches_trigger`): support `min_/max_piety_band`,
   `min_/max_unrest_band` (reuse the band-index gate logic; `public` is already passed to the roll).
3. **Templates** (`backend/data/events.json`):
   - **The Mob Marches** — `min_unrest_band: "Boiling"`, effects: world chaos +2 (a domain) + the
     public health −5. duration 1.
   - **The Ignored Omen** — `max_piety_band: "Lax"`, effects: the public piety −5 + support −3.
     duration 1.

**Test** (`tests/test_public_scale_events.py` new)
- A public-targeted effect (`the_public`, field `piety`) clamps-applies to `ThePublic` → *events DW*.
- `min_/max_piety_band` + `min_/max_unrest_band` gate sentinels exactly at the boundary
  (`min_unrest_band: "Boiling"` eligible only at Boiling) → *events DW*.
- The Mob Marches: chaos up in the target domain + Public health down on fire → *events DW*.
- The Ignored Omen: piety + support down on fire; never eligible at Observant+ → *events DW*.
- Headless `py main.py --cycles 8` survives; full suite green.

**Stuck if:** plumbing `public` into `process_active_events` ripples into many call sites — if so,
default the param to `None` and only the runner passes it (keep other callers working).

---

## Inspector
Fresh-eyes subagent after the Final slice. Hard calls to re-derive: (a) the piety crisis-blame
modifier scales only negative support deltas; (b) unrest's asymmetric memory (rise 10 / ease 4)
and the Guard lever (suppress without touching the cause, heavy-handed support cost); (c)
public-targeted event effects clamp and the two flagships gate + fire correctly; (d) piety settles
before unrest reads its band. Stamp this blueprint; report to `output/inspect/`.
