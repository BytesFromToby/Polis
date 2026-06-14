# Spec: Audience Training Log

> **ARCHIVED 2026-06-13 — consolidated into `../specs/audience_spec.md`** ("Training Log"), which
> carries the live rule + Done-when items. Kept here for full context. Non-authoritative.

A separate, structured JSONL log that captures each completed **live-AI** audience as one
record — the system prompt, the full negotiation transcript (including the Mayor's freeform
inputs), the raw LLM responses, the parsed deal, and the final outcome. It exists to build a
dataset for later fine-tuning a small LM that can play faction leaders, packaged with the
program. This feature builds the **capture** only; the training pipeline is out of scope.

## Scope
- Does: append one JSON line per completed audience to `backend/logs/audiences.jsonl`, capturing
  prompt, turns, raw responses, parsed deal, outcome, and model metadata — for audiences run
  against a real LLM profile.
- Does NOT: log stub-mode or test audiences; log abandoned/incomplete or LLM-errored audiences;
  build any training/export/fine-tuning pipeline; store API keys or secrets; change the audience
  flow, the LLM contract, or the existing narrative/system logs.

## Feature: Audience training log
A writer records a completed audience as one JSONL line. It is invoked from the audience flow at
the point the audience fully resolves: in `audience_conclude` when the faction **declines** (that
path finalizes the audience), and in `audience_finalize` when the faction **accepted** (after the
Mayor's accept/decline). The data is read from `session.audience_state` (`system`, `messages`,
`step5_raw`, `pending_parsed`, `llm_config`, `faction_id`) plus the faction, `run_id`, and `cycle`.

Capture is **live-AI only**: a record is written only when the audience's `llm_config.provider`
is not `"stub"`. Stub audiences (and the test suite, which runs stub) write nothing.

**Record shape** (one JSON object per line):
```
{
  "schema_version": 1,
  "timestamp": "<ISO-8601 UTC>",
  "run_id": "<run id>",
  "cycle": <int>,
  "provider": "<anthropic|openai_compat|...>",
  "model": "<model id>",
  "faction": { "id": "...", "name": "...", "domain_primary": "...", "traits": ["...", ...] },
  "system_prompt": "<full system prompt>",
  "turns": [
    { "role": "faction", "step": 1, "text": "<step-1 opening>" },
    { "role": "mayor",   "step": 2, "text": "<mayor input 1>" },
    { "role": "faction", "step": 3, "text": "<step-3 response>" },
    { "role": "mayor",   "step": 4, "text": "<mayor input 2>" },
    { "role": "faction", "step": 5, "text": "<step-5 narrative>" }
  ],
  "step5_raw": "<raw step-5 LLM text including the <deal> block>",
  "parsed_deal": { "accepted": <bool>, "mayor_terms": [...], "faction_terms": [...], "memory_note": "..." },
  "outcome": "faction_declined" | "accepted_confirmed" | "accepted_mayor_declined"
}
```

- Input: a fully-resolved audience (`session.audience_state`), the faction, `run_id`, `cycle`.
- Output: one appended line in `backend/logs/audiences.jsonl` (file/dir created on first write).

**Done when:**
- A completed live audience (real profile; faction accepts; Mayor confirms) appends exactly one new line to `backend/logs/audiences.jsonl`, and that line parses as JSON with all required top-level keys (`schema_version`, `timestamp`, `run_id`, `cycle`, `provider`, `model`, `faction`, `system_prompt`, `turns`, `step5_raw`, `parsed_deal`, `outcome`)  `[automated]`
- A stub-mode audience (`llm_config.provider == "stub"`) writes **no** record — the file line count is unchanged across a full stub audience  `[automated]`
- A faction-declined live audience writes its record at the `conclude` step (no `finalize` call needed) with `outcome == "faction_declined"`  `[automated]`
- A faction-accepted live audience confirmed by the Mayor records `outcome == "accepted_confirmed"`; accepted-but-Mayor-declined records `outcome == "accepted_mayor_declined"`  `[automated]`
- The `turns` array contains the faction's step-1/3/5 text **and** the Mayor's two freeform inputs, in conversation order (faction, mayor, faction, mayor, faction)  `[automated]`
- The record includes `step5_raw` (the unparsed step-5 text containing the `<deal>` block), distinct from `parsed_deal`  `[automated]`
- The record includes `provider` and `model`, and contains **no** API key / secret field anywhere in the line  `[automated]`
- The writer appends to `backend/logs/audiences.jsonl` only — `narrative.log` and `system.log` are unaffected  `[automated]`
