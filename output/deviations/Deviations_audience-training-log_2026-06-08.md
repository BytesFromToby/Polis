# Deviations — Audience Training Log
Blueprint: Planning/blueprints/audience-training-log_BP.md
Date: 2026-06-08

| Slice | Step | Deviation | Why |
|-------|------|-----------|-----|
| —     | —    | None.     | —   |

Implemented as written. Writer is `engine/llm/audience_log.py` (`log_audience`); call sites
wired in `audience_conclude` (faction-declined) and `audience_finalize` (accept outcomes).
Wiring tests monkeypatch the engine step functions + spy on `log_audience` (no LLM/DB), per
the blueprint's suggested approach.
