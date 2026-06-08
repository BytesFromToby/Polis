"""
engine/llm/audience_log.py — Audience training log (audience-training-log_spec).

Appends one JSONL record per COMPLETED, live-AI audience to backend/logs/audiences.jsonl,
capturing the system prompt, the full transcript (incl. the Mayor's freeform inputs), the raw
step-5 response, the parsed deal, and the outcome. Built for later fine-tuning of a small LM;
the training pipeline itself is out of scope. Stub-mode audiences (and tests) are not logged.
"""
from __future__ import annotations
import json
import os
from datetime import datetime, timezone

SCHEMA_VERSION = 1

# backend/engine/llm/audience_log.py → backend/logs/audiences.jsonl
DEFAULT_LOG_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "logs", "audiences.jsonl")
)


def _first_user_text(messages) -> str:
    """The Mayor's opening — the first user-role message in the transcript."""
    for m in messages or []:
        if m.get("role") == "user":
            return m.get("content", "")
    return ""


def _build_turns(state) -> list:
    parsed = state.get("pending_parsed")
    step5_text = getattr(parsed, "narrative", "") if parsed is not None else ""
    return [
        {"role": "faction", "step": 1, "text": state.get("step1_narrative", "")},
        {"role": "mayor",   "step": 2, "text": _first_user_text(state.get("messages"))},
        {"role": "faction", "step": 3, "text": state.get("step3_narrative", "")},
        {"role": "mayor",   "step": 4, "text": state.get("mayor_closing", "")},
        {"role": "faction", "step": 5, "text": step5_text},
    ]


def _parsed_deal(state) -> dict:
    from engine.llm.audiences import _term_to_dict
    parsed = state.get("pending_parsed")
    if parsed is None:
        return {"accepted": False, "mayor_terms": [], "faction_terms": [], "memory_note": ""}
    return {
        "accepted": bool(getattr(parsed, "accepted", False)),
        "mayor_terms": [_term_to_dict(t) for t in (getattr(parsed, "mayor_terms", None) or [])],
        "faction_terms": [_term_to_dict(t) for t in (getattr(parsed, "faction_terms", None) or [])],
        "memory_note": getattr(parsed, "memory_note", "") or "",
    }


def log_audience(state, faction, run_id, cycle, outcome, path=None) -> bool:
    """Append one JSONL record for a completed audience. Live-AI only: writes nothing
    (returns False) when the audience ran in stub mode. Returns True when a line is written."""
    cfg = state.get("llm_config")
    if cfg is None or getattr(cfg, "provider", "stub") == "stub":
        return False

    record = {
        "schema_version": SCHEMA_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "cycle": cycle,
        "provider": getattr(cfg, "provider", ""),
        "model": getattr(cfg, "model", ""),
        "faction": {
            "id": faction.id,
            "name": faction.name,
            "domain_primary": faction.domain_primary,
            "traits": [t.trait for t in getattr(faction, "traits", [])],
        },
        "system_prompt": state.get("system", ""),
        "turns": _build_turns(state),
        "step5_raw": state.get("step5_raw", ""),
        "parsed_deal": _parsed_deal(state),
        "outcome": outcome,
    }

    target = path or DEFAULT_LOG_PATH
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return True
