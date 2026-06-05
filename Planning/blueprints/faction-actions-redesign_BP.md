# Blueprint: Faction + Actions Redesign (demo)
Spec: Planning/specs/actions_spec.md · faction-behavior_spec.md · cycle-runner_spec.md
Reference: Planning/reference/data-models.md · formulas.md
Date: 2026-06-03

---

## Builder instructions
- Execute steps in order. Do not skip, reorder, or read ahead into the next slice.
- Check off each step when complete: [ ] → [x]
- One step = one logical concern. Deviation: note it inline and keep going. Stuck: stop immediately, report where and why — do not try alternative approaches.
- Test command: `cd backend && py -m pytest tests/ -q`
- This is a **rework**: existing tests encode the OLD behavior (Block, entrench, collapse). When a slice removes that behavior, delete/rewrite the corresponding old tests — a redesign making old tests fail is expected; leaving stale tests is not.

---

## Slice 1: Data model + formulas foundation
**Scope:** Faction is `rank` (float 1–10) + `health`; entrench/floor/Block/power-vacuum fields gone; formulas use the new grow curve and Σ-level utilization.

### Step 1: Trim the Faction/Domain/WorldState models
**Build:** In `engine/models.py`: clamp `rating` to 1.0–10.0; remove `entrench`, the stored `floor` field, `active_block_target`, `action_cancelled`, `action_downgraded`; keep the `floor_rating` property (`int(rating)`) and add a `level` alias for it. Remove `power_vacuums` from `WorldState`. Update `reset_cycle_state()` to drop the removed cycle-only fields.
**Test:** `py -c "from engine.models import Faction"` imports clean; grep shows no `entrench`/`active_block_target` in models.py.
**Done When:** Models construct with only `rank`+`health` as faction stats; removed fields are gone.
**Stuck If:** A removed field is referenced by a constructor default that can't resolve.
- [x] Complete

### Step 2: Update serialization + loaders + schemas + data
**Build:** In `serializer.py`, `loaders.py`, `api/schemas.py`: stop reading/writing `entrench`, `floor`, `active_block_target`, `power_vacuums`. In `data/factions.json` and `data/world_state.json`, remove those keys if present.
**Test:** `py main.py --cycles 1` loads and runs without KeyError/AttributeError on the removed fields.
**Done When:** A game loads, serializes, and round-trips with the trimmed model.
**Stuck If:** Loader requires a removed field and the default is unclear.
- [x] Complete

### Step 3: Rewrite formulas
**Build:** In `engine/formulas.py`: set the rank ceiling to 10.0 (`RANK_MAX`/`RATING_MAX`); replace `grow_increment` with `1/(level+1)`; remove the faction-weight table; add/standardize a domain-utilization helper that sums faction **level** (`int(rank)`). Keep the roll as `d20 + floor(rating)`.
**Test:** write/update `tests/test_formulas.py`.
**Done When:** see committed test below.
**Stuck If:** the weight table is referenced somewhere outside formulas that this step can't reach (note it for Slice 3/4).
- [x] Complete

### Step 4: Commit formulas tests
**Build:** In `tests/test_formulas.py`, assert: `grow_increment(level)==1/(level+1)` for levels 1–9; rank clamps at 10.0; utilization of a domain = Σ of member levels.
**Test:** `py -m pytest tests/test_formulas.py -q`
**Done When:** all three pass.
**Stuck If:** an assertion fails and the formula intent is ambiguous.
- [x] Complete

---
⛔ End of Slice 1. Run **inspector** on this slice before continuing.

---

## Slice 2: Action resolution
**Scope:** The five faction actions (Grow/Protect/Aid/Harm/Steal) resolve per actions_spec; Block is gone.

### Step 1: Grow
**Build:** In `engine/actions/faction.py`: Grow adds `1/(level+1)` to `rank` (cap 10.0); hard-block (no gain) when `domain.utilization >= domain.cap`; when rank crosses an integer, raise level and emit a Dramatic level-up `CycleEvent`.
**Test:** covered by Step 6 tests.
**Done When:** Grow increments, caps, blocks-at-cap, and fires level-up correctly.
**Stuck If:** the cap/utilization value isn't available at resolution time.
- [x] Complete

