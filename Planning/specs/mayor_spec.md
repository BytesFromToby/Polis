# Mayor Specification

**Version:** v3
**Date:** 2026-06-05

The Mayor is the player. The Mayor does not directly control factions — actions are indirect, costly, and create pressure rather than commands. The city runs on its own; the Mayor nudges it.

**v3 (demo focus):** the action roster is cut to **8 levers**. Every tool that let the Mayor *directly script faction behavior or rewire the faction-to-faction web* (Broker a Deal, Plant a Rumor, Appoint an Official, Issue a Decree, Turn a Blind Eye) is removed, so that the **LLM audience** becomes the single channel for influencing what factions do — the headline demo feature. `Withhold Resources` is replaced by **Sabotage**. `Commission/Repair Project` are folded into one context-aware **Build Project** action. The treasury system keeps running but exposes no player controls in the demo. References to the retired `entrench`/Block/collapse model (pre-redesign) are removed; factions now run on `rank` + `health` and never die — see `reference/data-models.md` and `reference/formulas.md`.

---

## Scope

- **Does:** define the Mayor's action pool, reputation model, and the 8 player-facing actions active in the demo, plus how the Mayor is removed.
- **Does:** specify the new **Sabotage** action and the consolidated **Build Project** action against the current `rank`/`level`/`health` faction model.
- **Does NOT:** specify the audience/negotiation flow itself — that lives in `audience_spec.md`. This spec only lists Request an Audience as a lever and its AP cost/cooldown.
- **Does NOT:** specify treasury internals (tax income, maintenance, moneylender) — those live in `treasury_spec.md`. This spec only records that the treasury system runs passively and is **not surfaced as player controls** in the demo.
- **Does NOT:** re-add any of the seven cut actions.

---

## Overview

The Mayor has:
- An **action pool** — accumulates each cycle, spent on mayor actions
- A **treasury** — separate spec covers income/expenditure
- **Reputation** — tracked per faction (and per the Public)
- **Exemptions** — factions currently excluded from taxation (`exemptions: Dict[str, int]` → faction_id: cycles_remaining)
- **Cooldowns** — per-faction action cooldowns (`cooldowns: Dict[str, int]`)
- **Deals** — binding agreements created via the audience system (`deals: Dict[str, Deal]`)

The Mayor cannot order factions. Every action is influence or investment, not control.

---

## Action Pool

The Mayor accumulates action points each cycle.

| Parameter | Value |
|---|---|
| Starting value | 1 action point |
| Gain per cycle | +1 action point |
| Maximum cap | 6 action points |
| Overflow | Excess points above cap are lost |

Action points do not carry forward past the cap. A Mayor who does nothing for 5 cycles from the start reaches cap at 6 — further inaction earns nothing.

Some actions also cost **gold** (Sabotage, Build Project). Gold is drawn from the treasury; an action whose gold cost cannot be met is refused without spending the action point.

---

## Mayor Actions

The demo roster is **8 levers**, grouped below. The action map (`engine/mayor/actions.py`) and the API allowlist (`VALID_MAYOR_ACTIONS`) contain exactly these — see the Removed Actions section for what is no longer dispatched.

### Political Actions

**Meet with Faction** (1 AP)
- Mayor requests a meeting with a faction leader
- Costs 1 AP + cooldown: cannot meet the same faction again for 10 cycles
- Outcome: immediate reputation +5 with that faction

**Publicly Endorse a Faction** (1 AP)
- Raise reputation with target faction +10
- All other factions in the same domain: reputation −3
- The Public: reputation +5 if the target is well-regarded (`health ≥ 50`), −5 otherwise

**Publicly Condemn a Faction** (1 AP)
- Reputation with target faction −15
- All other factions in the same domain: reputation +3 (the rival benefits)
- The Public: reputation +5 if condemnation is popular (`target health < 30`), neutral otherwise
- Target faction adds `angry at Mayor` relational trait (slight) — handled by trait evolution

