# Mayor Specification

**Version:** v2
**Date:** 2026-05-19

The Mayor is the player. The Mayor does not directly control factions — actions are indirect, costly, and create pressure rather than commands. The city runs on its own; the Mayor nudges it.

---

## Overview

The Mayor has:
- An **action pool** — accumulates each cycle, spent on mayor actions
- A **treasury** — separate spec covers income/expenditure
- **Reputation** — tracked per faction (and per the Public)
- **Exemptions** — factions currently excluded from taxation (`exemptions: Dict[str, int]` → faction_id: cycles_remaining)
- **Cooldowns** — per-faction action cooldowns (`cooldowns: Dict[str, int]`)

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

Some actions cost multiple points and lock commitment across several cycles (see Projects spec). While a multi-cycle action is committed, those action points are unavailable.

---

## Mayor Actions

### Political Actions

**Meet with Faction** (1 action)
- Mayor requests a meeting with a faction leader
- Costs 1 action + cooldown: cannot meet the same faction again for 10 cycles
- Outcome: immediate reputation +5 with that faction, plus one opportunity (see below)
- Opportunity: Mayor can pair the meeting with one of: endorse, condemn, broker deal
- Future: triggers audience system (POSSIBLE — not committed)

**Publicly Endorse a Faction** (1 action)
- Raise reputation with target faction +10
- All factions in the same domain: reputation −3
- The Public: reputation +5 if target is well-regarded, −5 if target is disliked

**Publicly Condemn a Faction** (1 action)
- Reputation with target faction −15
- All factions in the same domain: reputation +3 (the rival benefits)
- The Public: reputation +5 if condemnation is popular (target health < 30), neutral otherwise
- Target faction adds `angry at Mayor` relational trait (slight) — future: player-facing impact

**Broker a Deal** (2 actions)
- Mayor attempts to reduce hostility between two factions
- Requires: Mayor reputation ≥ 10 with both factions
- Outcome roll: d20 + average of the two reputation scores, vs DC 15
- Success: both factions gain `trusts other` relational trait (slight) — enemy relationship downgraded one step
- Failure: reputation −5 with both factions, no effect on relationship

### Resource Actions

**Allocate Budget to Domain** (1 action, 1 treasury cost)
- Choose a domain. That domain's domain.drift increases by +0.02 for 3 cycles (temporary improvement)
- Factions in that domain gain a +5 bonus to one action roll this cycle (Grow or Protect)
- Reputation +5 with all factions in that domain

**Withhold Resources** (1 action)
- Choose a faction. That faction's growth is blocked for 1 cycle
- That faction's reputation with Mayor −10
- If faction has `aggressive` or `angry at` trait toward Mayor: may retaliate (−health or −entrench event next cycle)

**Commission Project** (variable cost — see Projects spec)

**Grant Tax Exemption** (1 action)
- Exempt a specific faction from taxation for 1–10 cycles (Mayor sets duration at time of granting)
- Exempted faction's weight is excluded from that domain's tax income calculation
- Exempted faction gains +5 Mayor reputation per cycle of exemption
- Limit: no more than one exemption per domain at a time
- Tracked in `mayor.exemptions: Dict[str, int]` (faction_id → cycles_remaining); decremented each cycle

**Domain Jealousy:** When any faction in a domain is exempt (whether granted directly or via a deal), all other non-exempt factions in that domain gain −3 reputation with the mayor per cycle of the exemption. This applies regardless of how the exemption was created. Factions that are themselves exempt are not affected. The jealousy hit ends when the exemption expires or is revoked.

**Break a Deal** (0 actions — always available)
- Mayor revokes an active deal unilaterally at any time, at no AP cost
- Mayor reputation with that faction: −`deal.rep_cost_if_broken_by_mayor` (10–35, set at negotiation)
- Mayor reputation with The Public: −8
- All mayor-side deal terms revoked immediately (exemptions removed)
- Faction's committed terms released — faction resumes autonomous behavior
- Faction gains `angry at mayor` relational trait (moderate intensity)
- Other factions in the same domain: −3 reputation with mayor
- See `audience_spec.md` for full lifecycle detail

### Authority Actions

**Issue a Decree** (2 actions)
- Mayor issues a ruling affecting a domain (tariff, restriction, mandate)
- Factions in that domain must comply or resist
- Compliance: faction with `conservative` or `defensive` trait — rolls d20 vs DC 10. Success = forced Protect action this cycle
- Resistance: faction with `aggressive` or `ambitious` trait — reputation −5, faction gets +10 to their chosen action this cycle
- The Public: reputation +5 if decree is popular (reduces chaos), −5 if unpopular (raises taxes)

**Appoint an Official** (2 actions)
- Mayor appoints a new leader to a leaderless faction
- Leaderless faction gets a generated leader with traits chosen by Mayor (from available trait list)
- Reputation +15 with that faction
- Other factions in same domain: reputation −5 (they didn't get the appointment)

**Turn a Blind Eye** (1 action)
- Choose a faction. That faction's Harm or Steal action this cycle goes uncontested (resolve block skipped)
- Reputation +10 with that faction
- The Public: reputation −5
- If discovered (Public health < 30): additional −10 reputation with The Public

### Information Actions

**Request a Report** (1 action)
- Reveals full trait list and current action plan for one faction this cycle (what they declared)
- No game state change — information only

**Plant a Rumor** (1 action)
- Choose a faction and a target faction
- Target faction adds `distrusts X` toward another faction at slight intensity (Mayor-chosen)
- This shifts the target's action weighting for 3 cycles, then decays naturally

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
- Faction collapse caused by Mayor action (Turn a Blind Eye + resulting harm): Public reputation −10

Removal is not instant. It is a spiral — declining reputation accelerates other declines. The player can stabilize if they act in time.

---

## Audience System

See `audience_spec.md` for the full specification.

The Mayor requests an audience with a faction leader (1 AP, 10-cycle cooldown per faction). The faction leader is LLM-driven — they respond in character, negotiate terms, and decide whether to accept. A successful audience creates a binding `Deal` with committed terms on both sides. Audiences are the only way to create deals.
