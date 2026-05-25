# Engine Module Map

**Version:** v2
**Date:** 2026-04-03

Detailed reference for all engine modules in `city_sim_Project/scr/engine/`.

---

## `models.py`

Owns all dataclasses. No logic, no calculations. Imports only from stdlib.

### Sub-objects

#### `DomainRating`
A unit's rating in a single domain.

| Field | Type | Notes |
|-------|------|-------|
| `domain_id` | `str` | Domain name |
| `rating` | `float` | Current rating (may be fractional) |
| `entrench` | `float` | Entrenchment level (0.0–3.0) |
| `floor` | `int` | Last confirmed level (`int(rating)`) |

---

#### `FactionSlot`
A unit's membership record for one faction.

| Field | Type | Notes |
|-------|------|-------|
| `faction_id` | `str` | Faction identifier |
| `role` | `str` | `"member"` or `"leader"` |
| `inertia` | `float` | Membership inertia (0.0–2.0) |

---

#### `FocusSlot`
A unit's current focus target.

| Field | Type | Notes |
|-------|------|-------|
| `target_id` | `str` | Unit or faction ID |
| `score` | `float` | Focus intensity |
| `slot` | `int` | 1 = primary, 2 = secondary |

---

#### `FactionRelationship`

| Field | Type | Notes |
|-------|------|-------|
| `other_faction_id` | `str` | |
| `relationship` | `str` | `"Friend"`, `"Foe"`, `"Hide"`, `"Client"`, `"Neutral"` |

---

#### `DomainRelationship`

| Field | Type | Notes |
|-------|------|-------|
| `domain` | `str` | Domain name |
| `relationship` | `str` | `"Friend"`, `"Foe"`, `"Hide"`, `"Client"`, `"Neutral"` |

---

### Core Entities

#### `Unit`

| Field | Type | Persistent | Notes |
|-------|------|-----------|-------|
| `id` | `str` | Yes | |
| `name` | `str` | Yes | |
| `traits` | `List[str]` | Yes | |
| `domain_ratings` | `List[DomainRating]` | Yes | |
| `factions` | `List[FactionSlot]` | Yes | |
| `focus_1` | `FocusSlot \| None` | Yes | |
| `focus_2` | `FocusSlot \| None` | Yes | |
| `health` | `float` | Yes | 0–100 |
| `edge` | `int` | Yes | Offensive stat |
| `grit` | `int` | Yes | Defensive stat |
| `anonymous` | `bool` | Yes | |
| `retired` | `bool` | Yes | |
| `cycle_protect_level` | `int` | No | Cycle-only. Reset each cycle. |

---

#### `Faction`

| Field | Type | Persistent | Notes |
|-------|------|-----------|-------|
| `id` | `str` | Yes | |
| `name` | `str` | Yes | |
| `traits` | `List[str]` | Yes | |
| `domain_primary` | `str` | Yes | |
| `rating` | `float` | Yes | |
| `floor` | `int` | Yes | `int(rating)`, tracked separately |
| `entrench` | `float` | Yes | 0–100. Renamed from `health`. |
| `leadership_need` | `float` | Yes | |
| `leader_id` | `str \| None` | Yes | |
| `member_ids` | `List[str]` | Yes | |
| `level_1_count` | `int` | Yes | Background member count |
| `relationships` | `List[FactionRelationship]` | Yes | |
| `capacity` | derived | Never | `get_faction_capacity(floor)` |

---

#### `Domain`

| Field | Type | Persistent | Notes |
|-------|------|-----------|-------|
| `id` | `str` | Yes | |
| `name` | `str` | Yes | |
| `cap` | `int` | Yes | |
| `utilization` | `float` | Yes | Recalculated each cycle |
| `drift` | `float` | Yes | |
| `relationships` | `List[DomainRelationship]` | Yes | |

---

#### `WorldState`

| Field | Type | Persistent | Notes |
|-------|------|-----------|-------|
| `cycle` | `int` | Yes | |
| `sm_attention` | `float` | Yes | |
| `chaos` | `Dict[str, float]` | Yes | Per-domain |
| `power_vacuums` | `List[str]` | Yes | Domain names |
| `sm_state` | `str` | Yes | `"baseline"`, `"elevated"`, `"crisis"` |

---

### Plan and Result Types (cycle-local, never persisted)

#### `NPCPlan`
| Field | Type |
|-------|------|
| `unit_id` | `str` |
| `action` | `str` |
| `target_id` | `str \| None` |
| `domain` | `str \| None` |
| `level` | `int` |
| `source` | `str` |

#### `FactionPlan`
| Field | Type |
|-------|------|
| `faction_id` | `str` |
| `action` | `str` |
| `target_id` | `str \| None` |
| `domain` | `str \| None` |
| `level` | `int` |

#### `ActionResult`
| Field | Type |
|-------|------|
| `actor_id` | `str` |
| `action` | `str` |
| `target_id` | `str \| None` |
| `domain` | `str \| None` |
| `outcome` | `str` |
| `narrative` | `str` |
| `dramatic` | `bool` |
| `stat_changes` | `dict` |

#### `CycleEvent`
| Field | Type |
|-------|------|
| `cycle` | `int` |
| `step` | `int` |
| `actor_id` | `str` |
| `action` | `str` |
| `target_id` | `str \| None` |
| `outcome` | `str` |
| `narrative` | `str` |
| `dramatic` | `bool` |

