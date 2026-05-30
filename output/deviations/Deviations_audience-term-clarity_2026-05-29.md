# Deviations — Audience Term Clarity + Remove budget_allocation
Blueprint: Planning/blueprints/audience-term-clarity_BP.md
Date: 2026-05-29

| Slice | Step | Deviation | Why |
|-------|------|-----------|-----|
| 1 | 2 | `{valid_actions}` and `{domain}` placeholders became unused in the two term templates; left the `.format()` kwargs in `build()` rather than removing them | Harmless — `str.format` ignores unused kwargs; removing them was out of scope and risked touching unrelated call sites |
| 1 | 3 | Left `mayor_spec.md:71` ("Allocate Budget to Domain") and the engine `AllocateBudget` action untouched | That's the separate, *wired* Mayor toolkit action (`_allocate_budget`, drift +0.02), not the dead audience deal-term. Only the deal-term `budget_allocation` was removed; removing the action's docs would have deleted a real feature |

Net: implementation matched the blueprint. `budget_allocation` is gone as a deal term everywhere
operative; the only surviving mentions are the audience_spec v4 changelog/Done-when and the
decision log (documenting the removal), plus the unrelated `AllocateBudget` mayor action.
