# Data Models (Reference)

Shared entity definitions cited by the feature specs. Reference doc — definitional,
no **Done when:** items. (Re-tiered from `specs/data-models_spec.md`, 2026-05-25.)

**Version:** v6
**Date:** 2026-05-19
**Updated:** 2026-05-23 — Aligned with `engine/models.py` (data-models speccheck pass): added `Faction.floor`/`leadership_need`, `ActionResult.margin`; reconciled helper names, outcome values, and field defaults; delegated special-factions/events entities to their own specs.

Units removed. Leader embedded in Faction. SM domain removed. Personality system added to Faction.

> **Entities defined elsewhere:** special-factions entities (`ThePublic`, `ThreatEffect`, `ExternalThreat`) live in `../specs/special-factions_spec.md`; events entities (`GameEvent`, `EventEffect`, `CascadeSpec`) live in `../specs/events_spec.md`. They exist in `models.py` but are owned by those specs, not duplicated here.

---

## Core Entities

### `Leader`

Embedded object on `Faction`. Not a separate model.

| Field | Type | Default | Persistent | Notes |
|---|---|---|---|---|
| `name` | `str` | required | Yes | Display name |
| `traits` | `List[str]` | `[]` | Yes | Personal trait tags — influence faction behavior |
| `status` | `str` | `"present"` | Yes | `"present"`, `"weakened"`, `"absent"` |
| `personality_notes` | `List[str]` | `[]` | Yes | Free-text sentences added over time — audience memories, notable events |

Leader status effects:
- `present` — full faction action weight
- `weakened` — faction action weight ×0.75
- `absent` — leader is away; faction acts at reduced capacity

---

### `FactionTrait`

A trait entry in a faction's personality list.

| Field | Type | Default | Persistent | Notes |
|---|---|---|---|---|
| `trait` | `str` | required | Yes | Trait name (e.g., `"aggressive"`, `"distrusts"`) |
| `intensity` | `str` | `"moderate"` | Yes | `"slight"`, `"moderate"`, `"strong"`, `"very"` |
| `target_id` | `str \| None` | `None` | Yes | Faction ID if relational trait; None if general |

Examples:
- `{ trait: "aggressive", intensity: "very", target_id: None }` — generally aggressive
- `{ trait: "distrusts", intensity: "strong", target_id: "pyrrhidai" }` — distrusts a specific faction

---

### `Faction`

| Field | Type | Default | Persistent | Notes |
|---|---|---|---|---|
| `id` | `str` | required | Yes | Unique identifier |
| `name` | `str` | required | Yes | Display name |
| `domain_primary` | `str` | required | Yes | Primary domain id |
| `rating` | `float` | `1.0` | Yes | 1.0–5.0; floor used for action resolution |
| `floor` | `int` | `int(rating)` | Yes | Last *confirmed* level; advances step-wise (entrench-gated). Distinct from the `floor_rating` property (`int(rating)`); auto-inits to `int(rating)` |
| `health` | `int` | `75` | Yes | 1–100 |
| `entrench` | `int` | `75` | Yes | 1–100; organizational entrenchment |
| `leader` | `Leader` | required | Yes | Embedded leader — every faction always has one |
| `traits` | `List[FactionTrait]` | `[]` | Yes | Personality trait list with intensity and optional target |
| `relationships` | `List[FactionRelationship]` | `[]` | Yes | Specific faction-to-faction overrides |
| `active_block_target` | `str` | `""` | Yes | Faction id of standing block trap; `""` if none; persists until fired |
| `committed_action` | `str` | `""` | Yes | Action name if faction is under a deal commitment; `""` if none |
| `committed_target` | `str` | `""` | Yes | Target id for the committed action; `""` if no target required |
| `committed_deal_id` | `str` | `""` | Yes | Deal id this commitment comes from; `""` if none |
| `committed_abstain_action` | `str` | `""` | Yes | Action type faction has agreed not to take; `""` if none |
| `committed_abstain_target` | `str` | `""` | Yes | Target faction id for the abstain commitment; `""` if none |

**Cycle-only fields (reset each cycle, not stored):**

| Field | Type | Notes |
|---|---|---|
| `action_cancelled` | `bool` | Set True when a decisive block fires against this faction this turn |
| `action_downgraded` | `bool` | Set True when a partial block fires; action is downgraded before resolution |
| `unstable_stacks` | `int` | Penalty stacks; −1 per stack to rolls, max 3 |

**Helper methods:**

| Method | Returns | Notes |
|---|---|---|
| `is_leaderless() -> bool` | Bool | `leader.status == "absent"` |
| `floor_rating` (property) | `int` | `int(rating)` |
| `get_trait(name) -> FactionTrait \| None` | Trait or None | Find general trait by name |
| `get_relational_trait(name, target_id) -> FactionTrait \| None` | Trait or None | Find targeted trait |
| `get_faction_relationship(faction_id) -> str \| None` | Trait or None | Faction-specific relationship override |
| `reset_cycle_state()` | None | Clears the cycle-only fields |

