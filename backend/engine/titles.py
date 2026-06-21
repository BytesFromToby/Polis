"""
engine/titles.py — the Mayor's title ladder (elections_spec / elections-and-titles proposal).

An ordered progression of civic honorifics, bottom → top. Election wins climb it; losses demote
down it (on forgiving profiles); reaching the top rung is victory. `Mayor.title_rank` indexes here.

Content/theming — kept deliberately small; expand alongside reference/theming.md.
"""
from __future__ import annotations

TITLE_LADDER: list[str] = [
    "Prytanis",    # 0 — the starting rung (matches the player-identity default)
    "Archon",      # 1
    "Strategos",   # 2
    "Hegemon",     # 3
    "Basileus",    # 4 — the top rung; reaching it is victory
]

TOP_RANK: int = len(TITLE_LADDER) - 1


def title_for_rank(rank: int) -> str:
    """The title at a rank, clamped to the ladder bounds."""
    return TITLE_LADDER[max(0, min(TOP_RANK, rank))]
