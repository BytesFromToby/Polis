# Treasury Specification

**Version:** v2
**Date:** 2026-05-18

The Mayor controls a city treasury. Money is a lever — taxes generate income but create friction, expenditure on city needs keeps the city stable, and the moneylender offers a dangerous emergency option.

---

## Overview

Treasury is a single integer value: gold (or whatever the city's currency is called). It has no cap — but running out ends the game.

```python
@dataclass
class Treasury:
    gold: int = 500
    domain_tax_rates: Dict[str, float] = field(default_factory=dict)  # domain_id → rate; missing = 0.20
    debt: int = 0
    debt_rate: float = 0.05
    invested: int = 0
    invest_cycles_remaining: int = 0
    invest_return_rate: float = 0.0
    income_this_cycle: int = 0
    expenditure_this_cycle: int = 0
```

---

## Income

Income is generated each cycle at the start of Step 0.

**Per-domain tax income:**
```
domain_income = sum(faction_weight(f.floor) for f in domain_factions if f not exempt) × domain_rate × 10
total_income = sum(domain_income for all domains)
```

Each domain is taxed independently. Higher domain activity = larger tax base.

**Tax rate levels (per domain):**

| Rate | Label | Public Rep/cycle | Domain Faction Effects |
|---|---|---|---|
| 0.00 | Exempt | +1 | Grow +10 |
| 0.10 | Low | +1 | Grow +5 |
| 0.20 | Standard | 0 | none |
| 0.30 | Elevated | −1 | Grow −5 |
| 0.40 | High | −3 | Grow −10; Harm likelihood up |
| 0.50 | Punishing | −5 | Grow −20; Steal/Harm +15; chaos +1 in domain |

Default rate for any domain not explicitly set: **0.20 (Standard)**.

Public reputation effect is the sum across all domains each cycle.

Mayor adjusts a domain's tax rate as a free action (no AP cost). One domain per cycle. Rate cannot exceed the current tax collection level (see below).

---

## Tax Collection Infrastructure

Tax rates are limited by the city's tax collection infrastructure. Each active tax collection project unlocks one additional rate tier.

| Active Projects | Max Rate | Label |
|---|---|---|
| 0 | 0.00 | Exempt only — cannot collect |
| 1 (starting) | 0.10 | Low |
| 2 (starting) | 0.20 | Standard |
| 3 | 0.30 | Elevated |
| 4 | 0.40 | High |
| 5 | 0.50 | Punishing |

Tax collection projects belong to the `registry` domain and have `category: "tax_collection"`. They have no domain cap effect — their value is purely the rate tier they unlock.

If a tax collection project is destroyed, any domain currently taxed above the new maximum has its rate automatically capped down to the new maximum next cycle.

**Rivers Point starts with 2** — Tax Collector's Post and District Tax Office — giving a starting maximum rate of 0.20.

---

## Faction Tax Exemption

Mayor can exempt a specific faction from taxation for a set number of cycles.

- **Cost:** 1 action point
- **Duration:** Mayor sets 1–10 cycles at time of granting
- **Effect:** Exempt faction's weight is excluded from that domain's tax income calculation
- **Reputation:** Exempted faction gains +5 Mayor reputation per cycle of exemption
- **Limit:** No more than one exemption per domain at a time

Exemptions are tracked on Mayor:
```python
# Mayor.exemptions: Dict[str, int]  →  faction_id: cycles_remaining
```

Granting an exemption to a powerful faction in a high-rate domain is a significant income sacrifice — a deliberate political tool, not a cheap favor.

---

## Expenditure

Fixed costs are deducted each cycle automatically.

| Cost | Amount/cycle | Notes |
|---|---|---|
| City guard payroll | 20 gold | Reduced guard = chaos +1 in underworld/street each cycle; 0 = Public reputation −5/cycle |
| Infrastructure maintenance | 2 gold × (active projects) | Each project costs ongoing upkeep |

Optional costs (Mayor decides each cycle):

| Cost | Amount | Effect |
|---|---|---|
| Emergency guard surge | 50 gold | City-wide chaos −1 this cycle |
| Public works allocation | 30 gold | The Public: +5 reputation this cycle |

---

## The Moneylender

The Moneylender is a special faction (see Special Factions spec) with financial leverage over the city.

### Investing

Mayor can lock gold with the Moneylender for a fixed term.

| Term | Return | Notes |
|---|---|---|
| 3 cycles | 110% of invested | Low risk |
| 6 cycles | 125% of invested | Gold unavailable for emergencies |
| 12 cycles | 150% of invested | Major commitment |

Only one investment at a time. Investment cannot be recalled early.

### Borrowing

Mayor can borrow gold from the Moneylender at any time.

| Parameter | Value |
|---|---|
| Max borrow per cycle | 200 gold |
| Max total debt | 1000 gold |
| Base interest rate | 5% per cycle on outstanding debt |
| High-debt rate (debt > 500) | 10% per cycle |

Interest is deducted from treasury each cycle. If treasury cannot cover interest, debt increases instead.

**Leverage mechanic:**

When debt > 500 gold, the Moneylender gains leverage:
- Moneylender faction gets +10 to Steal actions against all other factions (they're calling in favors)
- Mayor's `Withhold Resources` action cannot target the Moneylender faction
- Moneylender may demand a political concession: reduce tax rate for 3 cycles or debt rate increases by 2%

When debt > 800 gold:
- Moneylender adds `angry at Mayor` relational trait (moderate)
- If debt is not reduced in 5 cycles: Moneylender backs a removal coalition attempt

---

## Bankruptcy

Treasury < 0 triggers bankruptcy consequences:

| Cycle in deficit | Effect |
|---|---|
| Cycle 1 | Guard payroll skipped; chaos +1 in all domains |
| Cycle 2 | Infrastructure maintenance skipped; all projects pause |
| Cycle 3 | Public reputation −20; Mayor removal risk triggered |

Recovery: if treasury returns to ≥ 0 before cycle 3, consequences stop. Mayor must explain the gap somehow (player narrative — no mechanical mitigation).

---

## Starting Balance

Starting gold is set in city data. Default: 500 gold.

Starting projects determine first-cycle infrastructure maintenance cost. A city with 5 docks and a city wall has a different baseline than a bare city.
