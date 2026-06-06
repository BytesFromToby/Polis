# Core Formulas (Reference)

The current faction-contest math. Reference doc — definitional, no **Done when:** items.
**Verified against `backend/engine/formulas.py` (v3, units removed), 2026-05-25.**
**Updated 2026-06-03 (demo-redesign):** rank widened to 1–10, linear-ish grow curve, faction-weight table dropped, entrench removed. *Redesign build landed (2026-06-06) and inspector-verified (suite green, 98/98 automated criteria proven); this reference is now as-built. See `../proposals/demo-redesign.md` for the original proposal.*
Subsystem-specific math (treasury interest, entrench decay, health) lives with its own
spec/module, not here.

---

## Rank ceiling
`RANK_MAX = 10.0` — faction rank is clamped to 1.0–10.0. `level = int(rank)`.

## Grow increment
Per-cycle rank gain toward the next level: `1 / (n + 1)` where `n = level` (`int(rank)`).
Retired `1/(2^n+1)` — the `2^n` is unusable across 10 levels. Provisional curve; tune by feel.

| Level n | Increment/cycle | Grows to next |
|---------|-----------------|---------------|
| 1 | 0.500 | 2 |
| 2 | 0.333 | 3 |
| 3 | 0.250 | 4 |
| 4 | 0.200 | 5 |
| 5 | 0.167 | 6 |
| 9 | 0.100 | 10 |

A successful **Grow** adds the increment to `rank`; crossing an integer is the level-up beat (~54 grows to climb 1→10).

## Faction roll
`d20 + floor(rating) + modifier`, where `floor(rating)` = `level` (now 1–10). Leaderless penalty (−2) applied by the caller when relevant.
*Open "roll dial": whether to feed the raw float instead of `floor(rating)` so power scales gradually — deferred (note: it's coupled to Steal balance).*

## Contest resolution
Roll attacker vs defender; `margin = attacker_roll − defender_roll`.

| Margin | Outcome |
|--------|---------|
| ≥ 5 | decisive |
| 1–4 | partial |
| ≤ 0 | fail (defender wins ties) |

## Domain utilization
A faction contributes its **level** (`int(rank)`) to its domain's `utilization`; a domain's `cap` is a **level budget**. Replaces the retired exponential weight table (`0,2,4,8,16`). The cap-resistance ramp below is unchanged for now — full cap rework is parked.

## Domain cap (projects rework)
`CAP_HEADROOM_MULT = 1.20`. A domain's cap is **derived, not authored**:

- `base_cap = base_cap_from_fill(fill) = round(fill × CAP_HEADROOM_MULT)`, where `fill` is the
  domain's starting `Σ level`. Frozen once at game start; authored `cap` in `domains.json` is ignored.
- Each cycle the runner re-derives `cap = base_cap + Σ project_cap_contribution(p)` over the domain's
  base projects, where `project_cap_contribution` (a `category=="base"` project, by health tier):

  | Project state | Cap contribution |
  |---|---|
  | active/damaged, health 51–100 (intact) | +2 |
  | damaged, health 21–50 | +1 |
  | critical / under_construction / destroyed | 0 |

Base projects (4 work units to build) are the only lever that grows a domain's ceiling. See `../specs/projects_spec.md`.

## Domain cap resistance
From `utilization / cap`:

| Utilization % | State |
|---------------|-------|
| < 60% | open |
| 60–85% | passive |
| 85–95% | contested |
| ≥ 95% | blocked |

(`cap == 0` → blocked.)