#### `CycleResult`
| Field | Type |
|-------|------|
| `cycle` | `int` |
| `events` | `List[CycleEvent]` |
| `unit_actions` | `int` |
| `faction_actions` | `int` |
| `retirements` | `List[str]` |
| `new_units` | `List[str]` |

---

## `actions/unit.py`

Unit action resolvers. One function per action. Returns `ActionResult`.

| Function | Action |
|----------|--------|
| `resolve_grow_unit()` | Grow |
| `resolve_protect()` | Protect (formerly Entrench) |
| `resolve_care()` | Care (formerly Rejuvenate) |
| `resolve_harm()` | Harm (formerly Attack) |
| `resolve_block()` | Block |
| `resolve_passive_spy()` | Steal / passive spy |
| `resolve_targeted_spy()` | Expose / targeted spy |
| `resolve_obscure()` | Obscure |

---

## `actions/faction.py`

| Function | Action |
|----------|--------|
| `resolve_grow_faction()` | Faction Grow |
| `resolve_support_faction()` | Support Faction |
| `resolve_defend()` | Defend |
| `resolve_block_citywide()` | Block (city-wide) |
| `resolve_block_specific()` | Block (specific) |

---

## `actions/membership.py`

| Function | Action |
|----------|--------|
| `resolve_seek_leadership()` | Seek Leadership |
| `resolve_join()` | Join |
| `resolve_leave()` | Leave |
| `resolve_kick()` | Kick (auto, cycle runner only) |
| `resolve_recruit()` | Recruit (auto, cycle runner only) |

---

## `cycle/runner.py`

Exports `run_cycle(world, units, factions, domains, logger) -> CycleResult`.
Thin orchestrator — delegates each phase to declaration, resolution, end_of_cycle.

---

## `cycle/declaration.py`

Steps 0–2.
- Recalculate domain utilization
- Resolve leaderless proxy
- Update SM attention
- Call `select_npc_actions()` for all units
- Call `select_faction_action()` for all factions

---

## `cycle/resolution.py`

Steps 3–9.
- Support Faction registration
- City-wide block resolution
- Specific block resolution
- Spy action resolution
- Remaining unit action dispatch
- Faction action dispatch
- active_supporters reset

---

## `cycle/end_of_cycle.py`

Steps 10–12.
- Health decay, entrench updates, focus decay, faction entrench decay
- Floor advancement (if entrench ≥ 50)
- Unit generator, emergence checks, cascade resolution
- State written to SQLite

---

## `events/cascades.py`

- `check_for_cascades()` — triggers on decisive hits that drop floor rating
- `fire_retirement_cascade()` — triggers on unit retirement
- `_fire_cascade()` — internal logic

---

## `events/faction.py`

- `check_faction_collapse()` — fires when faction entrench decay hits floor
- `apply_faction_entrench_decay()` — per-cycle faction entrench reduction
- Collapse outcomes by floor: 2–3 dissolve, 4–5 50/50, 6+ split

---

## `events/world.py`

- `process_world_chaos()` — chaos-driven events
- `tick_power_vacuums()` — power vacuum duration
- `update_sm_attention()` — SM state transitions
- `check_unit_retirement()` — health-based retirement
- `check_emergence()` — Level 1 → Level 2 emergence (1% chance per faction)
- `generate_unit_random()` — random new unit generation

---

## `npc/weights.py`

Weight tables — no functions, just constants.

- `BASE_WEIGHTS` — action priority defaults
- `TRAIT_WEIGHTS` — per-trait action modifiers (14 unit traits)
- `FACTION_TRAIT_WEIGHTS` — per-trait faction action modifiers
- `RELATIONSHIP_ACTION_BOOSTS` — domain relationship bonuses

---

## `npc/behavior.py`

- `build_action_weights()` — merges trait weights + health/entrench adjustments
- `select_npc_actions()` — top-3 threshold selection, returns `List[NPCPlan]`
- `select_faction_action()` — returns `FactionPlan`
- `_l1_budget()`, `_l1_cost()` — L1 budget system helpers
- `apply_tension_modifier()` — focus tension scaling

---

## `npc/targeting.py`

- `_pick_target_by_domain_relationship()` — faction/unit target bias
- `_pick_expose_target()` — spy targeting
- `_pick_harm_target()` — attack targeting (spy gate required)
- `_pick_primary_domain()` — active domain selection
- `update_focus_scores()` — decay focus slots each cycle
- `add_focus()` — create or update focus slot

---

## `formulas.py`

All pure calculation functions. No side effects. Imports from `models.py` and `math` only.

Key functions: `unit_weight()`, `grow_increment()`, `roll_result()`, `resolve_contest()`,
`get_faction_capacity()`, `faction_effective_power()`, `faction_action_rating()`,
`entrench_to_bonus()`, `calculate_inertia()`, `update_entrench()`, `harm_rating_damage()`,
`recruit_chance()`, `kick_chance()`, `retirement_chance()`, `unit_health_decay()`,
`compute_attention_state()`, `domain_cap_resistance()`, `join_desire()`.

---

## `logger.py`

`SimLogger` class. Owns narrative.log and system.log handles.

- `log_dramatic(event)` — writes to both logs
- `log_system(event)` — writes to system.log only
- `is_dramatic(event)` — classification logic
- `narrate(event)` — CycleEvent → prose string
- `close()` — flush and close
