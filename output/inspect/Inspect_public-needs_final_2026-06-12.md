# Inspection Report — Public Needs (The Barley Run) — FINAL SIGN-OFF
**Date:** 2026-06-12
**Inspector:** final-sign-off pass (fresh eyes; independent of builder)
**Spec:** `Planning/specs/public-needs_spec.md` (+ 2026-06-12 additions in actions, faction-behavior, cycle-runner, events, audience, special-factions specs)
**Blueprint:** `Planning/blueprints/public-needs_BP.md`
**Verdict: PASS** — every automated Done-when criterion is proven by a committed test or (one case) direct drive; the human-required UI criterion has captured screenshot evidence. One fidelity gap and one spec-letter deviation flagged below; neither blocks sign-off.

## Test baseline
`cd H:\Polis\backend; py -m pytest tests/ -q` → **436 passed in 1.53s** (matches expected count; zero failures, zero skips).

## Headless run
`py main.py --cycles 30 --seed 3` → completes; summary line present and sane:
`THE PUBLIC: pop=20,000 fed=54 (Fed) happy=80 (Festive) health=96`
(starts 20000/60/50/100 — population stable, fed held in the Fed band, no collapse.)

---

## Per-criterion results

### public-needs_spec — Feature: Public needs state
| # | Criterion | Verdict | Proof |
|---|---|---|---|
| 1 | Round-trip population/fed/happy; absent fields default 20000/60/50 | PASS | `test_needs_bands.py::TestSerialization` (round_trip, missing_fields_default) + `test_needs_cycle.py::TestSnapshotRoundTrip` (full serialize_state path, incl. no-public → None) |
| 2 | Band lookup exact at boundaries (20/21, 45/46, 75/76; both tables) | PASS | `test_needs_bands.py::TestFedBands/TestHappyBands::test_boundaries` — encodes every spec boundary literally |
| 3 | `drunk` exactly at wine-happy/demand ≥ DRUNK_THRESHOLD; `sickly` exactly at health < 40 | PASS (drunk: by direct drive — **no committed test**, see Fidelity) | sickly: `TestSickly` (39→True, 40→False). drunk: inspector drive — comparator `>=` at `engine/needs/chain.py:107`; flips correctly across the 0.25 crossing (pop 7199 → True, 7201 → False); exact equality is float-unrepresentable in this construction (3.0×0.6 = 1.7999…8) |

### public-needs_spec — Feature: The harvest chain
| # | Criterion | Verdict | Proof (`test_needs_chain.py`) |
|---|---|---|---|
| 1 | Pure function; twice on same state → identical | PASS | `TestPurity` — equal outputs + rating/health/toiling snapshot unchanged |
| 2 | Raw = Σ 3×level; dead estates → zero everything | PASS | `TestProduction` — raw 3×(4+3+2); dead-estates by removing aristocracy factions (faithful: rating floor 1.0 makes zero-level unreachable otherwise) |
| 3 | Over-capacity → full caps + porridge remainder; under → proportional, no leftover | PASS | `TestSplit::test_under/test_over` — exact unit counts (4.5/4.5/0 and 12/12/3) |
| 4 | Conservation: bread+wine+porridge = raw, exactly | PASS | `TestSplit::test_conservation` — three rating sets, 1e-9 tolerance |
| 5 | Porridge floor: no processors → 0.4×raw, nonzero when raw nonzero | PASS | `TestPorridgeFloor` — processors removed; fed_target computed from imported constants, asserted > 0 |
| 6 | Toiling producer ×1.5 harvest, processor ×1.5 capacity, this cycle only | PASS | `TestToil` (both multipliers, from imported `TOIL_MULT`); "this cycle only" closed by `test_needs_cycle.py::TestToilingReset` |

### public-needs_spec — Feature: Drift, shortage, and plenty
| # | Criterion | Verdict | Proof (`test_needs_drift.py`) |
|---|---|---|---|
| 1 | 30 below target → +DRIFT_STEP exactly; ≤ step away → lands exactly | PASS | `TestDrift` (also covers downward drift) |
| 2 | Health and support deltas match band tables | PASS | `TestHealthDriver` (Starving/Hungry/Well fed/Fed-neutral, cap at 100) + `TestSupportDeltas` (Starving+Miserable via mayor reputation; Well fed+Festive mayorless) — deltas read from the imported constant tables, which match spec values |
| 3 | Pop +2% Well fed & health≥70; −2% Starving or health<30; floor 1000; demand scales | PASS | `TestPopulation` — all five cases incl. 20k→40k halving fed_target |
| 4 | Drunk-city fixture: swapped 4.0/1.0 → happy above, fed below baseline within 10 cycles | PASS | `TestDrunkCity` — real factions.json, exact spec fixture |

