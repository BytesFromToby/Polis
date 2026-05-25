# Audience Specification

**Version:** v2
**Date:** 2026-05-20

The Mayor can request a formal audience with a faction leader. Audiences are the only way to create binding deals. The faction leader is driven by an LLM that opens the scene, negotiates through two player exchanges, and delivers a final decision.

---

## Overview

An audience is a structured five-step conversation:

1. **AI sets the scene** — faction leader speaks first, establishing mood and position
2. **Player prompts** — the mayor speaks (freeform)
3. **AI responds / counters** — faction leader reacts to the mayor's words
4. **Player prompts again** — the mayor has one final input
5. **AI concludes** — faction leader delivers their decision and, if accepting, the agreed terms

A completed audience either produces a `Deal` or produces nothing. There is no partial agreement.

---

## Triggering an Audience

**Cost:** 1 action point  
**Cooldown:** 10 cycles per faction (tracked in `mayor.cooldowns`)  
**Restriction:** Cannot request an audience with a faction that has an active deal — renegotiation is not available until the current deal expires, is fulfilled, or is broken.

The player selects a faction to meet. No terms are pre-selected. The negotiation emerges from the conversation.

---

## Valid Deal Terms

The LLM is told what is mechanically possible. The player negotiates freely — the LLM steers toward valid outcomes and will not promise things that cannot be implemented.

### Mayor can offer (one or more per deal):

| Term | Effect | Constraint |
|---|---|---|
| `tax_exemption` | Exempt faction from taxation for N cycles | N = 1–10; max one exemption per domain at a time |
| `endorsement` | Immediate +10 reputation with mayor | No constraint |
| `budget_allocation` | Faction's domain gets `drift +0.02` for N cycles | N = 1–5 |

### Faction can commit to (one per deal):

| Term | Description | Notes |
|---|---|---|
| `committed_action` | Faction takes a specific action every turn for N cycles | Must be a valid action for that faction; target optional |
| `committed_abstain` | Faction will not Harm or Steal a named faction for N cycles | Stored as action + target pair |

N = 1–10 cycles for all faction terms.

---

## The Conversation Flow

### Step 1 — AI sets the scene
**LLM call 1.** The faction leader opens the audience in character. This is generated from faction state, personality, recent events, and relationship with the mayor. The leader may be receptive, guarded, bitter, or eager depending on circumstances. No deal terms are mentioned yet — this is the leader establishing their position.

*Output:* 2–4 sentences of in-character dialogue. No structured JSON.

### Step 2 — Player prompts
The player types their opening. Freeform — no menu. They may state what they want, make an offer, ask a question, or probe the leader's position.

### Step 3 — AI responds / counters
**LLM call 2.** The faction leader responds to the player's words. They may agree in principle, push back, name their price, or shift the conversation. This is where deal shape emerges — the LLM may introduce what they want or react to the mayor's offer.

*Output:* 2–4 sentences of in-character dialogue. No structured JSON yet. The conversation is still live.

### Step 4 — Player prompts again
The player's second and final input. They accept what's on the table, modify the offer, or push for different terms. After this, the LLM delivers its conclusion — no further player input.

### Step 5 — AI concludes
**LLM call 3.** The faction leader delivers their final decision. In character, they accept or decline. If accepting, they restate what was agreed in their own words. The LLM also outputs a structured JSON block containing the deal terms as it understood them from the conversation.

*Output:*
```
[In-character closing — 2–3 sentences]

<deal>
{
  "accepted": true | false,
  "mayor_terms": [
    { "type": "tax_exemption", "duration": 4 }
  ],
  "faction_terms": [
    { "type": "committed_action", "action": "BuildProject", "target_id": "dock_expansion", "duration": 4 }
  ],
  "rep_cost_if_broken_by_mayor": 25,
  "memory_note": "agreed tax break for dock construction support",
  "reasoning": "<one sentence, out of character>"
}
</deal>
```

The `<deal>` block is parsed by the response parser. The in-character text is shown to the player. Invalid terms are dropped silently — if remaining terms are empty on either side, the deal is treated as rejected. `memory_note` (≤10 words) must always be present and is written to `faction_memory` regardless of outcome.

See `llm-system_spec.md` for the full system prompt structure, trait translation, response parser, and memory compression logic.

---

## Deal Lifecycle

```
created → active → fulfilled   (all cycles elapsed, both sides honoured)
                 → broken_by_mayor
                 → broken_by_faction
                 → suspended    (faction cannot execute — grace state)
```

### Ticking
Each end-of-cycle:
1. Decrement `cycles_remaining` by 1 for each active deal.
2. Check faction compliance (see Faction Breach below).
3. If `cycles_remaining` reaches 0 and status is still `active`: set status to `fulfilled`.
4. Apply domain jealousy rep hits for active tax exemptions (see `mayor_spec.md`).

### Fulfilled
The deal is archived. Mayor may request a new audience after the 10-cycle cooldown expires.

---

## Breaking a Deal — Mayor

The mayor can break any active deal at any time. This is a deliberate player action, at no AP cost.

**Immediate effects:**
- `deal.status → broken_by_mayor`
- Mayor reputation with that faction: `−deal.rep_cost_if_broken_by_mayor` (10–35)
- Mayor reputation with The Public: −8
- All mayor-side terms revoked immediately (exemption removed from `mayor.exemptions`, budget allocation cancelled)
- Faction's committed terms released — `faction.committed_action` cleared, faction resumes autonomous behavior
- Faction gains `angry at mayor` relational trait at **moderate** intensity — persists until natural decay, biases their actions toward Harm/Block targeting mayor interests
- Other factions in the same domain: −3 reputation with mayor (word travels)

A mayor that repeatedly breaks deals accelerates toward hostile factions and the removal spiral.

---

## Faction Breach

Checked each cycle after the faction acts.

### Breach conditions (all must be true):
- Faction took an action other than `committed_action` this cycle
- Their action was not cancelled by a Block (external interference is not breach)
- The committed action was executable this cycle (a valid target existed)

### Grace (suspended):
If the committed action cannot be executed — no valid project to build, domain at capacity — the deal becomes `suspended` for that cycle. If the condition clears, the deal resumes `active`. Three consecutive suspended cycles → deal expires as `fulfilled`, no penalty to either side.

### On breach:
- `deal.status → broken_by_faction`
- Mayor-side terms revoked immediately
- Mayor reputation with that faction: −5
- Faction loses the benefit but receives no further penalty
- Logged to narrative as a notable event

---

## Interaction with Behavior Engine

When `faction.committed_action` is set, the behavior engine skips weight calculation entirely and returns the committed action and target directly.

If `committed_action` is set but no valid target exists, the faction takes their next-best autonomous action for that cycle and the deal enters `suspended`.

`committed_abstain` is checked after weight calculation: if the selected action would target the forbidden faction, the behavior engine re-selects from the remaining candidates.

---

## Data Model Reference

See `../reference/data-models.md` — `Deal`, `DealTerm`, Faction `committed_action` / `committed_target` / `committed_deal_id` / `committed_abstain_action` / `committed_abstain_target`.
