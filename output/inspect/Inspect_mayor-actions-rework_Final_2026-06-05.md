# Inspect Report — Mayor Actions Rework · Final
Spec: Planning/specs/mayor_spec.md (v3)
Blueprint: Planning/blueprints/mayor-actions-rework_BP.md
Date: 2026-06-05
Run/demo command: `cd backend && py -m pytest tests/ -q` · `cd backend && py main.py --cycles 10`

Summary: **15 passed · 0 failed · 2 need human sign-off** — with **one criterion-wording flag** on Done-when #202 (code correct; spec text imprecise).

Full suite: **316 passed**. Headless `py main.py --cycles 10`: exit 0, clean.

---

## Results

### Feature: Sabotage
| Criterion | Status | Evidence |
|-----------|--------|----------|
| 1 AP + 50 gold; both deducted on success | PASS | `TestSabotage::test_cost_deducts_ap_and_gold` (AP 4→3, gold 500→450) |
| Insufficient gold/AP → refused, deducts nothing, AP refunded | PASS | `::test_insufficient_gold_refunds_ap_no_deduction` (gold 10 unchanged, AP restored to 4) |
| Rank −50% of fractional margin (3.50→3.25; integer→no change) | PASS | `::test_rank_erodes_fractional_margin` + **independent check**: rating 5.80→5.40 (level 5, no cross) |
| Health −50% of current (100→50, 50→25) | PASS | `::test_health_halved` + independent: health 30→15 |
| Single Sabotage never crosses a level nor zeroes health | PASS | `::test_single_sabotage_cannot_break_or_delevel` (3.50/40 → level 3, health 20) |
| Target reputation −10 | PASS | `::test_reputation_minus_ten` + independent (rep −10) |
| Level-1 faction is a valid target (not refused) | PASS | `::test_level_one_target_allowed` (rating 1.40, health 80→40, outcome decisive) |

### Feature: Build Project (context-aware)
| Criterion | Status | Evidence |
|-----------|--------|----------|
| No project under construction → initiate + 1 unit, 50g + 1 AP | PASS | `TestBuildProject::test_initiates_when_none_under_construction` + **independent**: empty 'harbor' → under_construction, progress 1, −50g/−1AP |
| Under construction → +1 work unit, 50g + 1 AP | PASS | `::test_adds_unit_when_under_construction` (progress 1→2) |
| 4th unit completes → active, health 100 | PASS | `::test_fourth_unit_completes` |
| Active & damaged (health<100) → +25 health, 30g + 1 AP | PASS | `::test_repairs_active_damaged` (60→85) + **independent**: status `damaged` health 40→65, −30g |
| Insufficient AP/gold → refused, deducts nothing | PASS | `::test_insufficient_funds_refunds` (no project created, nothing deducted) |

### Feature: Roster integrity
| Criterion | Status | Evidence |
|-----------|--------|----------|
| `VALID_MAYOR_ACTIONS` + dispatch map = exactly the demo roster; none of the 7 removed | **PASS (criterion-wording flag)** | `TestRosterIntegrity::test_valid_actions_is_exact_demo_set`. Actual allowlist = 7 entries {Meet, Endorse, Condemn, GrantTaxExemption, Sabotage, BuildProject, BreakADeal}, no removed actions. **See flag below — the criterion text names "Request an Audience" as an allowlist member; it is not (audiences dispatch via their own routes).** |
| Removed action name rejected (API 422 / not in map) | PASS | `::test_removed_actions_absent` + route check `mayor.py:248` (`if req.action not in VALID_MAYOR_ACTIONS → 422`) |

### Feature: Treasury runs but not surfaced
| Criterion | Status | Evidence |
|-----------|--------|----------|
| Multi-cycle headless run: treasury gold changes with no player treasury action | PASS | `TestMayorCycleIntegration::test_treasury_runs_without_player_action` (gold ≠ start after 3 cycles, no mayor action) |
| No treasury control in the demo player action surface | needs-human | `VALID_MAYOR_ACTIONS` contains no tax-set/guard-surge/public-works/borrow/invest entry; treasury endpoints exist but are out of the action roster. UI absence to be confirmed in the frontend pass. |

### Stale-reference cleanup
| Criterion | Status | Evidence |
|-----------|--------|----------|
| No normative `entrench`/Block/collapse references (only historical notes) | needs-human | `grep entrench\|Block\|collapse mayor_spec.md` → 4 hits, all explanatory/historical (v3 intro, Removed-Actions table reason, Mayor-Removal note, the Done-when item itself). No live-mechanic reference. |

---

## Criterion-wording flag (Done-when #202)

The criterion reads: *"`VALID_MAYOR_ACTIONS` and the action dispatch map contain exactly the demo roster (Meet, Endorse, Condemn, **Request an Audience**, Grant Tax Exemption, Sabotage, Build Project, Break a Deal)…"*

- **Observed:** `VALID_MAYOR_ACTIONS` has 7 entries and does **not** include any audience action. Request an Audience is dispatched through dedicated routes (`/mayor/audience/begin|reply|conclude|finalize`), not the allowlist — consistent with how the spec body and blueprint describe it.
- **Judgement:** the *substance* of the criterion passes (the allowlist is exactly the dispatchable demo subset, with none of the 7 removed actions). But the criterion **text is imprecise** — it lists "Request an Audience" as a `VALID_MAYOR_ACTIONS` member when the design (correctly) dispatches audiences elsewhere. This is a spec-wording defect, not a code defect; the committed test correctly encodes the real 7-entry set.
- **Recommendation:** architect touch to reword #202 — e.g. *"`VALID_MAYOR_ACTIONS` contains exactly the 7 dispatchable levers (… excluding Request an Audience, which is dispatched via the audience routes), and none of the 7 removed actions."* Blocks nothing.

## Deviations noted
| Step | Deviation | Impact |
|------|-----------|--------|
| 3/4 | Affordability pre-check added in `mayor_build_or_repair` so a refused build initiates no phantom project | **No spec contradiction.** Done-when #199 requires "refused and deducts nothing"; the guard satisfies it and additionally prevents an unpaid `under_construction` site (a latent wart in `mayor_build_base`'s initiate-then-fund order). Sound gameplay fix, contained to the new function. |
| 2/1 | Real field name `rating` used (not `rank`); integer-floor health halving | None — same observable behavior; verified independently. |
| 1/2 | Sabotage/BuildProject added to allowlist in Slice 1 rather than later | None — final state is correct; intermediate state not separately inspected (straight-through build). |
| Other | Cut-action test removals, dead-code cleanup (`copy`, composite-target, commission endpoint) | None — all verified by green suite. |

## Human sign-off
Review each, tick when verified:
- [ ] No treasury control appears in the demo's player action surface — evidence: `VALID_MAYOR_ACTIONS` = 7 levers, no treasury actions; UI confirmed in frontend pass
- [ ] Spec carries no normative entrench/Block/collapse reference — evidence: grep shows 4 hits, all historical notes

---

## Verdict
All 15 `[automated]` Done-when items pass via committed tests, with cap/rank/build math independently re-verified on untested values and the API 422 rejection path confirmed in the route. The affordability-guard deviation does not contradict the spec — it strengthens "refused = nothing happens." Full suite 316-green, headless clean. **One spec-wording defect** (Done-when #202 names Request an Audience as a `VALID_MAYOR_ACTIONS` member; by design it isn't) should be reconciled by an architect touch — it is a wording fix and blocks nothing. Feature verified.