### public-needs_spec — Feature: Cycle integration
| # | Criterion | Verdict | Proof |
|---|---|---|---|
| 1 | Needs step after action loop, before new-event rolling; same-cycle starvation unlock | PASS | `test_needs_event_gates.py::TestSameCycleGating` (fed 22→starved→sentinel fires same cycle); ordering also code-verified in `engine/cycle/runner.py` (tick_deals → item 5b → active events → roll) |
| 2 | Sentinel events eligible exactly when fed band matches gate | PASS | `TestFedGates::test_one_sentinel_per_band` + boundary tests (via `_matches_trigger`; the in-roll path is covered by the same-cycle test) |
| 3 | `Faction.toiling` always false after `run_cycle` | PASS | `test_needs_cycle.py::TestToilingReset` (committed-Toil cycle; all flags False; boost strictly visible vs control — the slice-5 vacuity fix is in place: fed=50 fixture, strict `>`) |
| 4 | Stability: 60 cycles untouched → Hungry-or-better ≥ 50/60 | PASS | `test_needs_dynamics.py::TestStability` (seed 101) |
| 5 | Legibility ≤ 5 cycles; recoverability ≤ 15 | PASS | `TestLegibilityAndRecovery` — one trajectory, two assertions (recorded deviation; same scenario, two phases) |
| 6 | Toil matters: committed estate Toil vs committed Protect → strictly higher min fed | PASS | `TestToilMatters` — encodes the corrected spec text exactly (producer Toil, committed control) |
| 7 | Audience system prompt contains needs line with current band words | PASS | `test_audience_terms.py::test_prompt_contains_needs_line` (+ `test_prompt_without_public_has_no_needs_line`) |
| 8 | **[human-required]** UI across a shortage reads clearly | **PASS** | Screenshots below — band words visible, color-coded, shifts unmistakable |

### actions_spec — Toil (added 2026-06-12)
| # | Criterion | Verdict | Proof (`test_toil.py`) |
|---|---|---|---|
| 1 | Resolved Toil sets `toiling`, no rank or health change | PASS | `TestResolver` |
| 2 | No-chain-role factions never select or resolve Toil | PASS | `TestWeights::test_non_chain_faction_has_no_toil` — Toil absent from the built weight dict (selection path); see Fidelity note on the resolve side |
| 3 | `committed_action == "Toil"` forces Toil selection | PASS | `TestCommitted` |

### events_spec — Public-need gates (added 2026-06-12)
| # | Criterion | Verdict | Proof (`test_needs_event_gates.py`) |
|---|---|---|---|
| 1 | `max_fed_band: "Starving"` never above Starving; eligible same cycle band reaches it | PASS | `TestFedGates::test_max_fed_band_boundary` + `TestSameCycleGating` |
| 2 | Each gate key honored independently via sentinels | PASS | `TestFedGates` / `TestHappyGates` / `TestSicklyGate` / `TestNoPublic` (no-public → gated ineligible, ungated unaffected) |

### audience_spec — Toil/needs-line items (added 2026-06-12)
| # | Criterion | Verdict | Proof (`test_audience_terms.py`) |
|---|---|---|---|
| 1 | Toil in term list for chain-role factions; absent entirely for non-chain | PASS | `test_toil_offered_only_to_chain_role_factions` (ovenmen yes, tidesworn no — asserts "Toil" nowhere in the prompt) |
| 2 | Needs line with current band words; drunk/sickly only when set | PASS | `test_prompt_contains_needs_line` (prompt level) + `test_needs_bands.py::TestNeedsLine` (flag conditionality, both states) |
| 3 | `<deal>` schema shows target_id only for BuildProject/abstain — not Toil | PASS | `test_toil_schema_line_untargeted` + `test_target_id_only_where_real` |
| 4 | Parser clears target_id on Toil (and Grow/Protect), preserves for BuildProject | PASS | `test_parser_clears_toil_target` + `test_parser_target_guard` |

### special-factions_spec — structure rows (read-verified, no new Done-when)
PASS — `engine/models.py::ThePublic` carries `population: int = 20000`, `fed: int = 60`, `happy: int = 50` per spec; support-table rows (Starving −5, Hungry −2, Well fed +2, Miserable −2, Festive +2) implemented as `SUPPORT_DELTAS` in `engine/needs/drift.py`, value-for-value; `data/world_state.json` block matches the spec example.

### faction-behavior_spec — weight rows (read-verified, no new Done-when)
PASS — `engine/npc/behavior.py`: `BASE_WEIGHTS["Toil"] = 10.0`; `industrious` trait row includes `Toil: 10`; state modifier "fed band ≤ Hungry AND chain role → Toil +25" at lines 136–140; non-chain factions get Toil popped from the weight dict. All three rows also pinned by `test_toil.py::TestWeights`.

