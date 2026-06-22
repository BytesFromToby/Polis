# Audience Specification

**Version:** v5.2
**Date:** 2026-06-07
**Updated:** 2026-06-12 — **Toil committable** (chain-role factions only) + **Public needs line** in the system prompt (public-needs / barley-run).
**Updated:** 2026-06-13 — consolidated three former satellite specs into this one (audience is one subsystem, one spec): **BuildProject buildable info**, **Deal card** transcript presentation, **Training log** capture. The originals are archived for their full problem-statement context.

The Mayor can request a formal audience with a faction leader. Audiences are the only way to create binding deals. The faction leader is driven by an LLM that opens the scene, negotiates through two player exchanges, and delivers a final decision.

> **v5 changes:** an audience now **requires an active AI**. Previously a run with no LLM
> profile silently fell back to stub mode for live play; now both the UI and the API refuse
> to start an audience unless the run has a valid active AI (see **Active-AI Requirement**).
> Stub mode (`LLMConfig(provider="stub")`) remains for automated tests and the non-audience
> sim — only the player-facing audience entry points are gated.

> **v4 changes:** the deal-term set is clarified so the LLM negotiates coherently — each term
> now carries a plain "what it does" line and explicit per-action targeting (see **Valid Deal
> Terms**). The dead `budget_allocation` Mayor term is removed (it was never applied). `Grow`
> and `Protect` are untargeted; only `BuildProject` (a project) and `committed_abstain` (a
> faction) take a target.

> **v3 changes:** a deal accepted by the faction is no longer created automatically — the
> Mayor must confirm it (Accept/Decline) before it is sealed (see **Mayor Confirmation**).
> Each step now also returns a **debug payload** (the prompt sent and the raw response) for
> always-on inspection (see **Debug Instrumentation**), and the UI shows a per-step
> **deal-status label** (see **Deal-Status Display**).

---

## Overview

An audience is a structured five-step conversation:

1. **AI sets the scene** — faction leader speaks first, establishing mood and position
2. **Player prompts** — the mayor speaks (freeform)
3. **AI responds / counters** — faction leader reacts to the mayor's words
4. **Player prompts again** — the mayor has one final input
5. **AI concludes** — faction leader delivers their decision and, if accepting, the agreed terms

A completed audience either produces a `Deal` or produces nothing. There is no partial agreement. When the faction accepts, the Mayor still has the final say — the deal is created only after the Mayor confirms (see **Mayor Confirmation**).

---

## Triggering an Audience

**Cost:** 1 action point  
**Cooldown:** 10 cycles per faction (tracked in `mayor.cooldowns`)  
**Restriction:** Cannot request an audience with a faction that has an active deal — renegotiation is not available until the current deal expires, is fulfilled, or is broken.

The player selects a faction to meet. No terms are pre-selected. The negotiation emerges from the conversation.

---

## Active-AI Requirement

An audience requires an **active AI** on the current run. "Active AI is set" means the run's
`llm_profile_id` is set **and** resolves to an existing `LLMProfile`. A live connection test is
**not** required — selection of a valid saved profile is sufficient. The active AI is chosen in
the in-game **Settings** panel (`LLMSettings`, "Active city AI" → `sim.setLlmProfile`); the run's
`llm_profile_id` is exposed to the client by `sim status` (`SimStatusResponse.llm_profile_id`).