---

### `Domain`

| Field | Type | Default | Persistent | Notes |
|---|---|---|---|---|
| `id` | `str` | required | Yes | Unique identifier |
| `name` | `str` | required | Yes | Display name |
| `cap` | `int` | required | Yes | Max weight capacity |
| `utilization` | `float` | `0.0` | Yes | Sum of faction weights in domain |
| `drift` | `float` | `0.0` | Yes | Natural utilization change per cycle |
| `relationships` | `List[DomainRelationship]` | `[]` | Yes | Domain-to-domain dispositions |

**The 14 domains (Social Media removed):**

Street, Political, Religion, Bureaucracy, Finance, Police, Underworld, Legal, Health, High Society, Industry, Traditional Media, Transportation, University

---

### `FactionRelationship`

| Field | Type | Default | Persistent | Notes |
|---|---|---|---|---|
| `faction_id` | `str` | required | Yes | Target faction ID |
| `trait` | `str` | required | Yes | `"Friend"` \| `"Foe"` \| `"Neutral"` |

---

### `DomainRelationship`

| Field | Type | Default | Persistent | Notes |
|---|---|---|---|---|
| `domain_id` | `str` | required | Yes | Target domain ID |
| `trait` | `str` | required | Yes | `"Friend"` \| `"Foe"` \| `"Hide"` \| `"Client"` \| `"Neutral"` |

---

### `WorldState`

| Field | Type | Default | Persistent | Notes |
|---|---|---|---|---|
| `cycle` | `int` | `0` | Yes | Current cycle number |
| `chaos` | `Dict[str, float]` | `{}` | Yes | Domain id → chaos value |
| `power_vacuums` | `List[dict]` | `[]` | Yes | `{domain_id, cycles_remaining}` |
| `initiative_order` | `List[str]` | `[]` | No | Faction ids in turn order for the current cycle; re-rolled each cycle |

---

## Result and Plan Types (Cycle-Only)

### `ActionResult`

| Field | Type | Notes |
|---|---|---|
| `actor_id` | `str` | Faction ID |
| `action` | `str` | Action name |
| `target_id` | `str \| None` | Target faction or domain ID |
| `domain` | `str \| None` | |
| `outcome` | `str` | `"decisive"`, `"partial"`, `"fail"`, `"blocked"`, `"no_op"` |
| `margin` | `int` | `0`; roll margin (attacker − defender) |
| `roll_attacker` | `int` | `0` |
| `roll_defender` | `int` | `0` |
| `delta` | `float` | Magnitude of effect |
| `narrative` | `str` | Readable description |
| `dramatic` | `bool` | Converted to int scale on write to CycleEvent |

---

### `FactionPlan`

| Field | Type | Notes |
|---|---|---|
| `faction_id` | `str` | |
| `action` | `str` | |
| `target_id` | `str \| None` | |
| `domain` | `str \| None` | |
| `cancelled` | `bool` | |

---

### `CycleEvent`

| Field | Type | Notes |
|---|---|---|
| `cycle` | `int` | |
| `actor_id` | `str` | |
| `action` | `str` | |
| `target_id` | `str \| None` | |
| `domain` | `str \| None` | |
| `narrative` | `str` | |
| `dramatic` | `int` | 0 = routine, 1 = notable, 2 = significant, 3 = major |

---

## Mayor and Treasury

### `DealTerm`

| Field | Type | Default | Notes |
|---|---|---|---|
| `type` | `str` | required | `"tax_exemption"` \| `"endorsement"` \| `"committed_action"` \| `"committed_abstain"` |
| `action` | `str` | `""` | Action name — used for `committed_action` and `committed_abstain` |
| `target_id` | `str` | `""` | Target faction/project id — used for `committed_action` with a target and `committed_abstain` |
| `duration` | `int` | `0` | Cycles; 1–10 |

---

### `Deal`

| Field | Type | Default | Notes |
|---|---|---|---|
| `id` | `str` | required | Unique id (e.g. `"deal_f1_042"`) |
| `faction_id` | `str` | required | The faction party to the deal |
| `mayor_terms` | `List[DealTerm]` | `[]` | What the mayor has committed to |
| `faction_terms` | `List[DealTerm]` | `[]` | What the faction has committed to |
| `cycles_remaining` | `int` | required | Counts down each cycle |
| `total_duration` | `int` | required | Original duration — for reference |
| `status` | `str` | `"active"` | `"active"` \| `"fulfilled"` \| `"broken_by_mayor"` \| `"broken_by_faction"` \| `"suspended"` |
| `rep_cost_if_broken` | `int` | `20` | Mayor reputation penalty if mayor breaks; set by LLM at negotiation (10–35) |
| `cycle_created` | `int` | required | Cycle number when deal was made |
| `suspension_streak` | `int` | `0` | Consecutive cycles in suspended state; deal expires fulfilled at 3 |

