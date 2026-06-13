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
- Each cycle the runner re-derives `cap = base_cap + stack_cap_contribution(stack)` for the domain's
  `BaseProjectStack` (projects_spec v6). For `count ≥ 1`:

  `stack_cap_contribution = (count − 1) × 2 + top_contribution`

  where the pristine pool below the top contributes `+2` each, and the **top** contributes
  `tier(progress)` when completed, else `0` (a building top adds nothing). `count == 0 → 0`.

  | Top (completed) `progress` | `tier` |
  |---|---|
  | 51–100 (intact) | +2 |
  | 21–50 (damaged) | +1 |
  | 1–20 (critical) | 0 |

Building a base project (raising the top's `progress` by `build_step`% per action; default 25 → 4 actions)
is the only lever that grows a domain's ceiling. See `../specs/projects_spec.md`.

## Domain cap resistance
From `utilization / cap`:

| Utilization % | State |
|---------------|-------|
| < 60% | open |
| 60–85% | passive |
| 85–95% | contested |
| ≥ 95% | blocked |

(`cap == 0` → blocked.)

## Public needs (public-needs_spec, as-built 2026-06-12)
Owned by `engine/needs/` — constants live in `chain.py`/`drift.py`/`bands.py`; tests import
them. All provisional — tune by feel against `tests/test_needs_dynamics.py`.

**Word bands** (`bands.py`): fed/happy 0–20 Starving/Miserable · 21–45 Hungry/Sullen ·
46–75 Fed/Content · 76–100 Well fed/Festive. `SICKLY_THRESHOLD = 40` (health below → sickly).

**Chain** (`chain.py`, defined in `data/chains.json`): raw = `3 × level` per aristocracy
faction; processor capacity = `6 × level` (Ovenmen → bread 1.0 fed/unit; Winepressers → wine
0.15 fed + 0.6 happy/unit; leftover → porridge 0.4 fed/unit). Capacity ≥ raw → proportional
split; else full capacities + porridge. `TOIL_MULT = 1.5` on a toiling faction's contribution.
`demand = population / 1000`; `fed_target = min(100, 75 × fed_supply/demand)`;
`happy_target = clamp(30 + 75 × happy_supply/demand, 0, 100)`;
`drunk = wine_happy/demand ≥ 0.25`.

**Drift & effects** (`drift.py`): traits move ≤ `DRIFT_STEP = 10`/cycle toward target.
Health: Starving −4 · Hungry −2 · Well fed +2. Support: Starving −5 · Hungry −2 ·
Well fed +2 · Miserable −2 · Festive +2 (via `mayor.reputation["the_public"]`).
Population: ±2%/cycle (grow: Well fed ∧ health ≥ 70; shrink: Starving ∨ health < 30;
floor 1000).