**UI gate.** The two audience entry points — the centre **Request Audience** button and a faction
card's **Audience ▸** button — check whether an active AI is set before starting. If none is set,
they open a small blocking **warning dialog** ("No active AI is set for this game. Set an AI to
hold audiences.") with an **Open Settings** control (opens the `LLMSettings` panel) and a **Close**
control. No audience begins, no AP is spent, and the faction picker / `AudienceModal` does not open.

**API gate.** `POST /mayor/audience/begin` independently enforces the same rule: if the run's
`llm_profile_id` is unset, or is set but does not resolve to an existing profile, the request is
rejected with **HTTP 400** and a message naming the missing active AI, **before** any action point
is spent. The previous silent stub fallback for live audiences is removed. The engine layer
(`begin_audience_step` with an explicit `llm_config`, including `LLMConfig(provider="stub")`)
is unchanged — automated tests drive it directly and are unaffected.

**Done when:**
- `POST /mayor/audience/begin` on a run whose `llm_profile_id` is unset returns HTTP 400 and leaves `mayor.action_points` unchanged (no AP spent)  `[automated]`
- `POST /mayor/audience/begin` on a run whose `llm_profile_id` is set but does not resolve to an existing `LLMProfile` returns HTTP 400 and spends no AP  `[automated]`
- `POST /mayor/audience/begin` on a run with a valid active `llm_profile_id` proceeds normally — spends 1 AP and returns the Step-1 opening  `[automated]`
- With no active AI set, clicking **Request Audience** or a faction's **Audience ▸** opens the warning dialog and does not open the faction picker or `AudienceModal`  `[human-required]`
- The warning dialog shows an **Open Settings** control that opens the `LLMSettings` panel, and a **Close** control that dismisses it  `[human-required]`
- With a valid active AI set, both audience entry points start the audience as before, with no warning  `[human-required]`

---

## Valid Deal Terms

The LLM is told what is mechanically possible **and what each term does**, so it negotiates
coherently and steers toward valid, implementable outcomes. The prompt must explain every term
in plain language and state its targeting — the leader should never, e.g., offer to "Protect
you from House X," because Protect has no target.

### Mayor can offer (one or more per deal):

| Term | What it does | Target | Constraint |
|---|---|---|---|
| `endorsement` | Immediate +10 reputation with the Mayor | — | No constraint |

> **`tax_exemption` is deferred (shelved 2026-06-08).** It had no income effect under
> treasury_spec v3 (income = base + Tax Offices), so it is no longer offered to factions —
> `endorsement` is the only Mayor term in the demo. The parser still accepts a stray
> `tax_exemption` term (dormant); full shelving record in `../archive/tax-exemption-shelve_spec.md`.

### Faction can commit to (one per deal):

Exactly one of the following, repeated every turn for N cycles (N = 1–10):

| Term | What it does | Target |
|---|---|---|
| `committed_action` · `Grow` | The faction invests in its own strength (raises rating/health) | none |
| `committed_action` · `Protect` | The faction defends itself — higher entrenchment and reduced incoming Harm from **all** rivals | none |
| `committed_action` · `BuildProject` | The faction works to build **its own domain's** base project (named in the prompt) | its domain id |
| `committed_action` · `Toil` | The faction works its trade, boosting its supply-chain output each committed cycle (offered **only** to factions with a chain role — see `actions_spec.md`) | none |
| `committed_action` · `Rally` | The faction publicly champions the Mayor each committed cycle, raising the Public's support (the Rally action — see `actions_spec.md`); any faction may be asked for this | none |
| `committed_abstain` | The faction refrains from Harm or Steal against one named faction | a faction |

**Targeting is per-action.** Only `BuildProject` (target = the faction's own domain id) and `committed_abstain`
(target = a faction) take a target. `Grow`, `Protect`, `Toil`, and `Rally` are untargeted; any `target_id`
supplied for them is dropped by the parser.

*Not yet a term:* `committed_abstain` · `Agitate` ("cease turning the people against me") — a planned
follow-up; needs targetless-abstain handling in the behavior engine (see `proposals/faction-influence.md`).

**The Public needs line (public-needs, 2026-06-12).** The audience system prompt's city-state
section includes one line built from the Public's band words and flags
(`public-needs_spec.md`): *"The people are {fed band}{, drunk}{, sickly}, and {happy band}."*
The leader sees the same city the engine does.

> `budget_allocation` was a Mayor term in v3 but was never wired to any effect; it is removed
> as of v4. It is no longer offered, accepted, or documented. A removed or otherwise unknown
> term type appearing in a `<deal>` is **dropped, and the rest of the deal still parses**
> (drop-and-continue) — it never fails an otherwise-valid deal.

**Done when:**
- `budget_allocation` appears in no spec, reference doc, or backend source file  `[automated]`
- The built audience system prompt lists only `endorsement` as a Mayor term (`tax_exemption` deferred — see note above), and gives a plain "what it does" line for each faction action (`Grow`, `Protect`, `BuildProject`, and — for chain-role factions only — `Toil`) and for `committed_abstain`  `[automated]`
- For a faction with no chain role, `Toil` does not appear in the prompt's term list at all  `[automated]`
- The built audience system prompt contains the Public needs line with the current band words (and `drunk`/`sickly` flags only when set)  `[automated]`
- In the prompt's `<deal>` schema, a `target_id` is shown only for `BuildProject` and `committed_abstain` — not for `Grow`, `Protect`, or `Toil`  `[automated]`
- The response parser clears `target_id` on a `committed_action` of `Grow`, `Protect`, `Toil`, or `Rally`, and preserves it for `BuildProject`  `[automated]`
- A `committed_action` of `Rally` parses as a valid faction term and binds the faction to the Rally action for the committed cycles — `tests/test_faction_influence.py`  `[automated]`
- A `<deal>` that offers `budget_allocation` **alongside** a valid Mayor term drops only `budget_allocation` and still seals on the valid term  `[automated]`
- A `<deal>` whose **only** Mayor term is `budget_allocation` yields no deal — it is dropped, leaving the Mayor side empty (one-sided), and `mayor.deals` is unchanged  `[automated]`

### BuildProject — the faction's own buildable (consolidated from build-target-info, 2026-06-13)

A faction can build **only its own domain's** base project. The prompt tells the LLM the one
project it can build (name + a one-line effect) and the `<deal>` BuildProject `target_id` is the
faction's **domain id** (matching `base_stacks` keys / the engine), so the agreed deal terms match
what is actually built. The effect text is single-sourced: `base_project_description(domain_id)`
parallels `BASE_PROJECT_NAMES` in `engine/projects/processing.py` (defaults to a generic
"raises {Domain}'s capacity…" sentence), so prompt/UI/docs cannot drift.

**Done when:**
- `base_project_description(domain_id)` returns a non-empty one-line string for every domain in `BASE_PROJECT_NAMES`, and a sensible default for an unknown domain  `[automated]`
- The built prompt for a faction contains its own domain's base-project name (e.g. a `harbor` faction's prompt contains "Docks") and that project's description text  `[automated]`
- The built prompt's BuildProject `<deal>` target instruction references the faction's domain id and contains no free-text "project id" placeholder and no `dock_expansion`  `[automated]`
- A faction's prompt does not enumerate other domains' base projects (only its own buildable appears)  `[automated]`

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
    { "type": "endorsement" }
  ],
  "faction_terms": [
    { "type": "committed_action", "action": "BuildProject", "target_id": "harbor", "duration": 4 }
  ],
  "rep_cost_if_broken_by_mayor": 25,
  "memory_note": "agreed tax break for dock construction support",
  "reasoning": "<one sentence, out of character>"
}
</deal>
```

The `<deal>` block is parsed by the response parser. The in-character text is shown to the player. Invalid terms are dropped silently — if remaining terms are empty on either side, the deal is treated as rejected.

**Conclusion no longer commits.** Step 5 parses the faction's decision and proposed terms but does **not** create the `Deal`, apply mayor/faction terms, or write the memory note when the faction accepts — those are deferred to **Mayor Confirmation**. The parsed result is held in the audience state. `memory_note` (≤10 words) is always produced by the LLM; it is written to `faction_memory` at the moment the audience is finalised (see Mayor Confirmation), reflecting the final outcome.

See `llm-system_spec.md` for the full system prompt structure, trait translation, response parser, and memory compression logic.

---

## Mayor Confirmation

After Step 5, control returns to the Mayor before any binding deal exists.

- **Faction declines** (`accepted: false`): the audience is finalised immediately — no
  deal is created, no terms apply, the memory note is written ("no deal reached" or the
  LLM's note), and the per-faction cooldown is set. The Mayor is shown the outcome; there
  is nothing to confirm.
- **Faction accepts** (`accepted: true`): the deal is **not** yet created. The Mayor is
  shown the proposed terms (mayor-side and faction-side) and chooses:
  - **Accept** — the `Deal` is created, mayor terms applied, faction `committed_*` fields
    set, memory note written ("deal reached" / the LLM note), cooldown set.
  - **Decline** — no deal is created, no terms apply, a memory note is written recording
    that the Mayor declined the agreed terms, and the cooldown is set.

The action point for the audience is spent at the start (Step 1) regardless of outcome —
confirming or declining costs no additional AP. The cooldown is set when the audience is
finalised, in every branch.

**Flow shape (backend):**
- `conclude` runs Step 5, parses, and — only on faction-decline — finalises and clears the
  audience state. On faction-accept it stores the parsed result and returns
  `accepted: true` with the proposed terms, **without** creating the deal.
- A new `finalize` step takes the Mayor's decision (`mayor_accepts: bool`). It is only
  required when the faction accepted. It creates-or-discards the deal accordingly, writes
  the memory note, sets the cooldown, and clears the audience state.

**Done when:**
- When the faction accepts, `conclude` creates no `Deal` and applies no mayor/faction terms — `mayor.deals` is unchanged after conclude  `[automated]`
- After a faction-accept conclude, `finalize` with `mayor_accepts: true` creates exactly one `Deal`, applies the mayor terms, and sets the faction's `committed_*` fields  `[automated]`
- After a faction-accept conclude, `finalize` with `mayor_accepts: false` creates no `Deal` and applies no terms, but still sets the faction cooldown  `[automated]`
- When the faction declines, the audience finalises without a `finalize` call: no deal, memory note written, cooldown set  `[automated]`
- A memory note is written for every finalised audience (accept-confirmed, accept-declined, faction-declined)  `[automated]`
- The audience UI shows Accept/Decline controls only when the faction accepted, and shows a terminal outcome (no confirm controls) when the faction declined  `[human-required]`

---

## Deal-Status Display

The UI shows a deal-status label beneath each faction speech so the player can read where
the negotiation stands. The label is **computed on the client from the current step** — it
does not change the LLM contract and the LLM does not emit interim structured terms.

- After Step 1 (faction opens): "no terms on the table yet"
- After Step 3 (faction counters): "negotiating"
- After Step 5 (faction concludes): the verdict — accepted (with the proposed terms) or
  declined; once the Mayor confirms, the sealed/declined final state.

Exact wording is a UI choice; the semantics above are the contract.

**Done when:**
- A status label appears under each faction speech, reflecting opening → negotiating → verdict as the conversation advances  `[human-required]`
- The status after Step 5 distinguishes faction-accepted (showing the proposed terms) from faction-declined  `[human-required]`

---

## Transcript Presentation — Deal Card (consolidated from audience-deal-card, 2026-06-13)

Faction LLMs sometimes emit the `<deal>` JSON block early (step 1 or 3). Each faction turn in
`AudienceModal.vue` is split on `<deal>`/`</deal>`: the prose before the block is shown in the
bubble; the JSON between the tags is parsed and, when it parses, rendered as a compact **"Proposed
deal" card** under that bubble (styled with the existing `.confirm-box` / `.terms-grid` classes) —
so raw JSON never leaks into a dialogue bubble. Frontend-only; the parser, schema, and negotiation
flow are unchanged. Card fields: **You give** (`mayor_terms`), **They give** (`faction_terms`),
**Break penalty** (`rep_cost_if_broken_by_mayor`), **Memory note**, and a muted **Why** (`reasoning`).

**Done when:**
- `cd frontend && npm run build` succeeds with no template/script errors  `[automated]`
- No faction transcript bubble displays a raw `<deal>`/`</deal>` tag or JSON braces — bubbles show only in-character prose  `[human-required]`
- When a faction turn carried a deal, a "Proposed deal" card renders under that bubble, visually consistent with the Confirm-the-deal box, showing You give / They give / break-penalty sentence / memory note / muted "Why:" line  `[human-required]`
- A faction turn with **no** deal block renders as prose only (no card); a malformed `<deal>` is stripped and produces no card and no render error  `[human-required]`

---

## Debug Instrumentation

Every audience step returns a **debug payload** alongside its narrative, so the exact LLM
interaction can be inspected. The payload is always returned (no flag) and surfaced in the
UI by two always-present, collapsed-by-default controls at the bottom of the audience:

- **Show JSON** — reveals the full request sent to the LLM for each interaction: the
  system prompt and the `messages` array.
- **Debug** — reveals every LLM call across the whole audience: for each, the prompt sent
  (system + messages) and the raw response text returned (before parsing).

The request payload (`system`, `messages`) and the raw response already exist server-side
in the audience state; this exposes them per step to the client. The Step 5 raw response
is the unparsed text (the `<deal>` block intact), distinct from the in-character narrative
shown in the transcript.

**Done when:**
- Each audience step response (`begin`, `reply`, `conclude`) includes a debug payload containing the request sent to the LLM (system prompt + messages) and the raw response text for that step  `[automated]`
- The Step 5 debug response is the raw unparsed LLM text including the `<deal>` block, distinct from the displayed narrative  `[automated]`
- The audience UI shows "Show JSON" and "Debug" controls at the bottom, collapsed by default, expanding to the request JSON and the full per-call request+response history respectively  `[human-required]`

---

## Training Log (consolidated from audience-training-log, 2026-06-13)

A structured JSONL log captures each completed **live-AI** audience as one record, to build a
dataset for later fine-tuning a small LM that plays faction leaders. This is **capture only** (no
training/export pipeline). The writer (`engine/llm/audience_log.py`) is invoked when the audience
fully resolves: in `audience_conclude` on a faction **decline**, and in `audience_finalize` on a
faction **accept**. It appends one line to `backend/logs/audiences.jsonl`, reading from
`session.audience_state`. **Live-AI only** — nothing is written when `llm_config.provider == "stub"`
(so the test suite and stub play write nothing); no API key/secret is ever recorded.

Record (one JSON object per line): `schema_version`, `timestamp` (ISO-8601 UTC), `run_id`, `cycle`,
`provider`, `model`, `faction` (id/name/domain_primary/traits), `system_prompt`, `turns` (faction
steps 1/3/5 + the Mayor's two freeform inputs, in conversation order), `step5_raw` (unparsed step-5
text with the `<deal>` block), `parsed_deal`, and `outcome` (`faction_declined` |
`accepted_confirmed` | `accepted_mayor_declined`).

**Done when:**
- A completed live audience (real profile; faction accepts; Mayor confirms) appends exactly one new line to `backend/logs/audiences.jsonl`, parsing as JSON with all required top-level keys (`schema_version`, `timestamp`, `run_id`, `cycle`, `provider`, `model`, `faction`, `system_prompt`, `turns`, `step5_raw`, `parsed_deal`, `outcome`)  `[automated]`
- A stub-mode audience (`llm_config.provider == "stub"`) writes **no** record — the file line count is unchanged across a full stub audience  `[automated]`
- A faction-declined live audience writes its record at the `conclude` step (no `finalize` needed) with `outcome == "faction_declined"`  `[automated]`
- A faction-accepted live audience confirmed by the Mayor records `outcome == "accepted_confirmed"`; accepted-but-Mayor-declined records `outcome == "accepted_mayor_declined"`  `[automated]`
- The `turns` array contains the faction's step-1/3/5 text **and** the Mayor's two freeform inputs, in conversation order (faction, mayor, faction, mayor, faction)  `[automated]`
- The record includes `step5_raw` (the unparsed step-5 text containing the `<deal>` block), distinct from `parsed_deal`  `[automated]`
- The record includes `provider` and `model`, and contains **no** API key / secret field anywhere in the line  `[automated]`
- The writer appends to `backend/logs/audiences.jsonl` only — `narrative.log` and `system.log` are unaffected  `[automated]`

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
- All mayor-side terms revoked immediately (exemption removed from `mayor.exemptions`)
- Faction's committed terms released — `faction.committed_action` cleared, faction resumes autonomous behavior
- Faction gains `angry at mayor` relational trait at **moderate** intensity — persists until natural decay, biases their actions toward Harm targeting mayor interests
- Other factions in the same domain: −3 reputation with mayor (word travels)

A mayor that repeatedly breaks deals accelerates toward hostile factions and the removal spiral.

---

## Faction Breach

Checked each cycle after the faction acts.

### Breach conditions (all must be true):
- Faction took an action other than `committed_action` this cycle
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
