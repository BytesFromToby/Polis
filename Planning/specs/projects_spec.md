# Projects Specification

**Version:** v6
**Date:** 2026-06-07
**Supersedes:** v5 (2026-06-05)

Stack rework. A domain's base projects are no longer stored as **N separate instances** —
they collapse into **one record per domain**: a counted stack with a single in-flux "top".
Because attacks and builds only ever touch the newest (top) instance, every instance below
the top is always pristine, so they never need individual storage. Each stack carries a
**count** (how many exist), a **completed** flag (is the top finished building?), and **one
unified `progress` number (0–100)** that is the top's build-fill while building and its
health once completed. This removes the awkward "finished a build that has 1 health" state,
unifies build-damage and structural-damage into one operation, and moves build length onto a
per-project **percentage step** so future projects can take any number of actions to finish.

Supersedes the v5 per-instance model (own `id`/`health`/`build_progress` per Estate). Faction
model (rank/level/health, Break, `utilization = Σ level`): `faction-behavior_spec.md`,
`cycle-runner_spec.md`. Cap math: `../reference/formulas.md`.

---

## Scope

- **Does:** define the **base-project stack** (one `BaseProjectStack` per domain — `count`,
  `completed`, unified `progress` 0–100, per-project `build_step`), the derived pool/front
  display view, and fuse stacks with the domain-cap system (`cap = base_cap + Σ
  stack_cap_contribution`). Builds raise `progress` by `build_step`%; sabotage lowers it;
  only the **top** instance is ever built, repaired, or attacked.
- **Does NOT:** rework `tax_collection` projects — they remain **legacy `Project` instances**,
  exactly as coded (`build_cost`/`build_time`/`tax_level`/`faction_build_actions` retained on
  the `Project` dataclass for them; not used by base stacks).
- **Does NOT:** implement multi-domain base projects yet — `domains` is a **list** so the
  shape is ready, but every base stack today lists exactly one domain and cap math applies to
  that one. Multi-domain cap rules are deferred to the spec that introduces the first such project.
- **Does NOT:** add count-scaling difficulty ("each new one harder"); `count` is exposed,
  nothing scales off it yet (deferred).

---

## Concepts & Data

A **base-project stack** is the new entity `BaseProjectStack`, one per domain, replacing the
v5 per-instance base `Project` records. Fields:

| Field | Type | Meaning |
|---|---|---|
| `name` | `str` | Base-project name for the domain (e.g. `Estate`); see table below |
| `domains` | `List[str]` | Domains this stack belongs to. Single-element today; a list for future multi-domain projects |
| `count` | `int` | Stack height = the highest number = how many instances exist (0 = none) |
| `completed` | `bool` | Has the **top** instance (`#count`) ever reached 100%? |
| `progress` | `float` | **0–100**, the **top** instance only: build-fill while `completed=False` (build raises, sabotage lowers); structural health once `completed=True` (sabotage lowers, repair raises) |
| `build_step` | `int` | **% one build action adds** (default `25` → 4 actions to finish). Per-project; encodes variable build length |
| `initiated_by` | `str` | `"mayor"` or faction_id — who broke ground on the current top (informational) |

**The stack invariant.** Because building, repair, and sabotage only ever act on the top
(`#count`), and a new top cannot be broken ground while the current top is in-flux (see
Initiation), **every instance below the top is always completed and pristine** (100%). The
record therefore needs to describe only the top; the rest are just a count.

**Derived pool/front view** (read off one record, used by cap, maintenance, and the UI):

| Derived | Rule |
|---|---|
| Top is **pristine** | `completed == True and progress == 100` |
| Top is **building** | `completed == False` (a fresh build site) |
| Top is **damaged** | `completed == True and progress < 100` |
| **Pool** (intact `Estate ×N`) | `count` if top pristine, else `count − 1` |
| **Front** (broken-out row) | none if top pristine, else the top (building or damaged) |
| **Active (completed) count** | `count` if `completed` else `count − 1` |

**Base-project names** (one per domain), unchanged from v5:

