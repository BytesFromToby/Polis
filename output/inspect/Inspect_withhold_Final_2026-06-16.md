# Inspector Report — Withhold (Final) — 2026-06-16

**Verdict: PASS**

Inspector: fresh-eyes, read-only. Independently re-derived the chain math, ran the full suite
(474 passed), ran the headless sim (8 cycles, clean), and re-derived the 4 hard fidelity calls
from the code rather than trusting test names.

- **Test command:** `py -m pytest tests/ -q` → **474 passed in 1.60s**
- **Withhold tests:** `tests/test_withhold.py` (11) + `tests/test_withhold_events.py` (7) =
  **18 passed**
- **Headless:** `py main.py --cycles 8` → completed, no error, full roster prints.

---

## The 4 hard fidelity calls — re-derived independently

### (a) Chain ×0 is real — Withhold zeroes producer harvest AND processor capacity, and beats Toil — VERIFIED

Read `engine/needs/chain.py` math directly (not the asserts):

- **Producer loop** (lines 68-75): `contribution = per_level * f.level`; then
  `if f.withholding: contribution = 0.0` is checked **before** `elif f.toiling: contribution *= TOIL_MULT`.
  The `if/elif` structure makes Withhold strictly win — a faction with both flags takes the
  `withholding` branch and never reaches the Toil multiply. ✅
- **Processor loop** (lines 80-87): `cap = per_level_capacity * f.level`; then
  `if f and f.withholding: cap = 0.0` **before** `elif f and f.toiling: cap *= TOIL_MULT`.
  Same precedence. A withholding processor contributes 0 capacity → in the proportional/overflow
  split (lines 91-98) it processes nothing. ✅
- The zeroed capacity correctly removes that processor's bread/wine output but leaves raw
  unchanged (raw is summed in the producer loop), so the remainder spills to porridge — matches
  `test_withholding_processor_drops_processed_units` (raw equal, bread strictly lower). ✅

Evidence: `test_withhold_beats_toil` (both flags → raw == 0.0),
`test_withholding_producer_yields_zero_harvest`, `test_withholding_processor_drops_processed_units`.
The math, not just the asserts, confirms ×0 and Withhold-wins.

### (b) Withhold-matters + redundancy — VERIFIED

- **Withhold matters** (`TestWithholdMatters::test_withhold_deepens_trough_but_not_starving`):
  runs the **standard city** via `load_state_from_json(DATA_DIR)` (not a toy fixture — all
  factions, three Food sources). Withholds `netmenders` (a single `faction_id`-keyed Food source,
  ~30%) under committed action for cycles 10–19, control = committed **Protect**. Asserts
  `min(withheld[10:20]) < min(control[10:20])` (the strike deepens the trough) AND every cycle
  stays strictly above Starving (`band_index(...) > Starving`). The control is committed (matches
  the established `test_needs_dynamics.py` precedent: an uncommitted hungry source Toils
  voluntarily via the prosocial weight, so the control must be pinned too). Not a tautology — if
  Withhold did nothing the strict-less-than would fail.
  - *Note on wording:* spec/blueprint phrase this as "one level-4 aristocracy producer." The test
    uses netmenders instead. This is a faithful — arguably cleaner — substitution: netmenders is a
    single-faction source (true one-source isolation), whereas an aristocracy estate is one of
    several domain producers AND a flocks source, muddying "a single withheld source." The
    property proven (one source out → deeper trough, never Starving) is exactly the spec's. Nit
    only.
- **Redundancy** (`test_withhold_events.py::TestRedundancyUnderForceWithhold`):
  - `test_one_source_withheld_never_starving` — force-withhold netmenders for 30 cycles →
    every cycle stays above Starving. ✅
  - `test_all_sources_withheld_starving` — force-withhold ALL Food sources
    (`ARISTOCRACY = eumelidai/pyrrhidai/skiadai/elaiades` covering barley + flocks, plus
    netmenders for fish) → `fed[-1]` lands in Starving. ✅
  - This matches the three-source redundancy the established removal tests encode (the deviation
    log records the spec correction from the stale 2-source "two→Starving" figure to
    "one→never-Starving, all→Starving"). The withhold flag reproduces the removal property.

### (c) Cycle reorder is needs-neutral for non-withhold effects — VERIFIED

