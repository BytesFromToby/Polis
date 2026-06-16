# Blueprint — Withhold (the supply-interruption primitive)

**Spec:** `actions_spec.md` (§Withhold), `public-needs_spec.md`, `faction-behavior_spec.md`,
`events_spec.md`, `cycle-runner_spec.md`. **Decision:** `decisions/2026-06-16-withhold.md`.
**Test cmd:** `cd backend && py -m pytest tests/ -q`

Two slices, both `[inspect]`. Slice 1 delivers faction-chosen Withhold end to end (action →
chain ×0 → anger weighting). The Final slice adds event-forced withhold and the cycle reorder.
Each slice ends with the full suite green.

Constants (new, in `engine/needs/chain.py` or `engine/npc/behavior.py` as noted): keep them
importable — tests must read them, never copy values.

---

## Slice 1 — Faction-chosen Withhold  `[inspect]`

**Build**

1. **Model** (`engine/models.py`): add `withholding: bool = False` to `Faction`, with a comment
   mirroring `toiling` (cycle-only; set by Withhold resolution / event; consumed by the needs
   step; reset in the runner; never persisted). Do **not** add it to `serialize_faction` (cycle-only,
   like `toiling`).
2. **Chain ×0** (`engine/needs/chain.py`): in `compute_chain`, a producer with `f.withholding`
   contributes 0 harvest and a processor with `f.withholding` contributes 0 capacity — checked
   **before** the Toil multiplier so Withhold wins even if both flags are set. (Simplest: `if
   f.withholding: contribution = 0` before the `if f.toiling` branch, in both the producer loop
   and the processor-capacity loop.)
3. **Action resolver** (`engine/actions/faction.py`): add `resolve_withhold(faction)` — sets
   `faction.withholding = True`, returns a `success` `ActionResult("Withhold", faction.id, None,
   "success", narrative=...)`, no rank/health/project effect. Export in
   `engine/actions/__init__.py`. Dispatch in `engine/cycle/resolution.py`: `if action ==
   "Withhold": return resolve_withhold(faction)` (alongside the Toil branch).
4. **Behavior base + gating** (`engine/npc/behavior.py`): add `"Withhold": 0` to `BASE_WEIGHTS`.
   In the chain-role gate (where non-chain factions get `weights.pop("Toil", None)`), also
   `weights.pop("Withhold", None)` for non-chain factions.
5. **Behavior anger weight** (`engine/npc/behavior.py`): add module constants
   `WITHHOLD_ANGER_THRESHOLD = -20` and `WITHHOLD_ANGER_WEIGHT = 40`. In Step 3 (state
   modifiers), for a chain-role faction when `mayor` is available and
   `mayor.get_reputation(faction.id) <= WITHHOLD_ANGER_THRESHOLD`: add `WITHHOLD_ANGER_WEIGHT`
   plus one extra `WITHHOLD_ANGER_WEIGHT`-step-fraction per −10 below threshold (e.g.
   `+= WITHHOLD_ANGER_WEIGHT * (1 + (THRESHOLD - rep)//10)`, tune by feel). `mayor is None` → no
   Withhold weight.
6. **Plumb `mayor`** into the behavior path: `decide_action(..., mayor=None)`; pass it from
   `run_sequential_actions` (add a `mayor=None` param) which passes to `decide_action`; pass
   `mayor` from `runner.run_cycle` into `run_sequential_actions`.
7. **Runner reset** (`engine/cycle/runner.py`): in the cycle-only reset loop (where `f.toiling =
   False`), also set `f.withholding = False`.

**Test** (`tests/test_withhold.py` new; food cases may extend `tests/test_needs_dynamics.py`)

- `resolve_withhold` sets `withholding` and returns success with no rank/health delta → *spec:
  actions §Withhold DW1*.
- A non-chain faction has no `Withhold` in its weights (popped) and never resolves it → *DW2*.
- `committed_action == "Withhold"` produces a Withhold plan and resolves to set `withholding`
  (generic committed machinery) → *DW3*.
