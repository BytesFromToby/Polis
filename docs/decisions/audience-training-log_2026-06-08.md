# Decisions: Audience Training Log
Spec: Planning/specs/audience-training-log_spec.md
Date: 2026-06-08

- JSONL, one record per completed audience — directly loadable for later LM fine-tuning; full
  records preserve the whole negotiation arc (vs per-call pairs, which lose context unless
  rejoined). Per-call pairs can be derived from a full record later if needed.
- Live-AI only (skip when `llm_config.provider == "stub"`). Stub responses are canned and
  useless as training data, and this also excludes the test suite automatically without a
  separate test flag. Each record still tags provider+model so a mixed dataset can be filtered.
- File at `backend/logs/audiences.jsonl`, not a DB table. Portable for export/packaging and
  trivially appendable; a table would be heavier and harder to ship as a dataset.
- Written on full resolution only — declines at `conclude`, accepts at `finalize` — so each
  record carries the final outcome. Abandoned/incomplete/errored audiences are skipped (partial
  examples would be noise).
- `schema_version` included so the record format can evolve without breaking older data when the
  training pipeline is built later.
- Capture only now; the training/export/fine-tune pipeline is explicitly out of scope (later).