| Domain | Name | | Domain | Name |
|---|---|---|---|---|
| harbor | Docks | | academy | Lyceum |
| trade | Agora | | aristocracy | Estate |
| guilds | Workshop | | temples | Temenos |
| military | Barracks | | professions | Gymnasion |

`CAP_HEADROOM_MULT = 1.20` lives in `engine/formulas.py` as a named constant (unchanged).

`tax_collection` projects remain stored as legacy `Project` instances alongside the stacks.

---

## Feature: Domain cap derivation

A domain's `cap` is derived each cycle. At game start (cycle 0) `base_cap` is frozen from the
starting faction fill; thereafter only the domain's base stack moves its cap.

- Input: a domain, its factions (for the cycle-0 base), and its `BaseProjectStack`.
- Output: the domain's current `cap` (int).

Rules:
- `base_cap[domain] = round(initial_fill × 1.20)`, `initial_fill = Σ level` of that domain's
  factions **at cycle 0**. Computed once at load; frozen thereafter. Authored `cap` in
  `data/domains.json` is ignored.
- Each cycle: `cap[domain] = base_cap[domain] + stack_cap_contribution(stack)`, where for the
  domain's stack:
  - `stack_cap_contribution = (count − 1) × 2 + top_contribution` for `count ≥ 1`, else `0`.
  - `top_contribution = tier(progress)` if `completed`, else `0` (a building top adds nothing).
  - `tier(progress)`: `progress ≥ 51 → +2`; `progress ≥ 21 → +1`; else `0`. (Identical bands
    to v5 health tiers; `progress` when completed *is* health.)
  - This makes a stack of all-pristine estates contribute `count × 2`; a top damaged into the
    21–50 band drops the domain's cap by 1; a building top contributes 0.
- `utilization` (Σ level) is unchanged; cap is compared against it by the existing
  cap-resistance ramp and Grow blocking. A freshly-lowered cap never forces a faction down —
  growth simply blocks until utilization falls below cap.

**Done when:**
- At cycle 0, each domain's `base_cap == round(initial Σ level × 1.20)` and authored `data/domains.json` cap values do not affect it  `[automated]`
- A domain whose stack has `count == 0` has `cap == base_cap` every cycle  `[automated]`
- A stack of `count` all-pristine estates (`completed`, `progress == 100`) raises the domain's cap by exactly `count × 2`  `[automated]`
- A top damaged from 100 into the 21–50 band drops that domain's cap by exactly 1 the same cycle; into the 1–20 band drops it by 2 (the top contributes 0)  `[automated]`
- A building top (`completed == False`) contributes 0 to cap regardless of its `progress`  `[automated]`
- `CAP_HEADROOM_MULT` is a single named constant in `engine/formulas.py`  `[automated]`

---

## Feature: Build model (percentage progress)

A base project is built by raising the top's `progress` toward 100 in steps of `build_step`%.
Two ways to add a step, with different cost and reliability. The number of actions to finish is
`ceil(100 / build_step)` (default `build_step = 25` → 4 actions, matching v5).

- Input: a `BaseProjectStack` whose top is building (`completed == False`); a builder (a
  faction action, or a Mayor buy).
- Output: `progress` raised by `build_step`% (clamped at 100); on first reaching 100 →
  `completed = True`.

Rules:
- **Faction `BuildProject`** — a faction whose `domain_primary` is the stack's domain spends
  its action: roll `d20 + level` vs **DC 12**. Success → `progress = min(100, progress +
  build_step)`; failure → no change. **Domain-gated** (a faction cannot build outside its
  domain — resolves `blocked`). Free (costs only the action).
- **Mayor buy** — the Mayor spends **50 gold + 1 action point** → `progress += build_step`,
  guaranteed. Repeatable within a turn while gold and action points remain. If gold < 50 or no
  action point: no change and nothing is charged.
- The first time `progress` reaches 100, the top flips to `completed = True` in the same
  resolution; `progress` stays 100 (now = full health). No upfront `build_cost` is charged.