### Step 2: Protect + Aid
**Build:** Protect → `actor.health = min(100, health+50)` (remove any round-long brace modifier). Add **Aid** → `target.health = min(100, +25)`, target must be a `Friend`/`allied with` ally; allowed cross-domain.
**Test:** Step 6.
**Done When:** Protect heals self +50; Aid heals an ally +25 and only accepts ally targets.
**Stuck If:** no relationship/ally lookup helper exists to validate Aid targets.
- [x] Complete

### Step 3: Harm → health
**Build:** Harm (contested) damages target faction `health`: decisive −30, partial −15, fail 0; floor at 0. Target must be same-domain and **not level 1**. Reaching 0 health is handled by the Break in Slice 4 — for now just floor at 0 and flag it.
**Test:** Step 6.
**Done When:** Harm reduces health by tier, never below 0, refuses level-1 / cross-domain targets.
**Stuck If:** unclear how resolution signals "health hit 0" to the cycle layer.
- [x] Complete

### Step 4: Steal → rank transfer
**Build:** Steal (contested) transfers rank = `0.5/(attacker_level+1)` (decisive full, partial half); actor `+`(cap 10), target `−`(floor 1.0). Same-domain, not level 1.
**Test:** Step 6.
**Done When:** transfer amount, floor/cap, and target guards correct.
**Stuck If:** attacker level vs target level usage is ambiguous (spec: attacker's level).
- [x] Complete

### Step 5: Remove Block action
**Build:** Delete the Block branch from action resolution and any `Block` enum/handler in `engine/actions/`. Remove the `Block`-setting logic.
**Test:** grep shows no `Block` action handler remains.
**Done When:** Block is not a resolvable action.
**Stuck If:** Block is referenced by cycle/resolution (expected — Slice 4 removes the check; just remove the action here).
- [x] Complete

### Step 6: Commit action tests
**Build:** Rewrite `tests/test_actions.py` and replace `tests/test_harm_block_steal.py` (drop Block) with committed tests: Grow increment+cap+level-up+cap-block; Protect +50 cap; Aid +25 ally-only + cross-domain; Harm −30/−15/0 + floor + level-1 guard + same-domain; Steal `0.5/(level+1)` transfer + half-partial + floor1/cap10 + level-1 guard.
**Test:** `py -m pytest tests/test_actions.py -q`
**Done When:** all action criteria pass; no Block test remains.
**Stuck If:** a contested-outcome helper can't be forced to decisive/partial/fail for deterministic tests.
- [x] Complete

---
⛔ End of Slice 2. Run **inspector** on this slice before continuing.

---

## Slice 3: Behavior engine
**Scope:** Weights/modifiers/targeting match faction-behavior_spec v4; Aid is selectable; aggression skips level-1.

### Step 1: Weights + modifiers
**Build:** In `engine/npc/behavior.py`: `BASE_WEIGHTS` drop `Block`, add `Aid: 10`. Update trait modifiers (drop Block columns; add Aid to `defensive`, `trusts X`, `allied with X`). State modifiers: remove the `entrench` row; near-cap row uses Σ-level utilization; add "ally at health<50 → Aid +25".
**Test:** Step 3.
**Done When:** weights/modifiers reflect the spec; no `Block` key remains.
**Stuck If:** a removed modifier is referenced elsewhere in behavior.
- [x] Complete

### Step 2: Targeting
**Build:** Aggression target selection (Harm/Steal) excludes level-1 factions and is same-domain; if no eligible target, drop the aggression and re-select. Add Aid target selection (lowest-health ally; Friend/`allied with`; cross-domain). Remove Block target selection.
**Test:** Step 3.
**Done When:** Harm/Steal never select a level-1 target; Aid selects an ally or isn't chosen.
**Stuck If:** ally lookup or domain membership isn't accessible in targeting.
- [x] Complete

### Step 3: Commit behavior tests
**Build:** In `tests/test_npc_and_eoc.py` (or a new `tests/test_behavior.py`): assert `Block` not in weights; Aid present; Harm/Steal target selection skips a level-1 faction; Aid picks the lowest-health ally.
**Test:** `py -m pytest tests/test_npc_and_eoc.py -q`
**Done When:** behavior tests pass.
**Stuck If:** targeting is non-deterministic and can't be seeded.
- [x] Complete

---
⛔ End of Slice 3. Run **inspector** on this slice before continuing.

---

## Slice 4: Cycle runner — remove Block/collapse, add Break
**Scope:** No Block check, no faction collapse/power-vacuum; a faction at 0 health Breaks (75/25) and lives on.

### Step 1: Strip Block + collapse + power-vacuum from the cycle
**Build:** In `engine/cycle/resolution.py` remove the Block-check (2a) phase. In `engine/cycle/end_of_cycle.py` + `runner.py` remove the faction-collapse check and the power-vacuum step. In `engine/events/cascades.py` remove the faction-collapse → power-vacuum cascade (neuter or delete; keep unrelated chaos if any). Initiative includes all factions (drop the `status != "destroyed"` filter). End-of-cycle utilization = Σ level.
**Test:** `py main.py --cycles 5` runs without error.
**Done When:** no Block/collapse/power-vacuum code paths execute.
**Stuck If:** cascades.py couples collapse with other live behavior that can't be cleanly separated.
- [x] Complete

### Step 2: Implement Break resolution
**Build:** When an action brings a faction to 0 health (signaled from Slice 2), resolve a Break immediately: roll 75% → `rank = (level-1).0` (reprieve, no change, if level==1); 25% → replace leader via the leader-generation helper, new leader `status="weakened"` (1 cycle); then `health = 75`; emit a Dramatic Break `CycleEvent`. Use a seam (injectable RNG / helper) so tests can force the branch.
**Test:** Step 3.
**Done When:** Break resets health to 75, never removes the faction, applies exactly one consequence, level-1 reprieve holds.
**Stuck If:** no leader-generation helper exists and creating a minimal one isn't obvious — stop and report.
- [x] Complete

### Step 3: Commit cycle + Break tests
**Build:** Update `tests/test_cycle.py`; add Break tests (`tests/test_break.py`): health→0 resets to 75 and faction still present; forced level-drop sets `rank=(level-1).0`; forced leader-death installs a weakened leader; level-1 Break keeps level 1; over N forced rolls the split ≈75/25. Keep/adjust: `world.cycle += 1`, N calls → `cycle==N`, utilization=Σlevel, `CycleResult` shape. Remove `test_cap_and_fill.py` weight-table assertions; update to Σ-level.
**Test:** `py -m pytest tests/test_cycle.py tests/test_break.py -q`
**Done When:** all cycle + Break criteria pass.
**Stuck If:** the RNG seam can't force a Break branch deterministically.
- [x] Complete

---
⛔ End of Slice 4. Run **inspector** on this slice before continuing.

---

## Final Slice: Full verification + cleanup
**Scope:** Whole suite green, no stale old-behavior tests, headless run clean.

### Step 1: Purge stale references
**Build:** Grep the whole `backend/` for `entrench`, `active_block_target`, `Block`, `power_vacuum`, `collapse`, the old weight table — remove any lingering references in code, tests, and data. Update `Planning/reference/architecture.md` if a subsystem (cascades/collapse) was removed.
**Test:** grep returns nothing live; `py -m pytest tests/ -q`.
**Done When:** no stale references; suite collects with no import errors.
**Stuck If:** a reference is load-bearing for an unrelated subsystem.
- [x] Complete

### Final Step: Verify spec Done when items
**Build:** No new code. Confirm every `**Done when:**` in actions_spec, cycle-runner_spec is met by a committed test.
**Test:** `cd backend && py -m pytest tests/ -q` (full suite) + a headless `py main.py --cycles 10` for smoke. Capture output.
**Done When:** every `[automated]` criterion passes via its committed test; headless run completes with Breaks/level-ups visible and no faction removed.
**Stuck If:** an automated criterion fails and the cause isn't clear from output.
- [x] Complete

---
⛔ Final slice complete. Run **inspector** for final sign-off.
