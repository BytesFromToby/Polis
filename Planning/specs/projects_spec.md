# Projects Specification

**Version:** v5
**Date:** 2026-06-05
**Supersedes:** v4 (2026-05-19)

Demo rework. Base projects are now **repeatable, counted infrastructure** — one type per domain — and they are the **lever that grows a domain's `cap`**. A project is no longer a unique structure with a hand-authored effect; it's a stackable thing factions and the Mayor build to expand a domain's ceiling. Build is unified to **4 work units**. Source of decisions: `../proposals/projects-rework.md`. Math: `../reference/formulas.md`. Faction model (rank/level/health, Break, `utilization = Σ level`): `../specs/faction-behavior_spec.md`, `../specs/cycle-runner_spec.md`.

This rework reconciles the v4 spec's stale `floor`/`entrench`/bespoke-effect references — all removed by the demo redesign.

---

## Scope

- **Does:** define **base projects** (one repeatable type per domain, uniform `+2` cap when intact, counted), fuse them with the domain-cap system (`cap = base_cap + Σ project contribution`, where `base_cap = round(initial Σ level × CAP_HEADROOM_MULT)`), and unify the build model to 4 work units built by faction labor (chancy) or Mayor gold (guaranteed).
- **Does NOT:** rework `tax_collection` projects — they are **out of scope for v5**, left exactly as coded (they retain the legacy `build_cost`/`build_time`/`faction_build_actions` fields, which therefore are NOT removed from the model).
- **Does NOT:** implement count-scaling difficulty ("each new one harder") — the `count` is exposed but no difficulty hooks onto it yet (deferred).
- **Does NOT:** restore `faction_level` projects or bespoke per-project `ProjectEffect`s — removed; a richer special tier may be rebuilt later on top of this model.

---

## Concepts & Data

A **base project** is a project with `category == "base"`. Each completed base project is its **own instance** (own `health`, individually sabotageable). All base projects in a domain share the same name (e.g. every Harbor base project is a `Docks`); `count` = the number of base-project instances of that type in the domain (derived — used for display and future scaling).

**Base project names** (one per domain):

| Domain | Name | | Domain | Name |
|---|---|---|---|---|
| harbor | Docks | | academy | Lyceum |
| trade | Agora | | aristocracy | Estate |
| guilds | Workshop | | temples | Temenos |
| military | Barracks | | professions | Gymnasion |

Project fields used by base projects: `id`, `name`, `domains` (single-element: the owning domain), `category="base"`, `status`, `health`, `build_progress` (0–4 work units, construction only), `initiated_by`. Legacy fields (`build_cost`, `build_time`, `faction_build_actions`, `tax_level`, `faction_level`, `effects`) are **unused by base projects** but retained on the dataclass for `tax_collection`.

`CAP_HEADROOM_MULT = 1.20` lives in `engine/formulas.py` as a named constant.

---

## Feature: Domain cap derivation

A domain's `cap` is no longer authored data — it is derived. At game start (cycle 0), `base_cap` is fixed from the starting faction fill; thereafter the only thing that moves a domain's cap is its active base projects, by their health tier. Cap is re-derived each cycle.

- Input: a domain, its factions (for the cycle-0 base), and its base-project instances.
- Output: the domain's current `cap` (int).

Rules:
- `base_cap[domain] = round(initial_fill × 1.20)`, where `initial_fill = Σ level` of that domain's factions **at cycle 0**. Computed once at load; frozen thereafter. (Authored `cap` values in `data/domains.json` are ignored/overwritten.)
- Each cycle: `cap[domain] = base_cap[domain] + Σ contribution(p)` over **active** base projects `p` in the domain, where `contribution` is by health tier:
  - intact (health 51–100) → **+2**
  - damaged (health 21–50) → **+1**
  - critical (health 1–20) → **0**
  - under-construction / destroyed → **0** (not active)
- `utilization` (Σ level) is unchanged; cap is compared against it by the existing cap-resistance ramp and Grow blocking.
- If utilization exceeds a freshly-lowered cap (e.g. a Docks was destroyed), no faction is forced down — growth simply blocks until utilization falls below cap again.

