# Treasury Specification

**Version:** v3
**Date:** 2026-06-07

The Mayor controls a city treasury. Gold is a lever: a small flat income keeps the lights on,
**Tax Offices** are the buildable way to grow income, and running short cannibalises the city's
own infrastructure. v3 is the demo-scoped treasury — simple, self-balancing, and meaningful
within a short game.

> **v3 changes (demo redesign):** income is now a flat base **+20/cycle** plus **+20 per
> completed Tax Office**; the old per-domain auto-tax (which silently taxed every domain at the
> default 0.20 and ballooned the treasury) is **removed**. Tax Offices are a base-project stack
> in a new faction-less city-wide domain `civic` ("Public Treasury"). Insolvency no longer runs
> a bankruptcy ladder — instead gold is clamped at 0 and the shortfall damages random non-civic
> projects (self-balancing, since fewer projects means lower upkeep). The **Moneylender**
> (invest/borrow/leverage), **emergency guard surge**, **public works allocation**, the
> **per-domain tax-rate tier table**, and **tax_collection-unlocks-tiers** are all **deferred to
> future** (see Deferred section). Their prior full design lives in git history (v2).

---

## Overview

Treasury is a single integer `gold` (default 500, from city data). It has no cap. Each cycle at
Step 0 (`process_treasury_step0` in `engine/mayor/treasury.py`) income is added and fixed
expenditure deducted; if expenditure cannot be covered, gold is clamped at 0 and the shortfall
is paid in infrastructure damage.

```python
@dataclass
class Treasury:
    gold: int = 500
    income_this_cycle: int = 0
    expenditure_this_cycle: int = 0
    # domain_tax_rates / debt / invested fields remain on the model but are DORMANT in the
    # demo (no action sets them); see Deferred.
```

---

## Feature: Income — base + Tax Offices

Income is computed each cycle in `process_treasury_step0`, replacing the per-domain auto-tax in
`_calc_tax_income`. The treasury step is given the `base_stacks` so it can count completed Tax
Offices.

- Input: `base_stacks` (the per-domain `BaseProjectStack` map), `Treasury`.
- Output: `income = BASE_INCOME + TAX_OFFICE_INCOME × (completed Tax Office instances)`, added to
  `gold` and `income_this_cycle`, logged as a `TaxIncome` result.

Constants (in `engine/formulas.py`): `BASE_INCOME = 20`, `TAX_OFFICE_INCOME = 20`.

"Completed Tax Office instances" = `active_count()` of the `civic` domain's base stack (a
building, not-yet-completed top contributes 0, matching `BaseProjectStack.active_count`).

**Done when:**
- With no Tax Offices built, one `process_treasury_step0` adds exactly `+20` income for the cycle, regardless of how many factions/domains exist  `[automated]`
- With N completed Tax Offices in the `civic` stack, income for the cycle equals `20 + 20 × N`  `[automated]`
- A `civic` stack whose top is still building (not completed) contributes 0 to income — income is `20 + 20 × (active_count)`, not counting the building top  `[automated]`
- A domain full of factions at the default tax rate contributes 0 income — total income depends only on base + Tax Offices (the per-domain auto-tax is gone)  `[automated]`

---

## Feature: Tax Office lever — the `civic` domain

A new faction-less city-wide domain `civic` (display name "Public Treasury") holds a repeatable
**"Tax Office"** base-project stack (the projects_spec v6 stack model). It is built with the
existing Build Project mayor action (`mayor_build_base`), at the same cost as any other base
project (50 gold + 1 AP per build step; ~4 steps to complete). There is **no hard cap** on Tax
Office count — they are paced by the gold/AP economy.

- Input: `data/domains.json` gains a `civic` domain (no faction references it); `BASE_PROJECT_NAMES`
  gains `"civic": "Tax Office"`.
- Output: a buildable Tax Office stack in `civic`; each completed instance feeds Income above.

Rules:
- **Faction-less domains keep their authored cap.** `_freeze_base_caps` must skip a domain with
  no factions (leave its authored `cap`/`base_cap` intact) instead of deriving cap 0 from zero
  fill. `civic` is authored with a nominal cap (e.g. 12) purely so its readout is sane.
- **Tax Offices do not contribute to domain cap.** The `civic` domain's live cap stays at its
  authored value as Tax Offices are built (Tax Offices are infrastructure, not influence — they
  add no `stack_cap_contribution`). No influence domain's cap is affected by Tax Offices.