- `process_active_events` (runner.py 144-148) now runs at **item 5a, before** the needs step
  (5b, lines 152-154). `roll_for_random_events` (lines 172-174) stays **after** needs. Confirmed
  by reading runner.py top-to-bottom: 5a → 5b → projects → world chaos → roll. ✅
- **Needs-neutrality argument re-derived:** `compute_chain` reads only `f.level`, `f.withholding`,
  `f.toiling` (chain.py 68-87). It reads **none** of the fields active events mutate via
  `_apply_single_event_effect` (event_system.py 269-298): `health`, `rating`, `drift`, `chaos`.
  So moving effect application earlier cannot change the needs computation for any effect except
  the new `withhold` field — exactly the intent. ✅
- **Both halves of the ordering pinned:**
  - *Effects-before-needs* (felt same cycle): `test_withhold_felt_same_cycle` — a 1-cycle storm
    lowers `fed` that very cycle vs control at the same seed. Proves 5a precedes 5b.
  - *Rolling-after-needs* (gates see this cycle's bands): `test_gate_evaluated_against_post_needs_band`
    checks a Starving-gated template's eligibility against the post-needs `fed`. (This proves the
    gate **logic** against the post-needs value; the runner code placement of the roll after needs
    is verified by direct read of runner.py 152→172.)
- **Full prior event/cascade suite still green:** the entire 474-test suite passes unchanged,
  including the pre-existing event/cascade tests — the blast radius is clean.

### (d) Base weight 0 / anger-gated — VERIFIED

Read `engine/npc/behavior.py` Step-3 gate (lines 143-157):

- `BASE_WEIGHTS["Withhold"] = 0.0` (line 33). ✅
- **Chain-role faction, no anger:** weight stays 0 — `test_chain_faction_base_weight_zero_when_not_angry`
  asserts `w["Withhold"] == BASE_WEIGHTS["Withhold"] == 0.0` with a neutral `Mayor()` (rep 0 ≥
  threshold −20). Asserts from the actual captured weight dict (monkeypatched `weighted_choice`). ✅
- **Non-chain faction:** `weights.pop("Withhold", None)` in the `else` branch (line 157) →
  `test_non_chain_faction_has_no_withhold` asserts `"Withhold" not in w`. ✅
- **mayor=None (headless):** the anger block is gated `if mayor is not None` (line 150), so
  Withhold stays at base 0 — `test_no_mayor_means_no_withhold_weight` asserts
  `w.get("Withhold", 0.0) == 0.0`. ✅
- **Anger lifts it, scales with hostility:** `rep <= WITHHOLD_ANGER_THRESHOLD` →
  `steps = 1 + (THRESHOLD - rep)//10`; `weight += WITHHOLD_ANGER_WEIGHT * steps`.
  `test_anger_lifts_withhold_off_zero` (exactly at threshold → one step = WEIGHT) and
  `test_deeper_hostility_scales_weight` (−30 below → strictly larger) both pass. ✅

All four asserted from the actual weight dict, not from action-selection side effects.

---

## Done-when verification (each item)

### actions_spec §Withhold
- *Resolved Withhold sets `withholding`, no rank/health change* — VERIFIED.
  `resolve_withhold` (faction.py 75-84) sets only `withholding=True`, returns success, touches
  nothing else. `TestResolver::test_sets_flag_no_rank_or_health_change` (rating + health
  unchanged).
- *Factions with no chain role never select/resolve Withhold* — VERIFIED.
  Non-chain → `weights.pop("Withhold")` (behavior.py 157); `test_non_chain_faction_has_no_withhold`.
- *`committed_action == "Withhold"` forces selection* — VERIFIED.
  `_committed_plan` (behavior.py 252-278) returns a no-target plan for Withhold via the generic
  Protect/Grow tail; `test_committed_withhold_forces_plan_and_resolves` (plan.action == "Withhold",
  target None, resolves to set flag).
- *Base weight 0 — absent anger a chain-role faction never selects it* — VERIFIED (hard call d).

### public-needs_spec (withhold chain note + Withhold-matters)
- *Withholding producer → 0 harvest, processor → 0 capacity, this cycle only; both flags → 0
  (Withhold wins)* — VERIFIED (hard call a). Cycle-only proven by the runner reset (below) +
  `test_recovers_after_storm_passes`.
- *Withhold matters + redundancy holds (one source ≠ Starving from full health)* — VERIFIED
  (hard call b).