**Done when:**
- At cycle 0, each domain's `base_cap == round(initial Σ level × 1.20)` and authored `data/domains.json` cap values do not affect it  `[automated]`
- A domain with no base projects has `cap == base_cap` every cycle  `[automated]`
- One intact base project raises the domain's `cap` by exactly 2; a damaged one by 1; a critical, under-construction, or destroyed one by 0  `[automated]`
- Cap is re-derived each cycle (damaging an active base project from intact→damaged drops that domain's cap by 1 the same cycle)  `[automated]`
- `CAP_HEADROOM_MULT` is a single named constant in `engine/formulas.py` (changing it changes every domain's base_cap)  `[automated]`

---

## Feature: Build model (4 work units)

A base project completes after **4 work units**. There are two ways to add a unit, with different cost and reliability.

- Input: an under-construction base project; a builder (a faction action, or a Mayor buy).
- Output: `build_progress` incremented (or not); on reaching 4 → status `active`, `health = 100`.

Rules:
- **Faction `BuildProject`** — a faction whose `domain_primary` is the project's domain spends its action: roll `d20 + level` vs **DC 12**. Success → `build_progress += 1`; failure → no change. **Domain-gated** (a faction cannot build a project outside its domain — that resolves `blocked`). Free (costs only the action).
- **Mayor buy** — the Mayor spends **50 gold + 1 action point** → `build_progress += 1`, guaranteed. Repeatable within a turn while gold and action points remain (3 AP + 150 gold → +3 units). If gold < 50 or no action point: no unit added and nothing is charged.
- Reaching `build_progress == 4` flips the project to `active` with `health = 100` in the same resolution that added the 4th unit.
- The legacy upfront `build_cost` is **not charged** for base projects.

**Done when:**
- A successful faction `BuildProject` (roll ≥ 12) on an own-domain base project adds exactly 1 work unit; a failed roll adds 0  `[automated]`
- A faction `BuildProject` targeting a base project outside its `domain_primary` resolves `blocked` and adds 0  `[automated]`
- A Mayor buy with ≥50 gold and ≥1 action point adds exactly 1 work unit and deducts 50 gold + 1 AP  `[automated]`
- A Mayor buy with <50 gold or 0 action points adds 0 work units and deducts nothing  `[automated]`
- With 3 action points and ≥150 gold, the Mayor can add 3 work units in one turn  `[automated]`
- A base project reaching 4 work units becomes `active` with `health == 100` in that same resolution  `[automated]`
- No `build_cost` (lump gold) is deducted when a base project is initiated or built  `[automated]`

---

## Feature: Initiation

A base project comes into being when a builder breaks ground in a domain that has none under construction. At most **one** base project per domain may be under construction at a time.

- Input: a domain with no base project currently `under_construction`.
- Output: a new base-project instance (`status="under_construction"`, `build_progress=0`, named for the domain), to which the breaking-ground build action then applies normally.

Rules:
- **Mayor** may initiate a base project in **any** domain, any time (subject to the one-under-construction-per-domain rule). The Mayor buy that breaks ground creates the instance, then applies its guaranteed +1 unit.
- **NPC factions** initiate under **near-cap pressure**: a faction whose own domain has `utilization ≥ 0.85 × cap` **and** no base project under construction there may choose `BuildProject`, which creates the instance and applies its build roll. A faction never initiates when a base project is already under construction in its domain, and never below the 0.85 threshold via this path.
- Initiation has **no level gate and no resource cost** beyond the breaking-ground build action itself.

**Done when:**
- Initiating creates one base-project instance with `status=="under_construction"`, `build_progress` starting at 0, and the domain's base-project name  `[automated]`
- At most one base project per domain is `under_construction` at once (a second initiation in the same domain is refused while one is in progress)  `[automated]`
- An NPC faction can select `BuildProject` to initiate when its domain is `≥ 0.85 × cap` with none under construction; it does not select initiation when one is already under construction in its domain  `[automated]`
- The Mayor can initiate a base project in a domain with no factions of its own  `[automated]`

---

## Feature: Damage, defense & destruction (unchanged from v4)

Active base projects retain v4 structural health, defense, and sabotage behavior. `SabotageProject` is **open to any faction** (no domain gate) — the deliberate asymmetry vs. domain-gated building.

- Input: an active/damaged base project targeted by `SabotageProject` (a base project still `under_construction` is not a valid target — it builds via `build_progress`, not structural `health`, so it has none to lose).
- Output: reduced `health`; `destroyed` at 0.

Rules (carried from v4):
- Sabotage is contested: attacker `d20 + level` vs `d20 + project_defense_rating (+ build bonus)`, where `project_defense_rating = max(1, health // 20)` and build bonus = successful builds this cycle (cap +2).
- Decisive: `health −25`; partial: `−10`; fail: none. `health` floors at 0 → `status = "destroyed"` (projects, unlike factions, can be destroyed).
- A destroyed base project is removed from play and contributes 0 to cap (see Cap derivation).

**Done when:**
- A decisive Sabotage reduces a base project's `health` by 25; partial by 10; fail by 0  `[automated]`
- A base project whose `health` reaches 0 becomes `destroyed` and stops contributing to its domain's cap  `[automated]`
- `SabotageProject` is not domain-gated (a faction can target a base project outside its own domain)  `[automated]`

---

## Feature: Maintenance (unchanged from v4)

The treasury pays a flat `2 × active_project_count` gold per cycle covering all active projects collectively (base and tax_collection). Stacked base projects therefore carry upkeep — a natural brake on unbounded cap growth. If the treasury cannot cover it, maintenance is silently skipped that cycle (no per-project damage).

**Done when:**
- Treasury maintenance per cycle equals `2 × (count of active projects)`  `[automated]`
- When the treasury cannot afford maintenance, it is skipped with no project taking damage  `[automated]`

---

## Open Questions

- **Count-scaling difficulty (deferred).** `count` (active base projects of a type in a domain) is exposed but nothing scales off it yet. When wanted, "each new one is harder" attaches to one of: more work units, a higher DC, or higher Mayor gold/cycle. Not part of this build.
- **tax_collection rework (later).** Tax projects are left on the v4 model this pass; a future spec moves them onto the work-unit build model and decides whether any ship pre-built at game start.
