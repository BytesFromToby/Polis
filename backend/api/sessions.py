"""
api/sessions.py — In-memory sim session manager.

Holds one live engine state per user. State is loaded from the DB on
city/load and cleared on sim/reset or server restart.

On server restart, an active run is restored from its latest cycle snapshot
when the user next hits a sim or state endpoint.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional

from fastapi import HTTPException, status

from engine.models import WorldState, Faction, Domain, Mayor, Treasury, Project, BaseProjectStack


@dataclass
class SimSession:
    run_id: str
    world: WorldState
    factions: Dict[str, Faction]
    domains: Dict[str, Domain]
    mayor: Mayor = None
    treasury: Treasury = None
    projects: Dict[str, Project] = None                       # legacy: tax_collection / standard
    base_stacks: Dict[str, BaseProjectStack] = None           # one per domain (projects_spec v6)
    is_running: bool = False   # True while sim/run/{n} is executing
    llm_profile_id: Optional[str] = None
    audience_state: Optional[dict] = None  # in-progress audience negotiation

    def __post_init__(self):
        if self.projects is None:
            self.projects = {}
        if self.base_stacks is None:
            self.base_stacks = {}


# user_id → SimSession
_sessions: Dict[str, SimSession] = {}


def get_session(user_id: str) -> Optional[SimSession]:
    return _sessions.get(user_id)


def set_session(user_id: str, session: SimSession) -> None:
    _sessions[user_id] = session


def clear_session(user_id: str) -> None:
    _sessions.pop(user_id, None)


def require_session(user_id: str) -> SimSession:
    """Return session or raise HTTPException(404) if none exists."""
    session = _sessions.get(user_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active sim session for user {user_id}",
        )
    return session