- Base weight 0: a chain-role faction with neutral Mayor reputation (≥ threshold) never selects
  Withhold across a weighted draw / its weight stays 0 → *actions §Withhold DW4 + behavior base*.
- Chain ×0: a withholding producer yields 0 harvest; a withholding processor yields 0 capacity;
  a faction with both `withholding` and `toiling` still yields 0 → *public-needs DW (withhold)*.
- *Withhold matters*: one angry level-4 aristocracy producer that withholds drives a strictly
  lower minimum `fed` than the same faction acting normally, but the Public stays above Starving
  from full health (redundancy holds) → *public-needs DW (Withhold matters)*.
- Anger weight: `mayor.get_reputation` ≤ threshold lifts Withhold weight above 0 and a more
  hostile rep lifts it further; `mayor=None` leaves it at 0 → *faction-behavior Step 3 row*.

**Done when:** all Slice-1 `[automated]` Done-when items in `actions_spec.md §Withhold`,
`public-needs_spec.md` (withhold + Withhold-matters), and the `faction-behavior_spec.md` Step-3
row are encoded by a committed test and the full suite is green.

**Stuck if:** the anger weight needs a signal the behavior engine cannot see without plumbing
beyond `mayor` (re-open the spec); or making Withhold ×0 breaks an existing food balance/legibility
test in a way that is *not* the anticipated coupling (stop and surface, like the fish/flocks
regime-shift repairs).

---

## Final Slice — Event-forced withhold + cycle reorder  `[inspect]`

**Build**

1. **Event effect** (`engine/events/event_system.py`): in `_apply_single_event_effect`, handle
   `eff.field == "withhold"` → set `factions[tid].withholding = True` if `tid in factions`
   (`value` ignored). Narrative already comes from the generic `_apply_event_effects` line.
2. **Cycle reorder** (`engine/cycle/runner.py`): move the `process_active_events(...)` call (and
   its resolved-event removal) to **immediately before** the `compute_chain` / `apply_needs`
   block (item 5a before 5b). Leave `roll_for_random_events(...)` where it is (after needs). Keep
   the existing `process_world_chaos` ordering. Verify projects/world-chaos still run after.
3. **Storm template** (`backend/data/events.json`): add "The Great Storm" — `type: random`,
   trigger on the `port` domain, target `netmenders`, one effect `{field: "withhold", target_id:
   "netmenders", value: 0, label: ...}`, `duration: 3`, no cascade. Keep weight modest.

**Test** (`tests/test_withhold_events.py` new)

- An active `withhold` event sets `withholding` on its target each active cycle, zeroing that
  faction's chain contribution; on the cycle the event resolves (`cycles_remaining` hits 0 and it
  no longer applies) the contribution returns to normal → *events §Withhold DW1*.
- Redundancy under force-withhold: force-withholding **one** Food source leaves the Public
  Hungry-not-Starving from full health; force-withholding **two** Food sources at once drives it
  toward Starving → *events §Withhold DW2* (reuses the fishery redundancy fixture, inverted).
- **Ordering** (one test): with an active withhold storm, `fed` reflects the lost source the
  **same** cycle (effects applied before needs) AND a band-gated sentinel template is still
  evaluated against this cycle's freshly-drifted bands (rolling stays after needs) → *events
  §Withhold DW3*.

**Done when:** the three event `[automated]` Done-when items are encoded by committed tests; a
headless run (`py main.py --cycles N`) survives a storm without error; the full suite is green.

**Stuck if:** moving `process_active_events` before needs changes the outcome of an existing
event/cascade test in a way that is a real regression (not just a one-step ordering shift the
spec now sanctions) — surface it rather than rewriting the test to pass.

---

## Inspector

Run a fresh-eyes inspector (separate subagent) after the Final slice. Hard fidelity calls to
re-derive independently: (a) Withhold ×0 actually zeroes contribution in the chain math (not just
the flag set); (b) the *Withhold matters* and redundancy properties hold (one source out =
Hungry, two = Starving); (c) the cycle reorder is needs-neutral for non-withhold event effects;
(d) base weight 0 — nothing reaches for Withhold absent anger. Stamp this blueprint and write the
report to `output/inspect/`.
