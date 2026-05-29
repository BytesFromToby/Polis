# LLM System Specification

**Version:** v1
**Date:** 2026-05-20

The LLM system has three layers that sit between the game engine and any AI model provider. The rest of the codebase interacts only with the translation layer — it never calls an LLM client directly. The game runs fully without an LLM configured (stub mode).

---

## Architecture Overview

```
Engine models / DB
      │
      ▼
Translation Layer          ← prompt builder + response parser
  (llm/translation.py)
      │
      ▼
LLM Client                 ← provider abstraction
  (llm/client.py)
      │
      ▼
Provider                   ← Anthropic SDK | OpenAI-compat SDK | Stub
```

The translation layer knows about the game. The client layer knows about providers. Neither knows about the other's internals.

---

## Layer 1 — LLM Client

### Config

```python
@dataclass
class LLMConfig:
    provider:    str    # "anthropic" | "openai_compat"
    model:       str    # "claude-sonnet-4-6", "gpt-4o", "llama3.2", etc.
    api_key:     str    # empty string for local models
    base_url:    str    # custom endpoint; required for openai_compat
    temperature: float  # 0.0–1.0; default 0.7
    max_tokens:  int    # default 500 — audience responses are short
    timeout:     int    # seconds; default 30; local models may need more
```

### Config Loading (priority order)

1. `city.llm_config_json` — per-city override stored in the database
2. Environment variables: `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_TEMPERATURE`, `LLM_MAX_TOKENS`, `LLM_TIMEOUT`
3. Stub fallback — no LLM call made; canned response returned

A city without `llm_config_json` uses server-level env vars. A server without env vars uses the stub. The GM sets the city config through the city settings UI.

### Providers

**Anthropic** (`provider: "anthropic"`):
- Uses `anthropic` Python SDK
- `api_key` required
- `base_url` ignored

**OpenAI-compatible** (`provider: "openai_compat"`):
- Uses `openai` Python SDK with `base_url` override
- Covers: OpenAI, Ollama (`http://localhost:11434/v1`), LM Studio, Jan, and most third-party APIs
- `api_key` = `"ollama"` or similar placeholder for local models that require a non-empty key

### Interface

```python
class LLMClient:
    def __init__(self, config: LLMConfig): ...

    def complete(self, system: str, messages: list[dict]) -> str:
        """
        Send a conversation and return the assistant's text response.
        messages: [{"role": "user"|"assistant", "content": str}, ...]
        Raises LLMError on failure.
        """
```

### Stub Client

```python
class StubLLMClient:
    def complete(self, system: str, messages: list[dict]) -> str:
        # Returns a valid but minimal response for each audience step.
        # Step 1 (no prior messages): opening scene-setting text
        # Step 3 (one prior exchange): neutral counter or holding position
        # Step 5 (two prior exchanges): rejection with valid <deal> block
        ...
```

The stub always produces parseable output. It is used in tests and when no LLM is configured.

### Errors

| Exception | When |
|---|---|
| `LLMError` | Base; provider call failed or returned empty |
| `LLMTimeoutError` | Request exceeded `config.timeout` |
| `LLMParseError` | Raised by translation layer, not client |

On any error during an audience: the audience ends gracefully with no deal. The AP cost is not refunded — the meeting happened, it just went nowhere. The failure is logged.

---

## Layer 2 — Translation Layer

Two modules: `prompt_builder.py` and `response_parser.py`.

### Prompt Builder

Translates engine model data into a natural-language system prompt. Called once per audience; the same prompt is sent on all three LLM calls with conversation history appended.

**Inputs:** `faction`, `run_id`, `mayor`, `db_session`, `city`

**Output:** `str` — the full system prompt

#### Trait Translation

Trait labels are mapped to personality sentences. Relational traits include the target name.

```python
TRAIT_SENTENCES = {
    "aggressive":   "You push hard for advantage and do not back down easily.",
    "defensive":    "You protect what you have before seeking more.",
    "industrious":  "You build and invest — conflict is a distraction from growth.",
    "destructive":  "You would rather tear down a rival than build yourself up.",
    "conservative": "You prefer stability and proven methods over risk.",
    "ambitious":    "You are always looking for the next opening.",
    "distrusts":    "You distrust {target} — their motives have disappointed you before.",
    "angry at":     "You are angry at {target} — they wronged you and you have not forgotten.",
    "trusts":       "You trust {target} — you have found them reliable.",
    "allied with":  "You consider {target} an ally — you would rather see them succeed than fail.",
}
```

Intensity multipliers adjust the sentence prefix:
- `slight` → "You are mildly..."
- `moderate` → sentence as-is
- `strong` → "You strongly..."
- `very` → "You are deeply... and this shapes much of how you act."

#### State Narrative