**Done when:**
- `base_project_name("civic")` returns `"Tax Office"`  `[automated]`
- After loading `data`, the `civic` domain exists with its authored cap (not overwritten to 0 by the freeze) and utilization 0  `[automated]`
- Building a Tax Office via `mayor_build_base("civic", ...)` succeeds at the standard base-project cost (50 gold + 1 AP to break ground) and grows the `civic` stack  `[automated]`
- The `civic` domain's cap is unchanged by building Tax Offices, and no influence domain's cap changes when a Tax Office is built  `[automated]`
- Tax Offices appear under a "Public Treasury" group in the projects panel, and `civic` does not appear as a faction group in the faction panel  `[human-required]`

---

## Feature: Expenditure (unchanged)

Fixed costs deducted each cycle:

| Cost | Amount/cycle |
|---|---|
| City guard payroll | 20 gold |
| Infrastructure maintenance | 2 gold × (active base-project instances) |

`active project count` = `sum(s.active_count() for s in base_stacks.values())` (as today; civic
Tax Offices are included — each nets +18/cycle). Guard payroll and maintenance behave as in v2.

**Done when:**
- Guard payroll deducts 20/cycle and maintenance deducts `2 × active_count` when gold covers them  `[automated]`

---

## Feature: Insolvency — clamp + infrastructure damage

Replaces the v2 bankruptcy ladder. When the cycle's expenditure cannot be fully covered by gold:

- `gold` is **clamped at 0** (never goes negative).
- The uncovered **shortfall** is converted to damage applied to **random non-civic base-project
  instances** (Tax Offices are never targeted). Conversion is ~1:1 gold→health points, where one
  full instance = 100 health: damage reduces a stack top's `progress` (health), and enough damage
  destroys the top (`count` drops, `active_count` falls). This lowers next cycle's maintenance —
  self-balancing.

- Input: the deficit (expenditure − available gold), `base_stacks`.
- Output: gold clamped to 0; one or more non-civic stacks damaged/reduced; a logged result.

**Done when:**
- When expenditure exceeds available gold, `gold` ends the cycle at exactly 0 (never negative)  `[automated]`
- An insolvency shortfall reduces total health/`active_count` across non-civic base stacks, and a `civic` Tax Office stack is never damaged by insolvency  `[automated]`
- A shortfall large enough to exceed an instance's remaining health destroys an instance, so the next cycle's `active_count` (and thus maintenance) is lower  `[automated]`
- No v2 bankruptcy-ladder effect (guard skip / projects-pause / −20 public rep removal trigger) fires on a deficit  `[automated]`

---

## Deferred to future (not in the demo)

The following v2 mechanics are intentionally out of scope. Engine fields/blocks for some remain
but are **dormant** (no action sets them); no demo UI exposes them. Full v2 design is in git
history.

- **Moneylender** — investing (3/6/12-cycle terms) and borrowing (debt, interest, >500/>800
  leverage). `Treasury.debt`/`invested` stay 0; the invest/debt code paths never trigger.
- **Per-domain tax-rate tiers** — the 6-tier rate table with per-cycle public-rep / Grow / chaos
  effects, and **tax_collection projects unlocking rate tiers**. `apply_tax_effects` is a no-op
  for the demo (all domains effectively rate 0; income is base + Tax Offices only).
- **Emergency guard surge** (50 gold → chaos −1) and **public works allocation** (30 gold →
  Public +5).
- **Bankruptcy ladder** (the 3-cycle deficit consequence table) — replaced by Insolvency above.
- **Faction tax exemption** — had no income effect under v3 (income = base + Tax Offices, not
  faction-weighted), so it is shelved: no UI action, not offered in audiences. The engine
  exemption machinery (`mayor.exemptions`, domain jealousy) remains dormant. See
  `tax-exemption-shelve_spec.md`.

**Done when:**
- The demo exposes no invest, borrow, guard-surge, or public-works action, and adjusting a domain tax rate has no income or reputation effect  `[human-required]`

---

## Starting Balance

Starting gold from city data (default 500). With base income 20/cycle and guard payroll 20/cycle,
a city with no Tax Offices roughly breaks even before maintenance — so building the first Tax
Office is the first real economic decision.