**Persistent:** Yes — serialised and deserialised with game state.

---

### `Mayor`

| Field | Type | Default | Notes |
|---|---|---|---|
| `action_points` | `int` | `1` | Current unspent action points (start 1; `refill()` adds +1/cycle, capped at `action_cap`) |
| `action_cap` | `int` | `6` | Max action points (overflow is lost) |
| `reputation` | `Dict[str, int]` | `{}` | faction_id / "the_public" → −50 to +50 |
| `committed_actions` | `List[dict]` | `[]` | Active multi-cycle commitments |
| `cooldowns` | `Dict[str, int]` | `{}` | faction_id → cycles_until_available |
| `exemptions` | `Dict[str, int]` | `{}` | faction_id → cycles_remaining |
| `deals` | `Dict[str, Deal]` | `{}` | deal_id → Deal; all statuses retained for history |

---

### `Treasury`

| Field | Type | Default | Notes |
|---|---|---|---|
| `gold` | `int` | `500` | Current balance; game ends if this stays < 0 for 3 cycles |
| `domain_tax_rates` | `Dict[str, float]` | `{}` | domain_id → rate; missing entries default to 0.20 |
| `debt` | `int` | `0` | Outstanding debt to Moneylender |
| `debt_rate` | `float` | `0.05` | Interest rate; auto-elevated to 0.10 when debt > 500 |
| `invested` | `int` | `0` | Gold locked in current investment |
| `invest_cycles_remaining` | `int` | `0` | Cycles until investment matures |
| `invest_return_rate` | `float` | `0.0` | Multiplier applied to `invested` on maturity |
| `income_this_cycle` | `int` | `0` | Reset each cycle; not persisted |
| `expenditure_this_cycle` | `int` | `0` | Reset each cycle; not persisted |

---

## Projects

### `ProjectEffect`

| Field | Type | Default | Notes |
|---|---|---|---|
| `target` | `str` | required | `"domain"` \| `"faction"` \| `"treasury"` \| `"world"` |
| `target_id` | `str` | required | ID of the entity being affected |
| `field` | `str` | required | Attribute being modified (e.g. `"drift"`, `"rating"`) |
| `value` | `float` | required | Magnitude of effect |
| `condition` | `str` | `"always"` | `"always"` \| `"active"` \| `"damaged"` |

---

### `Project`

| Field | Type | Default | Notes |
|---|---|---|---|
| `id` | `str` | required | Unique identifier |
| `name` | `str` | required | Display name |
| `domains` | `List[str]` | required | Domains this project belongs to; factions in any listed domain can build, attack, or receive effects |
| `build_cost` | `int` | required | Gold drawn from treasury on commission |
| `build_time` | `int` | required | Cycle fallback for completion |
| `faction_build_actions` | `int` | `4` | Successful faction actions required to complete |
| `cycles_built` | `int` | `0` | Fallback cycle counter |
| `category` | `str` | `"standard"` | `"standard"` \| `"tax_collection"` |
| `tax_level` | `int` | `0` | 1–5 for tax_collection projects; unlocks that rate tier |
| `faction_level` | `bool` | `False` | When True, effects apply only to the faction matching `initiated_by`; Mayor cannot commission |
| `status` | `str` | `"under_construction"` | `"under_construction"` \| `"active"` \| `"damaged"` \| `"destroyed"` |
| `health` | `int` | `0` | Build progress 0→100 during construction; structural health 0→100 when active |
| `effects` | `List[ProjectEffect]` | `[]` | Applied each cycle while active |
| `maintenance_cost` | `int` | `10` | Stored per-project; treasury deducts flat `2 × active_project_count` globally |
| `initiated_by` | `str` | `"mayor"` | `"mayor"` or faction_id; doubles as effect owner when `faction_level=True` |

**Cycle-only fields (not persisted):**

| Field | Type | Notes |
|---|---|---|
| `build_actions_this_cycle` | `int` | Successful BuildProject actions this cycle; grants defense bonus (+1 each, max +2) |

---

### `MayorAction`

| Field | Type | Default | Notes |
|---|---|---|---|
| `action` | `str` | required | Action name (see mayor_spec) |
| `target_id` | `str` | `""` | Faction ID, domain ID, or empty |
| `cost` | `int` | `1` | Action points spent |

---

### `CycleResult`

| Field | Type | Notes |
|---|---|---|
| `cycle` | `int` | |
| `events` | `List[CycleEvent]` | All events in order |
| `faction_actions` | `int` | Total faction actions resolved |