```python
HEALTH_NARRATIVE = {
    (75, 100): "Your organisation is strong and functioning well.",
    (50, 74):  "Your organisation is in reasonable shape but showing strain.",
    (25, 49):  "Your organisation is struggling — resources are stretched thin.",
    (1,  24):  "Your organisation is in crisis. You are fighting to survive.",
}

ENTRENCH_NARRATIVE = {
    (75, 100): "deeply rooted and institutionally secure",
    (50, 74):  "reasonably entrenched but not unassailable",
    (25, 49):  "your grip is weakening — others sense an opportunity",
    (1,  24):  "your organisational hold is precarious",
}

RATING_NARRATIVE = {
    (4, 5): "dominant",
    (3, 4): "significant",
    (2, 3): "established",
    (1, 2): "modest",
}
```

#### Recent Events (last 5 cycles)

Query `narrative_log` for the 5 most recent cycle rows for this `run_id`. Parse `events_json` for each cycle, filter to events where `actor_id` or `target_id` matches `faction.id`. Format as plain-English bullet points with cycle numbers. Cap at 8 events total to stay concise.

#### Memory Notes

Query `faction_memory` for this `(run_id, faction_id)`, ordered by `cycle` ascending. Format:
- `is_summary = True` → *"older interactions summary: [note]"*
- `is_summary = False` → *"[note]"*

#### Valid Terms (plain English)

Each `DealTerm` type has a plain-language template. Resource constraints are injected as hard facts:

```
Mayor can offer:
- Tax exemption for 1–10 cycles  [OR: "Tax exemption is not available — 
  one is already active in {domain}"]
- Public endorsement (immediate, one-time)
- Budget allocation to {domain} for 1–5 cycles

You can commit to:
- Taking a specific action (BuildProject, Protect, Grow) every turn for 
  1–10 cycles [target optional]
- Refraining from Harm or Steal against a named faction for 1–10 cycles
```

#### City Setting / Tone

> **Superseded (2026-05-29) by `player-identity_spec.md`.** The multi-theme `SETTING_TONE`
> dict described below is removed. Polis has one canonical theme (`reference/theming.md`),
> so the prompt always opens with the canonical Greek **situation briefing** from
> `reference/theming.md`, with the city name, player name, and player title substituted in.
> The historical description is kept below for context only.

~~`city.setting` and `city.description` are injected as a preamble paragraph before the character block. A DnD city gets a different register than a modern political sim. The prompt builder reads the setting string and selects an appropriate tone note:~~

```python
# REMOVED — replaced by the single canonical briefing (see player-identity_spec.md).
SETTING_TONE = {
    "DnD":    "This is a fantasy city of guilds, coin, and power. Speak accordingly.",
    "modern": "This is a contemporary city of politics, media, and institutions.",
    # fallback: no tone note injected
}
```

#### Full Prompt Structure

```
[City tone note — from setting]

You are [Leader Name], leader of [Faction Name].

[Faction Name] is a [domain] organisation. [city.description — 1 sentence if set]

Your character:
[Trait sentences, one per line]

Your relationship with the Mayor: [reputation label] ([score])

Your organisation right now:
[Health narrative]. Your influence is [rating narrative] (rating [X.X], floor [N]).
Organisationally you are [entrench narrative] ([X]/100).

Recent events (last 5 cycles):
[Bullet list from narrative_log]

What you remember:
[Memory notes, one per line]

What you can commit to in a deal:
[Valid faction terms]

What the Mayor can offer you:
[Valid mayor terms with constraints]

Speak in character throughout. Keep responses to 3–4 sentences — measured,
not verbose. On your third and final response only, after your closing words,
output a <deal> block with this exact JSON structure:

<deal>
{
  "accepted": true | false,
  "mayor_terms": [...],
  "faction_terms": [...],
  "rep_cost_if_broken_by_mayor": <int 10–35>,
  "memory_note": "<10 words or fewer — what you will remember about this meeting>",
  "reasoning": "<one sentence, out of character>"
}
</deal>

If no deal is reached, set "accepted": false and leave term arrays empty.
memory_note must always be present — even on rejection.
```

---

### Response Parser

Parses the LLM's step 5 conclusion output.

**Input:** raw response string from `LLMClient.complete()`

**Output:** `ParsedAudienceResponse(narrative: str, deal: Deal | None, memory_note: str)`

#### Extraction

1. Split on `<deal>` and `</deal>` tags
2. `narrative` = everything before `<deal>` (stripped)
3. `json_block` = content between tags
4. If tags not found → `deal = None`, full response text used as narrative

#### Validation

```python
VALID_MAYOR_TERM_TYPES = {"tax_exemption", "endorsement", "budget_allocation"}
VALID_FACTION_TERM_TYPES = {"committed_action", "committed_abstain"}
VALID_ACTIONS = {"BuildProject", "Protect", "Grow", "Harm", "Steal", "Block"}
DURATION_RANGE = range(1, 11)
```

