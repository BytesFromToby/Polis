# Balance Specification

**Version:** v1
**Date:** 2026-06-21

A single source of truth for the game's tunable dials, and the difficulty system layered over it.
Every "would I ever change this to retune difficulty or feel?" constant lives in one module as a
field on a `BalanceProfile`; difficulty is named profiles (`easy` / `normal` / `hard`) of those
dials. From `proposals/roadmap.md` (item 0) — the prerequisite for [endgame](../proposals/endgame.md).

---

## Overview

```
engine/balance.py
  ├─ BalanceProfile        one complete set of dials (a frozen dataclass)
  ├─ NORMAL                base profile = the pre-extraction constants, exactly
  ├─ EASY / HARD           NORMAL + overrides (defined; not yet consumed — see Slice 2)
  ├─ PROFILES              {"easy", "normal", "hard"}
  └─ get_profile(name)     name → profile; unknown/None → NORMAL

engine modules (formulas, needs/drift, needs/scales, mayor/actions, special/moneylender)
  └─ re-export their historical constant names FROM NORMAL
       e.g.  DRIFT_STEP = NORMAL.drift_step
     → existing imports and tests keep working; the values now live in one place.

SimRun.difficulty   selected at /sim/start, persisted, restored on resume
```

---

## What belongs in `balance.py` (the discriminator)

Include a constant iff it is a **difficulty / feel / stakes dial** — something tuned to change how
hard or how "feely" the game is. Leave **structural invariants** where they are:

| In balance.py | Stays put (structural) |
|---------------|------------------------|
| drift step, population growth/floor, food/support deltas | `RATING_MAX`, the d20 roll |
| unrest pressures + ease, City-Guard suppression | term-type maps, band thresholds |
| piety supply/parity/blame, zealot tax | action-point costs (`ACTION_COSTS`) |
| consumption parity, dry-health, production efficiency | contest margins (decisive/partial) |
| treasury income, domain cap headroom | |
| meet cooldown, sabotage cost | |
| moneylender leverage / removal thresholds + grace | |

**Slice-1 dial set (extracted):** `base_income`, `tax_office_income`, `cap_headroom_mult`,
`drift_step`, `pop_growth`, `pop_min`, `health_deltas`, `support_deltas`, `piety_per_level`,
`piety_parity`, `piety_blame`, `zealot_support_tax`, `unrest_hunger`, `unrest_impiety`,
`unrest_confidence`, `unrest_drunk`, `unrest_ease`, `guard_suppress`, `guard_heavy_threshold`,
`guard_heavy_support`, `consumption_parity`, `consumption_dry_health`, `health_output`,
`consumption_output`, `eff_min`, `eff_max`, `meet_cooldown`, `sabotage_gold`,
`leverage_threshold`, `removal_threshold`, `removal_grace_cycles`.

**Deferred candidates** (migrate when next touched, same pattern): `TOIL_MULT` (needs/chain),
event chaos→probability table (`_CHAOS_CHANCE`, events), `WITHHOLD_ANGER_THRESHOLD` (npc).

---

## Difficulty

- A run stores `difficulty` on `SimRun` (default `"normal"`), chosen at `/sim/start`, restored on
  `/sim/switch`. Mirrors `llm_profile_id`.
- `get_profile(name)` resolves case-insensitively; unknown or `None` → `NORMAL`.
- `EASY` and `HARD` are `NORMAL` plus a small set of **provisional, untuned** overrides
  (income, unrest ease, meet cooldown, removal thresholds). They demonstrate the
  base-plus-overrides mechanism.

### Slice boundary

- **Slice 1 (shipped 2026-06-21) — behavior-preserving.** `NORMAL` reproduces the old constants
  exactly and is the only profile the engine consumes; `EASY`/`HARD` and `SimRun.difficulty`
  exist and persist but do not yet change gameplay. The "prove the plumbing" step.
