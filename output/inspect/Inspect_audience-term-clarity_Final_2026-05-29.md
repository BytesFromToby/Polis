# Inspect Report — Audience Term Clarity + Remove budget_allocation · Final
Spec: Planning/specs/audience_spec.md (v4, "Valid Deal Terms")
Blueprint: Planning/blueprints/audience-term-clarity_BP.md
Date: 2026-05-29
Run/demo command: `cd backend && py -m pytest tests/ -q`

Summary: 6 passed · 0 failed · 0 need human sign-off

## Results
| Criterion | Status | Evidence |
|-----------|--------|----------|
| `budget_allocation` appears in no spec, reference doc, or backend source file | PASS | `test_audience_terms.py::test_budget_allocation_not_a_live_term` (not in VALID_TERM_TYPES / _STRING_TERM_MAP / built prompt) + removal grep over engine/, api/, reference, llm-system_spec, mayor_spec returns empty (exit 1) |
| Prompt lists only tax_exemption + endorsement (Mayor) and explains each faction action + abstain | PASS | `test_prompt_explains_each_term` |
| `target_id` shown only for BuildProject and committed_abstain, not Grow/Protect | PASS | `test_target_id_only_where_real` (per-line isolation) |
| Parser clears `target_id` on a committed Grow/Protect, preserves it for BuildProject | PASS | `test_parser_target_guard` (Protect→"", Grow→"", BuildProject→"dock") |
| A `<deal>` with budget_allocation alongside a valid Mayor term drops only budget_allocation and seals | PASS | `test_budget_term_dropped_deal_seals` (mayor_terms length 1, tax_exemption kept) |
| A `<deal>` whose only Mayor term is budget_allocation yields no deal | PASS | `test_only_budget_term_no_deal` (not accepted; "one side committed nothing") |

Full suite: **274 passed**.

## Deviations noted
| Step | Deviation | Impact |
|------|-----------|--------|
| Slice 1 / Step 2 | `{valid_actions}`/`{domain}` placeholders now unused; `.format()` kwargs left in place | None — ignored by `str.format` |
| Slice 1 / Step 3 | Left `mayor_spec.md:71` "Allocate Budget to Domain" + engine `AllocateBudget` untouched | None — that is the separate, wired Mayor *action* (`_allocate_budget`), not the removed deal-term; not in scope |

Both deviations confirmed harmless and consistent with the spec criteria.