- Missing required fields → term dropped
- Invalid `type` → term dropped
- Duration out of range → clamped to 1–10
- `committed_action` with invalid `action` → term dropped
- `committed_action` target not a valid faction/project id → target cleared (action still valid)
- `rep_cost_if_broken_by_mayor` out of 10–35 → clamped
- `memory_note` over 10 words → truncated to 10 words
- `memory_note` missing → use `"meeting held, no note recorded"`

#### Resource Constraint Check

After validation, cross-check mayor terms against current state:
- `tax_exemption`: fail if domain already has an active exemption → term dropped, deal treated as rejected if faction_terms are now unmatched

If the deal JSON parses but terms are inconsistent (e.g., faction committed to something impossible), the audience ends with no deal. The narrative text is still shown.

#### Raises

`LLMParseError` is not raised — parse failures are handled silently and result in `deal = None`. Only truly unrecoverable errors (malformed UTF-8, etc.) propagate.

---

## Layer 3 — Faction Memory

### Note Generation

**From audiences** — the `memory_note` field in the `<deal>` JSON block. Always present (even on rejection). Written by the LLM in ≤10 words from the faction's perspective. Stored with `type="audience"`.

**From engine events** — generated by the engine at the time of the event. Stored with `type="event"`.

| Trigger | Note template |
|---|---|
| Decisive harm received | `"[faction_name] dealt decisive harm, cycle [N]"` |
| Decisive harm dealt | `"dealt decisive harm to [faction_name], cycle [N]"` |
| Deal made | `"deal made with mayor, [action] for [N] cycles"` |
| Deal broken by mayor | `"mayor broke deal, cycle [N]"` |
| Deal broken by faction | `"breached deal with mayor, cycle [N]"` |
| Leader changed | `"new leader [name], cycle [N]"` |
| Project completed | `"[project_name] completed, cycle [N]"` |

### Compression

**Trigger:** before inserting a note that would create a 9th row for `(run_id, faction_id)`

**Process:**
1. Fetch the 5 oldest notes for `(run_id, faction_id)` ordered by `cycle` ASC
2. Call `LLMClient.complete()` with a minimal prompt:
   > *"Summarise these 5 notes in 10 words or fewer from [Faction Name]'s perspective. Output only the summary, nothing else."*
   > *Notes: [note 1] / [note 2] / [note 3] / [note 4] / [note 5]*
3. Parse response — take first 10 words
4. Delete the 5 oldest rows
5. Insert one new row: `is_summary=True, type="summary", note=compressed_text, cycle=<oldest_cycle_of_the_5>`
6. Insert the new note normally

**Result:** row count goes from 8 → 4 (summary + 3 remaining recent + 1 new)

**Stub behaviour:** compression using `StubLLMClient` produces `"past events summarised"` — valid, short, uninteresting. Functional for tests.

---

## Audience Integration

Full call sequence for a complete audience:

```
Mayor spends 1 AP → cooldown set (10 cycles)
        │
        ▼
PromptBuilder.build(faction, run_id, mayor, db, city)
        │  → system_str
        ▼
LLMClient.complete(system_str, [])
        │  → Call 1: opening text
        ▼
[Player reads opening, types prompt_1]
        │
        ▼
LLMClient.complete(system_str, [opening, prompt_1])
        │  → Call 2: faction response / counter
        ▼
[Player reads response, types prompt_2]
        │
        ▼
LLMClient.complete(system_str, [opening, prompt_1, response, prompt_2])
        │  → Call 3: conclusion text + <deal> block
        ▼
ResponseParser.parse(conclusion)
        │  → (narrative, deal_or_none, memory_note)
        ▼
if deal:
    deals table ← insert Deal row
    faction.committed_action / committed_abstain ← set
    mayor terms applied (exemption, endorsement, etc.)

MemoryWriter.write(run_id, faction_id, memory_note, type="audience", cycle)
    → compression if count would reach 9

narrative shown to player
```

On `LLMError` at any step: audience ends, no deal, narrative shows
*"The meeting concluded without agreement."*

---

## Future Hooks (not specced)

**Crisis decision** — when a faction crosses a crisis threshold, an LLM call selects their next action. Uses the same client and a simplified prompt (no deal terms, no memory write). Placeholder: `llm/crisis.py`.

**Demo mode** — all faction turns routed through LLM. Requires async batching. Placeholder: `llm/demo.py`.

Both use `LLMClient` and `PromptBuilder` sub-components without the full audience flow.

---

## File Structure

```
engine/llm/
    __init__.py
    client.py          ← LLMConfig, LLMClient, StubLLMClient, LLMError
    prompt_builder.py  ← PromptBuilder, TRAIT_SENTENCES, HEALTH_NARRATIVE, etc.
    response_parser.py ← ResponseParser, ParsedAudienceResponse
    memory.py          ← MemoryWriter (note creation, compression trigger)
    audiences.py       ← full audience flow, wires the three layers together
```