- **Slice 2 (shipped 2026-06-21) — difficulty bites.** `run_cycle` takes a `balance` argument
  (default `NORMAL`) threaded into the per-cycle dial consumers: treasury income
  (`process_treasury_step0`/`_calc_income`), the needs step (`apply_needs` + the `scales`
  helpers `piety_*`/`blame_factor`/`unrest_target`/`consumption_target`/`production_efficiency`),
  and the moneylender (`process_moneylender`). The API resolves `get_profile(run.difficulty)` and
  passes it at both `/sim/step` and `/sim/run/{n}`. A difficulty selector is on the new-game
  builder screen. Threaded explicitly (house style), not via a global — safe under FastAPI's
  threadpool. Existing callers/tests omit `balance` → get `NORMAL` → unchanged.
  - **Deferred (mayor-action path):** `meet_cooldown` and `sabotage_gold` are read on the
    player-action dispatch map and the separate audience route, not the per-cycle path. They
    still resolve from `NORMAL` regardless of difficulty; threading them is a follow-up and they
    are intentionally not among the `EASY`/`HARD` overrides.
  - **Still provisional:** `EASY`/`HARD` override *values* are untuned starting points; the
    TitleView quick-start defaults to `normal` (no stored default-difficulty preference yet).

---

## Data Model

`SimRun` gains:

| Column | Type | Notes |
|--------|------|-------|
| `difficulty` | String | `"easy"` \| `"normal"` \| `"hard"`; default `"normal"` |

Forward-only migration in `db/session.py::_migrate` adds the column to existing DBs
(`TEXT DEFAULT 'normal'`).

---

## API

- `POST /sim/start` request gains optional `difficulty` (None/unknown → `"normal"`, validated via
  `get_profile().name`).
- `SimStatusResponse` gains `difficulty` (default `"normal"`).
- `/sim/step` and `/sim/run/{n}` resolve `get_profile(session.difficulty)` and pass it to
  `run_cycle(..., balance=...)` so the run's difficulty drives the cycle.
- Frontend: a difficulty selector on the new-game builder modal (`BuilderView.vue`), passed via
  `sim.start(..., { difficulty })`.

---

## File Structure

```
engine/
    balance.py                 ← BalanceProfile, NORMAL/EASY/HARD, PROFILES, get_profile
    formulas.py                ← re-exports income + cap dials from NORMAL
    needs/drift.py             ← re-exports + apply_needs(balance=…) threads dials
    needs/scales.py            ← re-exports + piety/unrest/consumption/production fns take balance
    mayor/actions.py           ← re-exports meet_cooldown, sabotage_gold (NOT yet threaded)
    mayor/treasury.py          ← process_treasury_step0(balance=…) → _calc_income
    special/moneylender.py     ← process_moneylender(balance=…)
    cycle/runner.py            ← run_cycle(balance=…) threads it to the consumers above
db/
    models.py                  ← SimRun.difficulty
    session.py                 ← _migrate adds the column
api/
    schemas.py                 ← SimStartRequest.difficulty, SimStatusResponse.difficulty
    sessions.py                ← SimSession.difficulty
    routes/sim.py              ← start stores it; status/switch return it
```

---

## Done when

- `engine/balance.py` defines `BalanceProfile` with the slice-1 dial set, and `NORMAL`
  reproduces every pre-extraction constant value exactly — `tests/test_balance.py`  `[automated]`
- Each engine module re-exports its dial from `NORMAL` with no drift (the module constant equals
  the `NORMAL` field) — `tests/test_balance.py`  `[automated]`
- The full backend suite passes unchanged — behavior is identical to pre-extraction
  (`py -m pytest tests/ -q`)  `[automated]`
- `PROFILES` contains exactly `easy`/`normal`/`hard`; `get_profile` resolves case-insensitively and
  maps unknown/None to `NORMAL` — `tests/test_balance.py`  `[automated]`
- A `difficulty` passed to `/sim/start` is stored on the `SimRun`; omitting it yields `"normal"`;
  an unknown value falls back to `"normal"`; resuming via `/sim/switch` restores it —
  `tests/test_sim_difficulty.py`  `[automated]`
- `EASY`/`NORMAL`/`HARD` produce different per-cycle outcomes on the threaded path — treasury
  income, unrest easing, population growth, and the removal-coalition trigger all diverge by
  profile — `tests/test_difficulty_bite.py`  `[automated]`
- The new-game builder offers a difficulty selector and starting with it set persists that
  difficulty on the run  `[human-required]`

---

## Tests

- `tests/test_balance.py` — NORMAL-matches-history lock, module re-export agreement, registry +
  `get_profile` resolution, easy/hard override shape.
- `tests/test_sim_difficulty.py` — start persists / defaults / falls back; switch restores.
- `tests/test_difficulty_bite.py` — easy/normal/hard diverge on income, unrest easing, population
  growth, and the removal-coalition trigger.