### faction-behavior_spec (Step-3 anger row + base-weight-0)
- *Chain-role + low Mayor standing → Withhold += WEIGHT, scaling per −10; mayor absent → 0* —
  VERIFIED (hard call d). Constants `WITHHOLD_ANGER_THRESHOLD=-20`, `WITHHOLD_ANGER_WEIGHT=40.0`
  imported by tests, never copied.

### events_spec §Withhold
- *Active `withhold` event sets `withholding` each active cycle; returns to normal the cycle it
  resolves* — VERIFIED. `_apply_single_event_effect` `eff.field == "withhold"` →
  `faction.withholding = True` (event_system.py 283-287). `test_active_event_sets_withholding_each_cycle`,
  `test_resolves_after_duration`, `test_recovers_after_storm_passes` (flag False after resolve).
- *One Food source force-withheld → never Starving; all → Starving* — VERIFIED (hard call b,
  `TestRedundancyUnderForceWithhold`).
- *Effects ordered before needs while rolling stays after (one ordering test)* — VERIFIED
  (hard call c).

### cycle-runner_spec (item 5a/5b reorder + cycle-only state)
- *`process_active_events` at 5a before needs; rolling after* — VERIFIED by direct read
  (runner.py 144-174).
- *`withholding` is cycle-only, reset each cycle* — VERIFIED. runner.py 197-200 sets
  `f.withholding = False` for every faction at end of cycle (alongside `f.toiling`), AFTER the
  needs step consumed it. `withholding` is a plain dataclass field (models.py 75), absent from any
  serializer / db persistence (grep of engine/db/api found no serialization of it). Matches
  `toiling` exactly.

### data/events.json — great_storm template — VERIFIED
`great_storm`: type random, `trigger_conditions {domain: port, min_chaos: 3}`, weight 2, target
`netmenders`, one effect `{field: withhold, target_id: netmenders, value: 0, duration: 3}`, no
cascade. Matches the blueprint and events_spec example.

---

## Test fidelity

- **Constants imported, not hard-coded:** `test_withhold.py` reads `behavior.BASE_WEIGHTS`,
  `behavior.WITHHOLD_ANGER_THRESHOLD`, `behavior.WITHHOLD_ANGER_WEIGHT`; `chain.py` constants via
  the chain module; bands via `engine.needs.bands`. No baked literals for the tuned values. ✅
- **No tautologies found:** the weight tests capture the real weight dict via a monkeypatched
  `weighted_choice` and assert exact values; the chain tests compare against a live baseline; the
  matters/redundancy tests use strict inequalities that would fail if the feature were inert.
- **No Done-when left unbacked:** every `[automated]` Withhold item across the five specs maps to
  at least one passing test (table above).

## Nits (non-blocking)

1. **Spec/blueprint wording vs test fixture (matters test):** spec and blueprint say "one
   level-4 aristocracy producer that withholds"; the test uses `netmenders` instead. The property
   proven is identical and the substitution is arguably cleaner (true single-source isolation).
   Purely a wording mismatch — no behavior gap. Worth a one-line spec tweak someday, not a blocker.
2. **Ordering test (rolls-see-post-needs-band) is semi-direct:** `test_gate_evaluated_against_post_needs_band`
   proves the gate *function* honors the post-needs `fed`, and `test_withhold_felt_same_cycle`
   proves effects precede needs; the literal placement of the roll *after* needs in the cycle is
   confirmed by code read (runner.py), not by an in-cycle assertion that a freshly-eligible
   template actually got rolled this cycle. Adequate (the band-gate sentinel suite already pins
   roll-after-needs for the pre-existing public-needs work), but a single end-to-end ordering test
   would be marginally stronger. Not a blocker.
3. **`compute_chain` docstring** says "reads faction levels and toiling flags" — it now also reads
   `withholding`. Cosmetic doc drift in chain.py line 55.

---

**Conclusion: PASS.** All `[automated]` Done-when items across actions, public-needs,
faction-behavior, events, and cycle-runner specs are encoded by passing tests; the four hard
fidelity calls re-derive cleanly from the code; the full suite is 474 green; the headless sim
survives. Withhold is the genuine ×0 twin of Toil — it wins over Toil in the chain math, is
structurally rare (base 0, anger-only), force-withholds via events under the reordered cycle,
preserves source redundancy, and resets cleanly as cycle-only state.

— Inspector, 2026-06-16
