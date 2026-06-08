# Inspection — Audience Training Log (Final Sign-Off)

- **Feature:** Audience Training Log
- **Spec:** Planning/specs/audience-training-log_spec.md (8 Done-when items, all [automated])
- **Blueprint:** Planning/blueprints/audience-training-log_BP.md
- **Inspected:** 2026-06-08
- **Inspector:** fresh-eyes (did not build)

## Test runs

- `cd backend && py -m pytest tests/test_audience_training_log.py -v` → **8 passed in 0.52s**
- `cd backend && py -m pytest tests/ -q` → **366 passed in 1.06s**

## Done-when verdicts

### 1. Completed live audience appends exactly one new line that parses as JSON with all required top-level keys — PASS
Test: `test_live_audience_writes_one_wellformed_record` (tests/test_audience_training_log.py:43).
Asserts `log_audience(...) is True`, `len(records) == 1`, and presence of every required key
(`schema_version, timestamp, run_id, cycle, provider, model, faction, system_prompt, turns, step5_raw, parsed_deal, outcome`).
Implementation: audience_log.py:62-80 builds exactly those keys.

### 2. Stub-mode audience writes no record (line count unchanged) — PASS
Test: `test_stub_audience_writes_nothing` (line 56). `provider="stub"` → returns False and file does not exist.
Implementation: live-AI gate at audience_log.py:59 (`provider == "stub"` → return False, no write).

### 3. Faction-declined live audience writes its record at conclude with outcome == "faction_declined" — PASS
Test: `test_conclude_logs_faction_declined` (line 147) — drives `audience_conclude` with a finalized
declining result; spy confirms `log_audience` called once with `outcome="faction_declined"`.
Implementation: mayor.py:505-508 — call is inside `if result.finalized:` and BEFORE `session.audience_state = None`.

### 4. accepted_confirmed vs accepted_mayor_declined at finalize — PASS
Test: `test_finalize_logs_accepted_outcomes` (line 160) — `mayor_accepts=True` → `accepted_confirmed`;
`mayor_accepts=False` → `accepted_mayor_declined`.
Implementation: mayor.py:559-560 — outcome ternary, BEFORE `session.audience_state = None` (mayor.py:561).
Round-trip of all three literal outcome values also covered by `test_outcome_value_round_trips` (line 94).

### 5. turns array has faction step-1/3/5 + the Mayor's two inputs in conversation order — PASS
Test: `test_turns_order_and_content` (line 62). Asserts order
`[(faction,1),(mayor,2),(faction,3),(mayor,4),(faction,5)]` and the five text values.
Implementation: `_build_turns` (audience_log.py:30-39); mayor/2 = first user message via `_first_user_text`.

### 6. step5_raw present (contains `<deal>`) and distinct from parsed_deal — PASS
Test: `test_step5_raw_distinct_from_parsed_deal` (line 75). Asserts `<deal>` in `step5_raw` and
`step5_raw != json.dumps(parsed_deal)`.
Implementation: `step5_raw` from `state["step5_raw"]` (audience_log.py:77); `parsed_deal` separately via `_parsed_deal` (42-52).

### 7. Record includes provider + model and no API key / secret anywhere in the line — PASS
Test: `test_provider_model_present_no_secrets` (line 84). Asserts `provider`/`model` set and that
`api_key`, `encrypted_api_key`, `base_url` do not appear in the serialized line.
Implementation: only `.provider`/`.model` are read via `getattr` (audience_log.py:67-68); the LLMConfig
object (which does carry `api_key`/`base_url`, client.py:38-39) is never serialized. No leak path.

### 8. Writer appends to backend/logs/audiences.jsonl only — narrative.log / system.log unaffected — PASS
Tests use `tmp_path` paths; the only writer is `log_audience`'s single `open(target, "a")` (audience_log.py:84).
`DEFAULT_LOG_PATH` (audience_log.py:17-19) resolves to backend/logs/audiences.jsonl; call sites pass no path arg.
No code path in audience_log.py touches narrative.log or system.log. Full suite (366 passed) confirms no regression.

## Spot-check notes

- Live-AI gate returns False when `provider == "stub"` (also when `cfg is None`). Correct. (audience_log.py:59)
- `log_audience` imported at mayor.py:36; called in both routes before state is cleared. Correct.
- `_term_to_dict` imported locally inside `_parsed_deal` to avoid import cycle (matches blueprint Stuck-If guidance).
- `DEFAULT_LOG_PATH` uses `os.path.normpath` of the `__file__`-relative join — points at backend/logs/audiences.jsonl.

## Result

**8 PASS · 0 FAIL** — no gaps. Every [automated] Done-when item is encoded by a committed, passing test.

Signed: inspector — 2026-06-08