**Done when:**
- A successful faction `BuildProject` (roll ≥ 12) on the building top raises `progress` by exactly `build_step`%; a failed roll changes nothing  `[automated]`
- A faction `BuildProject` on a stack outside its `domain_primary` resolves `blocked` and changes nothing  `[automated]`
- A Mayor buy with ≥50 gold and ≥1 action point raises `progress` by `build_step`% and deducts 50 gold + 1 AP; with <50 gold or 0 AP it changes nothing and deducts nothing  `[automated]`
- A top reaching 100% becomes `completed == True` with `progress == 100` in that same resolution  `[automated]`
- A stack with `build_step == 10` requires 10 successful build actions to reach 100% (variable build length is honored)  `[automated]`
- No `build_cost` (lump gold) is deducted when a base project is initiated or built  `[automated]`

---

## Feature: Initiation (break ground on a new top)

Breaking ground adds a new top to the stack. At most **one in-flux top** per domain at a time
— a new top cannot be started while the current top is building or damaged ("resolve the front
first").

- Input: a `BaseProjectStack` whose top is pristine (or `count == 0`).
- Output: `count += 1`, `completed = False`, `progress = 0` (a fresh build site), to which the
  breaking-ground build action then applies normally.

Rules:
- A new top may be broken ground **only** when there is no in-flux top — i.e. the current top
  is pristine (`completed and progress == 100`) or the stack is empty (`count == 0`). If the
  top is building or damaged, initiation is **refused**.
- **Mayor** may initiate in **any** domain, any time (subject to the no-in-flux-top rule). The
  Mayor buy that breaks ground sets `count += 1, completed = False, progress = 0`, then applies
  its guaranteed `+build_step`%.
- **NPC factions** initiate under **near-cap pressure**: a faction whose own domain has
  `utilization ≥ 0.85 × cap` **and** whose stack has no in-flux top may choose `BuildProject`,
  which breaks ground and applies its build roll. A faction never initiates while a top is
  in-flux, and never below the 0.85 threshold via this path.
- Initiation has **no level gate and no resource cost** beyond the breaking-ground build action.

**Done when:**
- Initiating sets `count += 1`, `completed == False`, and `progress == 0` (a fresh build site)  `[automated]`
- Initiation is refused while the top is building (`completed == False`) or damaged (`completed and progress < 100`) — `count` does not change  `[automated]`
- An NPC faction can select `BuildProject` to initiate when its domain is `≥ 0.85 × cap` with a pristine/empty top; it does not initiate while a top is in-flux  `[automated]`
- The Mayor can initiate in a domain with no factions of its own  `[automated]`

---

## Feature: Sabotage & destruction (the front only)

Sabotage always targets the stack's **top** (`#count`) — the only attackable instance; the
pristine pool beneath it is never a legal target (the top shields the pool). A **building top is
now a valid target** (this reverses v5, which made under-construction projects un-attackable):
sabotaging a build site knocks back its build `progress`; sabotaging a completed top knocks
back its health. Both are the same operation on the same `progress` number.

- Input: a `BaseProjectStack` with `count ≥ 1`, targeted by `SabotageProject`.
- Output: reduced `progress` (clamped at 0); `count` reduced only per the destruction rule.

Rules:
- **Targeting**: `SabotageProject` resolves against the top of the addressed domain's stack —
  **open to any faction** (no domain gate, the deliberate asymmetry vs. domain-gated building).
  NPC sabotage auto-aims the top; there is no per-instance picking.
- **Contest** (carried from v5): attacker `d20 + level` vs `d20 + stack_defense_rating (+ build
  bonus)`, where `stack_defense_rating = max(1, int(progress) // 20)` (works for a building top
  too) and build bonus = successful builds this cycle (cap +2).
- **Outcome** applied to `progress` (the unified track): decisive **−25**, partial **−10**, fail
  **0**. `progress` floors at 0.
- **Destruction rule**: a sabotage **never destroys on the hit that reaches 0** — `progress`
  clamps at 0 and the instance survives as a husk. `count` drops **only when a sabotage lands
  while `progress` is already 0**: then `count −= 1`, and the revealed instance below becomes the
  new top, pristine (`completed = True, progress = 100`). If `count` was 1, the stack goes empty
  (`count = 0, completed = False, progress = 0`). This gives every instance a one-hit grace buffer
  at the bottom and applies uniformly to build sites and completed structures.

**Done when:**
- `SabotageProject` resolves against the stack's top; the pristine pool below is never targeted (a stack with a building or damaged top takes hits on that top, not on the pool)  `[automated]`
- A decisive Sabotage reduces the top's `progress` by 25; partial by 10; fail by 0  `[automated]`
- A building top (`completed == False`) is a valid Sabotage target and its `progress` is reduced (build knocked back)  `[automated]`
- A Sabotage that would take `progress` below 0 leaves it at exactly 0 with `count` unchanged  `[automated]`
- A Sabotage landing while `progress == 0` reduces `count` by 1 and sets the revealed top to `completed == True, progress == 100` (or empties the stack when `count` was 1)  `[automated]`
- `SabotageProject` is not domain-gated (a faction can attack a stack outside its own domain)  `[automated]`

---

## Feature: Repair (the damaged top)

The Mayor repairs a damaged top, raising its `progress` back toward 100. When it reaches 100 it
is pristine again and folds into the pool (no separate front row).

- Input: a `BaseProjectStack` whose top is damaged (`completed == True and progress < 100`).
- Output: `progress` raised by `build_step`% (clamped at 100), `30 gold + 1 action point` spent.

Rules:
- Repair applies **only** to a damaged completed top. A building top (`completed == False`) is
  built, not repaired; a pristine top needs none.
- **Mayor** spends **30 gold + 1 action point** → `progress = min(100, progress + build_step)`.
  If gold < 30 or no action point: no change, nothing charged.
- Repair uses the same `build_step`% the project builds at — one knob scales both build and
  repair with the project's size.
- The Mayor's single project lever stays **context-aware** on a domain id: a damaged top →
  repair; otherwise → build (funding the building top, or breaking ground first).

**Done when:**
- A Mayor repair on a damaged top (≥30 gold, ≥1 AP) raises `progress` by `build_step`% and deducts 30 gold + 1 AP  `[automated]`
- A repair taking `progress` to 100 makes the top pristine (folds into the pool — pool count rises by 1, no front remains)  `[automated]`
- Repair on a pristine or building top is refused (no change, nothing charged)  `[automated]`
- The Mayor's domain-targeted project lever repairs when the top is damaged and builds otherwise  `[automated]`

---

## Feature: Maintenance (unchanged rule, new count source)

The treasury pays a flat `2 × active_project_count` gold per cycle covering all active projects
collectively. `active_project_count` now sums the **active (completed) count** of every base
stack (`count` if `completed` else `count − 1`) plus active legacy `tax_collection` projects.
If the treasury cannot cover it, maintenance is silently skipped that cycle (no damage).

**Done when:**
- Treasury maintenance per cycle equals `2 × (Σ active completed base instances + active tax_collection projects)`; a building top is not counted as active  `[automated]`
- When the treasury cannot afford maintenance, it is skipped with no project taking damage  `[automated]`

---

## Reference reconciliation (at build time, not now)

These as-built docs must be updated by the builder when this rework lands (per the Change rules):
- `../reference/data-models.md` — replace the base-project `Project` field rows with the
  `BaseProjectStack` entity; keep the legacy `Project` rows for `tax_collection`.
- `../reference/formulas.md` — restate `project_cap_contribution` on the stack
  (`(count − 1) × 2 + top tier`) and note `build_step` / the percentage build track.
- `../reference/architecture.md` — note the base-project storage change (stack per domain) if it
  affects the system map.
- `actions_spec.md` (SabotageProject / BuildProject one-liners) and `game-ui_spec.md` (Projects
  Panel stacked display) are updated alongside this spec.

## Open Questions
- **Build-site defense (resolved here, flagged for review).** A fresh build site at `progress
  == 0` has `stack_defense_rating == max(1, 0) == 1`. If a tougher floor is wanted for
  early-stage sites, raise this minimum — currently it mirrors the v5 `max(1, …)` floor.
- **Count-scaling difficulty (deferred).** `count` is exposed; nothing scales `build_step`, DC,
  or sabotage off it yet.
- **tax_collection rework (later).** Tax projects stay on the legacy `Project` model this pass.
