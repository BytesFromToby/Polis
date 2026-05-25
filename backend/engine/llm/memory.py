"""
engine/llm/memory.py — Faction memory note creation and LLM-driven compression.

Rules:
  - Notes are ≤10 words (enforced by word-count trim at write time)
  - Max 8 notes per faction per run before compression is triggered
  - Compression: when a 9th note would be added, send oldest 5 to LLM for summary,
    replace them with one is_summary=True note, then write the new note
  - Compression falls back to a canned summary on LLM failure
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from engine.llm.client import LLMClient

_COMPRESS_SYSTEM = (
    "You are a concise historian. Summarise the following interaction notes "
    "into one sentence of 10 words or fewer. Output ONLY that sentence."
)

_MAX_NOTES = 8
_COMPRESS_OLDEST = 5


def _trim_to_words(text: str, limit: int = 10) -> str:
    words = re.split(r"\s+", text.strip())
    return " ".join(words[:limit])


class MemoryWriter:

    def write_note(
        self,
        run_id: str,
        faction_id: str,
        cycle: int,
        note: str,
        note_type: str,
        db: "Session",
        llm_client: "LLMClient | None" = None,
    ) -> None:
        """
        Persist a memory note. Triggers compression if this would exceed _MAX_NOTES.
        note_type: "audience" | "event" | "summary"
        """
        from db.models import FactionMemory

        note = _trim_to_words(note)

        existing = (
            db.query(FactionMemory)
            .filter(FactionMemory.run_id == run_id, FactionMemory.faction_id == faction_id)
            .order_by(FactionMemory.cycle.asc())
            .all()
        )

        if len(existing) >= _MAX_NOTES:
            self._compress(existing, run_id, faction_id, cycle, db, llm_client)

        db.add(FactionMemory(
            run_id=run_id,
            faction_id=faction_id,
            cycle=cycle,
            note=note,
            is_summary=False,
            type=note_type,
        ))
        db.flush()

    def _compress(
        self,
        existing: list,
        run_id: str,
        faction_id: str,
        cycle: int,
        db: "Session",
        llm_client: "LLMClient | None",
    ) -> None:
        """Replace the oldest _COMPRESS_OLDEST notes with a single summary note."""
        from db.models import FactionMemory

        to_compress = existing[:_COMPRESS_OLDEST]
        notes_text = "\n".join(f"- {row.note}" for row in to_compress)

        summary = self._llm_summarise(notes_text, llm_client)

        for row in to_compress:
            db.delete(row)

        db.add(FactionMemory(
            run_id=run_id,
            faction_id=faction_id,
            cycle=cycle,
            note=f"older interactions summary: {summary}",
            is_summary=True,
            type="summary",
        ))
        db.flush()

    def _llm_summarise(self, notes_text: str, llm_client: "LLMClient | None") -> str:
        if llm_client is None:
            return "earlier dealings with mayor noted"
        try:
            result = llm_client.complete(
                system=_COMPRESS_SYSTEM,
                messages=[{"role": "user", "content": notes_text}],
            )
            return _trim_to_words(result.strip())
        except Exception:
            return "earlier dealings with mayor noted"