**Request an Audience** (1 AP)
- Mayor requests an audience with a faction leader; the leader is LLM-driven and negotiates in character. A successful audience creates a binding `Deal`. 10-cycle cooldown per faction (shared with Meet's cooldown tracking).
- Full lifecycle, negotiation, and deal terms: see `audience_spec.md`. This is the **only** way to create a deal.

### Resource Actions

**Grant Tax Exemption** (1 AP) — **deferred/dormant (shelved 2026-06-08).** No income effect
under treasury_spec v3, so it is not exposed in the UI and not offered in audiences. The
backend lever and engine machinery remain dormant; see `tax-exemption-shelve_spec.md`.
- Exempt a specific faction from taxation for 1–10 cycles (Mayor sets duration at time of granting)
- Exempted faction's weight is excluded from that domain's tax income calculation
- Exempted faction gains +5 Mayor reputation per cycle of exemption
- Limit: no more than one exemption per domain at a time
- Tracked in `mayor.exemptions: Dict[str, int]` (faction_id → cycles_remaining); decremented each cycle

**Domain Jealousy:** When any faction in a domain is exempt (whether granted directly or via a deal), all other non-exempt factions in that domain gain −3 reputation with the Mayor per cycle of the exemption. This applies regardless of how the exemption was created. Factions that are themselves exempt are not affected. The jealousy hit ends when the exemption expires or is revoked.

**Sabotage** (1 AP + 50 gold) — *replaces the former Withhold Resources*
- Mayor covertly undermines a target faction. The hit is **guaranteed** (no contest) but deliberately bounded so it can never single-handedly cripple a faction.
- **Level effect:** `rank −= 0.50 × (rank − int(rank))` — erodes half of the faction's *fractional progress* above its current integer level. A faction sitting exactly on an integer (`rank == int(rank)`, margin 0) loses no rank. A single Sabotage therefore **never crosses an integer level boundary** (e.g. `3.50 → 3.25`, `3.99 → ~3.50`, never reaching `3.00`).
- **Health effect:** `health −= 0.50 × health` (percent of *current* health). 100 → 50, 50 → 25. Because it always takes half of what remains, a single Sabotage **never reduces health to 0**, so it can never directly Break a faction.
- **Reputation:** target faction −10 with the Mayor (overt — the faction knows who did it).
- **No safe floor:** a level-1 faction **can** be targeted (unlike faction-vs-faction Harm/Steal, which refuse level-1). A level-1 faction at integer rank simply takes the health bite and the reputation hit, with no rank change.
- **Cost handling:** if the Mayor lacks the action point or the treasury lacks 50 gold, the action is refused and **nothing is deducted** (action point refunded if gold was the blocker).
- **Emergent property (intended):** Sabotage alone is pure attritional setback — it cannot de-level or Break a faction. It only contributes pressure that, combined with passive health decay and rival Harm, may eventually lead to a Break.

**Build Project** (1 AP + gold) — *consolidates the former Commission Project + Repair Project*
- One context-aware action targeting a **domain** (and, for repair, that domain's base project). Behavior is chosen by the state of the domain's base project:
  - **No base project under construction** → initiate a new base project in the domain and fund its first work unit. Cost **50 gold + 1 AP**. (`mayor_build_base`)
  - **A base project is under construction** → fund one more work unit (`build_progress += 1`). Cost **50 gold + 1 AP**. The 4th unit completes the project → `status="active"`, `health=100`. (`mayor_buy_build_unit`)
  - **The domain's base project is active and damaged** (`health < 100`) → repair it by **+25 health** (capped at 100). Cost **30 gold + 1 AP**. (`repair_project`)
- The Mayor is not gated by cap or faction presence — the Mayor may build in any domain, including a faction-less one.
- **Cost handling:** insufficient AP or gold → refused, nothing deducted (action point refunded if gold was the blocker).
- Build math, the 4-work-unit model, and cap contribution live in `projects_spec.md` / `reference/formulas.md`. This action is the player-facing entry to them.

### Deals

**Break a Deal** (0 AP — always available)
- Mayor revokes an active deal unilaterally at any time, at no AP cost
- Mayor reputation with that faction: −`deal.rep_cost_if_broken` (10–35, set at negotiation)
- Mayor reputation with The Public: −8
- All Mayor-side deal terms revoked immediately (exemptions removed)
- Faction's committed terms released — faction resumes autonomous behavior
- Faction gains `angry at mayor` relational trait (moderate intensity)
- Other factions in the same domain: −3 reputation with Mayor
- See `audience_spec.md` for full lifecycle detail

---

## Removed Actions (not in the demo)

The following are **cut from the roster** — not in `engine/mayor/actions.py`'s action map, not in `VALID_MAYOR_ACTIONS`, not dispatched:

| Action | Reason removed |
|---|---|
| **Turn a Blind Eye** | Was inert — its effect ("skip the Block resolve") referenced Block, removed in the prior redesign. Faction-behavior influence is now audience-only. |
| **Issue a Decree** | Was inert — its forced-compliance flag (`_decree_active`) was never consumed. Faction-behavior influence is now audience-only. |
| **Broker a Deal** | Deterministic relationship-softening competed with the LLM audience, which is now the sole deal/relationship channel. |
| **Plant a Rumor** | Deterministic relationship manipulation — same reason as Broker. |
| **Appoint an Official** | Redundant: the Break system auto-regenerates a leader on the leader-death branch, so manual appointment solves a problem the redesign already solves. |
| **Request a Report** | Pure information; the demo UI surfaces faction state directly. |
| **Withhold Resources** | Replaced by **Sabotage** (its `_growth_blocked` flag was also never consumed). |

---

## Treasury (present, not surfaced in the demo)

The treasury **system** keeps running every cycle — tax income accrues, project maintenance is paid, and the moneylender remains available in code (`engine/mayor/treasury.py`: `process_treasury_step0`, `apply_tax_effects`, `spend_emergency_guard_surge`, `spend_public_works`, `borrow_from_moneylender`, `invest_with_moneylender`). Gold continues to flow so the economy breathes and Sabotage/Build costs are meaningful.

The demo exposes **no player-facing treasury controls** — no tax-level setting, no Emergency Guard Surge, no Public Works Allocation, no borrow/invest. These remain implemented and tested but are not part of the demo action surface. (Re-surfacing them is post-demo work.)

---

## Reputation

Reputation is tracked per faction. Range: −50 to +50.

| Score | Label | Effect |
|---|---|---|
| +30 to +50 | Trusted | Factions comply with decrees, broker deals easier |
| +10 to +29 | Favorable | Normal interaction |
| −9 to +9 | Neutral | Baseline |
| −10 to −29 | Suspicious | Actions cost +1 action point with this faction |
| −30 to −50 | Hostile | Actions have −10 to outcome rolls with this faction |

Reputation with The Public is also tracked and follows the same scale. Public reputation affects end conditions.

### Reputation Decay

Reputation decays toward 0 slowly when no interaction occurs:
- +50 to +11: −1 per cycle
- −50 to −11: +1 per cycle
- −10 to +10: no decay

---

## Mayor Removal

The Mayor is removed when a removal coalition forms. Conditions that contribute:

- The Public reputation ≤ −30: starts removal countdown (5 cycles to recover or be removed)
- 3 or more factions at hostile (≤ −30): coalition pressure — each cycle beyond this is −2 to Public reputation
- Treasury bankruptcy: immediate −20 Public reputation; 3 cycles to resolve or removal triggers

Removal is not instant. It is a spiral — declining reputation accelerates other declines. The player can stabilize if they act in time.

*(The former "faction collapse caused by Mayor action" trigger is removed: factions no longer collapse or die — at `health` 0 they Break, per `reference/data-models.md`. The Mayor has no action that can directly Break a faction.)*

---

## Done when

### Sabotage
- Sabotage costs 1 AP **and** 50 gold; on success both are deducted (action point spent, treasury −50)  `[automated]`
- Sabotage with insufficient gold (or no AP) is refused and deducts nothing; the action point is refunded if gold was the blocker  `[automated]`
- Sabotage reduces target `rank` by 50% of its fractional margin: a faction at `rank 3.50` → `3.25`; a faction at integer `rank` (e.g. `3.00`) loses no rank  `[automated]`
- Sabotage reduces target `health` by 50% of current health: `100 → 50`, `50 → 25`  `[automated]`
- A single Sabotage never crosses an integer level boundary and never reduces `health` to 0 (cannot Break a faction)  `[automated]`
- Sabotage sets target reputation with the Mayor to its prior value −10  `[automated]`
- A level-1 faction is a valid Sabotage target (the action is not refused on the safe-floor grounds that gate faction Harm/Steal)  `[automated]`

### Build Project (context-aware)
- Build on a domain with **no** base project under construction creates one (`status="under_construction"`, `build_progress=1`) and charges 50 gold + 1 AP  `[automated]`
- Build on a domain with a base project **already under construction** adds one work unit (`build_progress += 1`) and charges 50 gold + 1 AP  `[automated]`
- Build that brings a base project to its 4th work unit completes it: `status="active"`, `health=100`  `[automated]`
- Build on a domain whose base project is **active and damaged** (`health < 100`) repairs it by +25 health (capped at 100) and charges 30 gold + 1 AP  `[automated]`
- Build with insufficient AP or gold is refused and deducts nothing (action point refunded if gold was the blocker)  `[automated]`

### Roster integrity
- `VALID_MAYOR_ACTIONS` contains exactly the 7 dispatchable levers (Meet with Faction, Publicly Endorse, Publicly Condemn, Grant Tax Exemption, Sabotage, Build Project, Break a Deal) and none of the seven removed actions. (Request an Audience — the 8th demo lever — is dispatched via the audience routes, not this allowlist.)  `[automated]`
- Dispatching a removed action name (e.g. `TurnABlindEye`, `IssueADecree`, `BrokerADeal`, `AllocateBudget`, `AppointAnOfficial`, `RequestAReport`, `PlantARumor`, `WithholdResources`) is rejected (API 422 / not found in the action map)  `[automated]`

### Treasury runs but is not surfaced
- A multi-cycle headless run shows treasury gold changing from passive tax income / maintenance with no player treasury action issued (the economy runs on its own)  `[automated]`
- No treasury control (tax-setting, guard surge, public works, borrow/invest) appears in the demo's player action surface  `[human-required]`

### Stale-reference cleanup
- The spec contains no normative reference to `entrench`, Block, or faction collapse/death as live mechanics (only the historical notes that explain their removal)  `[human-required]`
