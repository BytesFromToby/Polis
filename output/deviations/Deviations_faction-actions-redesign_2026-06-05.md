# Deviations — Faction + Actions Redesign (demo)

**Blueprint:** `Planning/blueprints/faction-actions-redesign_BP.md`
**Build completed:** 2026-06-05 (resumed from 2026-06-04 handoff)
**Result:** full suite green — `280 passed`; headless `py main.py --cycles 10` clean (level-ups visible, no faction removed).

---

## Deviations from the blueprint

1. **Atomic refactor — not slice-by-slice testable.** Removing model fields (`entrench`/`floor`/Block flags) breaks every caller at once, so the engine was built as one unit and only goes green at the end. The per-slice ⛔ inspector checkpoints could not run independently; verification is a single end-of-build pass.

2. **Break leader regen uses `status="present"`, not the spec's `"weakened"`.** The existing leadership flow escalates `weakened`→`absent`→replace, which would turn the post-Break recovery window into a leadership crisis. The 1-cycle weakened window was dropped; a regenerated leader is full strength. (Carried from the 2026-06-04 session; unchanged.)

3. **Minimal leader name pool added in `resolution.py`** (`_NEW_LEADER_NAMES`). `end_of_cycle._generate_leader_name` is a separate pool — could be unified later.

4. **Grow no longer heals +3 health.** Health is now moved only by Harm / Protect / Aid (and passive decay). Passive −1/cycle decay is kept; decay-to-0 is caught by the Break sweep.

5. **`WithholdResources` event effect retargeted `entrench` → `health`.** Entrench is gone, so the mayor-triggered "Outside Pressure" event now wears down the breaking-buffer (health) instead of a dead field. Test updated to match.

6. **`engine/events/cascades.py` neutered to a no-op** returning `[]` (rather than deleting it), keeping its import/export valid while collapse cascades are retired.

---

## Items the 2026-06-04 handoff listed as DONE but were not

The handoff marked serialization/loaders/API as complete; two live `Faction(...)` constructions still passed the removed fields and would have crashed at runtime:

- **`loaders.py`** — the default/fallback faction-pair builder still passed `entrench=75, floor=2` (in addition to the JSON loader path the handoff did fix).
- **`api/routes/city.py`** (add-faction route) — still passed `floor=int(req.rating), entrench=75`.
- **`api/schemas.py`** — `FactionPatchRequest.entrench` field removed.

All three fixed this session.

---

## Behavioral note

- **Domain utilization now counts level-1 factions.** `faction_weight(level)` returns `level`, so a level-1 faction contributes `1` to Σ-level utilization (the old exponential table mapped floor 1 → 0). Intentional under the new "cap = level budget" framing.

---

## Out of scope (separate pass)

- **Frontend (`game-ui`, Vue):** still reads `entrench`/`floor` from the API, which no longer returns them. Needs its own architect → build pass (show rank/level + health, drop the entrench bar).