### cycle-runner_spec — item 5b + cycle-only state row (read-verified)
PASS — `engine/cycle/runner.py`: needs step sits after `tick_deals` (end of state updates) and before `process_active_events` / `roll_for_random_events`, with a spec-citing comment; `toiling` reset for all factions at the very end of `run_cycle` (cycle-only state row honored; placement deviation from `end_of_cycle.py` recorded and correct — end_of_cycle runs *before* the needs step).

---

## Human-required evidence
Captured via playwright against the live server (`py -m uvicorn api.server:app`), throwaway registered users, real UI clicks on **Run Cycle**. The shortage was engineered with the spec's own dead-estates scenario (the three aristocracy estates deleted in city setup).

Saved to `H:\Polis\docs\InPlayScreenshots\`:
- `public-needs_2026-06-12_01_healthy.png` (+ `_people.png` crop) — Population 20,000 · Fed: **Fed** · Mood: **Content (drunk)** · Health 100. The drunk flag renders; Toil narratives ("…bend to their trade") appear in the event log.
- `public-needs_2026-06-12_02_shortage_cycle0.png` — shortage city at cycle 0: Fed band, baseline.
- `public-needs_2026-06-12_03_shortage_hungry.png` — 3 cycles in: Fed→**Hungry**, Mood→**Sullen**, support −4.
- `public-needs_2026-06-12_04_shortage_starving.png` — 7 cycles in: **Starving** (rendered in warning color), population 20,000→**18,448**, public standing −21, disposition restless.
Band words are visible, color-coded, and the shift across the shortage is unmistakable. **Criterion met.**
Drive script: `output/inspect/drive_public_needs.py`. Server stopped via `Stop-Process` after capture.

## Fidelity judgments and concerns
1. **Drunk threshold has no committed test** (the only unproven-by-suite criterion). `test_needs_chain.py` never asserts `ChainOutput.drunk`; `test_needs_drift.py` only passes it through. I proved the comparator by direct drive (flips at the 0.25 crossing; `>=` per spec). **Recommend** a small committed test in `test_needs_chain.py` asserting drunk on both sides of the threshold (exact equality is float-unrepresentable with the wine profile 0.6 — a both-sides test is the honest encoding).
2. `drunk` **is persisted** (`serializer.py` round-trips it) while the spec says "Drunk is not stored." Behaviorally harmless — `apply_needs` overwrites it every cycle and it never drifts — and the deviation is recorded (BP Final/1), but the spec sentence is now false in letter. Recommend a one-line spec amendment ("cached for display and serialized; never drifted").
3. Support-delta coverage is by pairs (Starving+Miserable, Well fed+Festive); the Hungry support row (−2) and the neutral Fed/Sullen/Content rows are not individually asserted — they hold via the imported `SUPPORT_DELTAS` table matching the spec, which I read-verified. Low risk.
4. actions_spec item 2 says "never select **or resolve**": only selection is test-guarded (weight absent). Nothing in the engine prevents a direct `resolve_toil` call on a non-chain faction, but no live path reaches it (NPC selection is gated; audiences offer Toil only to chain-role factions — tested). Acceptable.
5. Sentinel gate tests exercise `_matches_trigger` directly rather than the full roll; the same-cycle test covers the in-roll path once. Acceptable layering.
6. Audience needs-line test builds the prompt directly rather than "after a cycle" — presence and band-word correctness are what the criterion assigns to this spec; assembly freshness is covered by the cycle-runner ordering tests. Acceptable.

## Deviations review (`output/deviations/Deviations_public-needs_2026-06-12.md`)
All 17 rows reviewed. Sixteen are clean how-not-what (test placement, aliases, signature shapes, reset placement, IO-free engine choices, monkeypatch strategy). Two are borderline-but-acceptable:
- **6/2 (deck effects conformed to faction-health only):** the shipped bread_riot/plague_outbreak effects differ from the events_spec prose example (Public support/chaos effects), because `_apply_single_event_effect` cannot touch The Public. No events_spec Done-when binds effect payloads — both gating criteria pass — and the follow-up is recorded. Acceptable, but the events-system follow-up should land before the deck is treated as content-complete.
- **F/1 (drunk stored):** see Fidelity #2 — recorded, honest, slightly contradicts spec letter; spec amendment recommended.
The two spec corrections in F/3 (Toil-matters: estate Toil + committed control) were written **into the spec itself** with the build findings dated and reasoned — that is spec evolution done properly, not a silent deviation.

## Verdict
**FINAL SIGN-OFF: PASS.** 25 automated criteria pass via committed tests; 1 (drunk threshold) passes via direct drive and needs a committed test as follow-up; the human-required UI criterion passes with screenshot evidence; all read-only verification items (structure rows, weight rows, orchestration order) match their specs.

— Inspector, 2026-06-12
