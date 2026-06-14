# Blueprint: Audience Training Log
Spec: Planning/specs/audience-training-log_spec.md
Date: 2026-06-08

---

## Builder instructions
- Execute steps in order. Do not skip, reorder, or read ahead into the next slice.
- Check off each step when complete: [ ] → [x]
- One step = one logical concern. If a step can't be tested on its own, it's too small — merge it. If it touches more than one concern, split it.
- Deviation: if you do something differently than the step says, note it inline and keep going.
- Stuck: stop immediately. Do not try alternative approaches. Report exactly where and why.
- Test command: `cd backend && py -m pytest tests/ -q`

---

## Slice 1: The writer (engine/llm/audience_log.py)
**Scope:** A standalone `log_audience(...)` builds one record from an audience state dict and appends it as a JSONL line — live-AI only — to a given path; fully testable without the route or network.

### Step 1: Write the log_audience module
**Build:** Create `backend/engine/llm/audience_log.py` with:
- `SCHEMA_VERSION = 1` and `DEFAULT_LOG_PATH` = absolute path to `backend/logs/audiences.jsonl` computed from `__file__` (`os.path.join(os.path.dirname(__file__), "..", "..", "logs", "audiences.jsonl")`).
- `def log_audience(state, faction, run_id, cycle, outcome, path=None) -> bool:` — returns False without writing when `state["llm_config"].provider == "stub"` (live-AI gate). Otherwise builds the record and appends one JSON line (`json.dumps(record) + "\n"`), creating the dir/file if needed; returns True.
- Record fields (per spec): `schema_version`, `timestamp` (`datetime.now(timezone.utc).isoformat()`), `run_id`, `cycle`, `provider`/`model` (from `state["llm_config"].provider/.model`), `faction` `{id,name,domain_primary,traits:[t.trait for t in faction.traits]}`, `system_prompt` (`state["system"]`), `turns` (list — see mapping), `step5_raw` (`state.get("step5_raw","")`), `parsed_deal`, `outcome`.
- Turns mapping (in order): faction/1 = `state["step1_narrative"]`; mayor/2 = first `role=="user"` content in `state["messages"]` (the mayor's opening); faction/3 = `state.get("step3_narrative","")`; mayor/4 = `state.get("mayor_closing","")`; faction/5 = `state["pending_parsed"].narrative`.
- `parsed_deal` from `state["pending_parsed"]`: `{accepted, mayor_terms, faction_terms, memory_note}` — serialize terms with `_term_to_dict` from `engine.llm.audiences` (import locally to avoid cycles).
- Never include any api_key/secret field.
**Test:** `cd backend && py -c "from engine.llm.audience_log import log_audience, SCHEMA_VERSION, DEFAULT_LOG_PATH; print(SCHEMA_VERSION)"`
**Done When:** Module imports; prints `1`.
**Stuck If:** Importing `_term_to_dict` causes a circular import — define a tiny local term-serializer instead and note the deviation.
- [x] Complete

### Step 2: Writer tests (record shape, gate, fields)
**Build:** Create `backend/tests/test_audience_training_log.py`. Build a helper that returns a realistic `state` dict (keys: `system`, `messages` = `[{"role":"assistant","content":"<step1>"},{"role":"user","content":"<mayor1>"},{"role":"assistant","content":"<step3>"}]`, `step1_narrative`, `step3_narrative`, `mayor_closing`, `step5_raw` containing a `<deal>` block, `pending_parsed` (a small stub object/namespace with `.accepted/.narrative/.mayor_terms=[]/.faction_terms=[]/.memory_note`), and `llm_config` (a stub object with `.provider/.model`)). Use a `tmp_path` file. Cover these `[automated]` items by calling `log_audience` directly:
1. Non-stub provider + outcome `accepted_confirmed` → exactly one new line; parses as JSON; has all required top-level keys (`schema_version,timestamp,run_id,cycle,provider,model,faction,system_prompt,turns,step5_raw,parsed_deal,outcome`).
2. provider `"stub"` → returns False and writes no line (file absent or line count unchanged).
3. `turns` has 5 entries in order faction,mayor,faction,mayor,faction with the step-1/3/5 text and the two mayor inputs.
4. `step5_raw` is present and contains `<deal>`, and differs from `parsed_deal`.
5. `provider` and `model` are set; assert no key named `api_key`/`encrypted_api_key`/`base_url` anywhere in the serialized line.
6. Outcome value round-trips: calling with each of `faction_declined`/`accepted_confirmed`/`accepted_mayor_declined` writes that exact `outcome`.
**Test:** `cd backend && py -m pytest tests/test_audience_training_log.py -q`
**Done When:** All pass.
**Stuck If:** The faction-traits access fails — build the fake faction with real `Faction`/`Leader`/`FactionTrait` or a namespace exposing `.traits` of objects with `.trait`.
- [x] Complete

---
⛔ End of Slice 1. Run **inspector** on this slice before continuing.

---

## Final Slice: Wire the call sites + verify
**Scope:** `audience_conclude` logs faction-declines; `audience_finalize` logs accepts with the right outcome; full spec verified.

### Step 1: Call log_audience from conclude + finalize
**Build:** In `backend/api/routes/mayor.py`:
- Import `from engine.llm.audience_log import log_audience`.
- In `audience_conclude`, inside `if result.finalized:` (the faction-declined path), call `log_audience(state, faction, session.run_id, session.world.cycle, outcome="faction_declined")` BEFORE `session.audience_state = None`.
- In `audience_finalize`, before `session.audience_state = None`, call `log_audience(state, faction, session.run_id, session.world.cycle, outcome=("accepted_confirmed" if req.mayor_accepts else "accepted_mayor_declined"))`.
- Use the default log path (no path arg). The live-AI gate inside log_audience handles stub skip, so no extra guard is needed at the call site.
**Test:** `cd backend && py -m pytest tests/ -q`
**Done When:** Full suite green (existing audience tests unaffected — they run stub, so nothing is logged).
**Stuck If:** `state` is cleared before the log call — ensure the call precedes `session.audience_state = None` in both routes.
- [x] Complete

### Step 2: Call-site wiring tests
**Build:** Add to `backend/tests/test_audience_training_log.py` tests that the routes invoke the writer with the correct outcome. Approach (no network): build a `SimSession` (mirror `tests/test_audience_requires_ai.py`) with a hand-built `session.audience_state` whose `llm_config.provider` is non-stub (e.g. `"anthropic"`) and the keys conclude/finalize need; monkeypatch `engine.llm.audiences.LLMClient.complete` (or the client used in `conclude_audience_step`) to return canned step-5 text — a declining `<deal>` for the decline case, an accepting `<deal>` for the accept case — so no network call happens; and monkeypatch `api.routes.mayor.log_audience` with a spy capturing `(outcome,)`. Then:
1. Drive `audience_conclude` with a declining canned response → spy called once with `outcome="faction_declined"`.
2. Drive `audience_finalize` (after a faction-accept state) with `mayor_accepts=True` → spy called with `outcome="accepted_confirmed"`; with `mayor_accepts=False` → `outcome="accepted_mayor_declined"`.
(If hand-building the accept state for finalize is fiddly, set `state["pending_parsed"]` to an accepted parsed object directly — finalize reads `pending_parsed`, not the LLM, except for the memory note.)
**Test:** `cd backend && py -m pytest tests/test_audience_training_log.py -q`
**Done When:** All three wiring tests pass.
**Stuck If:** The LLM client can't be monkeypatched cleanly (wrong import path) — report the exact call chain in `conclude_audience_step`; do not make a real network call.
- [x] Complete

### Final Step: Verify spec Done when items
**Build:** No new code. Confirm all `**Done when:**` items in audience-training-log_spec.md are met.
**Test:** `cd backend && py -m pytest tests/ -q` — the committed tests cover all 8 `[automated]` items. Capture output.
**Done When:** Every `[automated]` criterion passes via its committed test.
**Stuck If:** An automated criterion fails and the cause is not clear from the output.
- [x] Complete

---
⛔ Final slice complete. Run **inspector** for final sign-off.

INSPECTED 2026-06-08 — 8 PASS · 0 FAIL (see output/inspect/Inspect_audience-training-log_Final_2026-06-08.md)
