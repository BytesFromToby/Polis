"""
api/routes/state.py — State reads and GM edits (live sim).

GET    /users/{user_id}/state                   Full world state snapshot
GET    /users/{user_id}/factions                All factions
GET    /users/{user_id}/factions/{id}           Single faction
GET    /users/{user_id}/domains                 All domains
GET    /users/{user_id}/logs                    Narrative log (most recent N)
GET    /users/{user_id}/cycles                  List cycle snapshot metadata
GET    /users/{user_id}/cycles/{n}              State at cycle N

PATCH  /users/{user_id}/factions/{id}           Edit faction mid-sim
POST   /users/{user_id}/factions                Add faction mid-sim
DELETE /users/{user_id}/factions/{id}           Dissolve faction mid-sim
POST   /users/{user_id}/events/trigger          Manually fire a named event
"""
from __future__ import annotations
import json
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.deps import get_current_user
from api.routes.sim import _get_or_restore_session
from api.schemas import (
    FactionCreateRequest, FactionPatchRequest,
    EventTriggerRequest,
    CycleSnapshotMeta,
)
from api.sessions import require_session, get_session
from db.models import CycleSnapshot, NarrativeLog, SimRun, User
from db.session import get_db
from engine.models import Faction, FactionTrait, Leader
from serializer import (
    serialize_state, serialize_faction,
    deserialize_state,
)

router = APIRouter(prefix="/users/{user_id}", tags=["state"])


def _check_not_running(user_id: str) -> None:
    from api.sessions import get_session
    session = get_session(user_id)
    if session and session.is_running:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="GM edits are blocked while a multi-cycle run is in progress.",
        )


def _get_run(user_id: str, db: Session) -> SimRun:
    """Get the active SimRun, preferring the in-memory session's run_id."""
    session = get_session(user_id)
    if session:
        run = db.query(SimRun).filter_by(run_id=session.run_id).first()
        if run and run.status in ("running", "paused"):
            return run
    # Fallback
    run = db.query(SimRun).filter(
        SimRun.user_id == user_id,
        SimRun.status.in_(["running", "paused"]),
    ).order_by(SimRun.created_at.desc()).first()
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active sim run.",
        )
    return run


# ── State Reads ───────────────────────────────────────────────────────────────

@router.get("/state")
def get_state(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    session = _get_or_restore_session(user_id, db)
    return serialize_state(session.world, session.factions, session.domains,
                           public=session.public, active_events=session.active_events)


@router.get("/factions")
def get_factions(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    session = _get_or_restore_session(user_id, db)
    return {fid: serialize_faction(f) for fid, f in session.factions.items()}


@router.get("/factions/{faction_id}")
def get_faction(
    user_id: str,
    faction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    session = _get_or_restore_session(user_id, db)
    faction = session.factions.get(faction_id)
    if faction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faction not found")
    return serialize_faction(faction)


@router.get("/domains")
def get_domains(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    session = _get_or_restore_session(user_id, db)
    from serializer import serialize_domain
    return {did: serialize_domain(d) for did, d in session.domains.items()}


@router.get("/logs")
def get_logs(
    user_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    run = _get_run(user_id, db)
    entries = (
        db.query(NarrativeLog)
        .filter_by(run_id=run.run_id)
        .order_by(NarrativeLog.cycle_number.desc())
        .limit(limit)
        .all()
    )
    result = []
    for e in reversed(entries):
        result.append({
            "cycle": e.cycle_number,
            "events": json.loads(e.events_json),
        })
    return result


@router.get("/cycles", response_model=List[CycleSnapshotMeta])
def list_cycles(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    run = _get_run(user_id, db)
    snapshots = (
        db.query(CycleSnapshot)
        .filter_by(run_id=run.run_id)
        .order_by(CycleSnapshot.cycle_number)
        .all()
    )
    return snapshots


@router.get("/cycles/{cycle_number}")
def get_cycle(
    user_id: str,
    cycle_number: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    run = _get_run(user_id, db)
    snapshot = (
        db.query(CycleSnapshot)
        .filter_by(run_id=run.run_id, cycle_number=cycle_number)
        .first()
    )
    if snapshot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cycle snapshot not found")
    return json.loads(snapshot.state_json)


# ── GM Edits ──────────────────────────────────────────────────────────────────

@router.patch("/factions/{faction_id}")
def patch_faction_live(
    user_id: str,
    faction_id: str,
    req: FactionPatchRequest,
    current_user: User = Depends(get_current_user),
):
    if user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    _check_not_running(user_id)
    session = require_session(user_id)
    faction = session.factions.get(faction_id)
    if faction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faction not found")

    if req.name is not None:
        faction.name = req.name
    if req.rating is not None:
        faction.rating = max(1.0, min(10.0, req.rating))

    return serialize_faction(faction)


@router.post("/factions")
def add_faction_live(
    user_id: str,
    req: FactionCreateRequest,
    current_user: User = Depends(get_current_user),
):
    if user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    _check_not_running(user_id)
    session = require_session(user_id)

    fid = f"faction_{str(uuid.uuid4())[:8]}"
    new_faction = Faction(
        id=fid,
        name=req.name,
        domain_primary=req.domain_primary,
        leader=Leader(name=f"Leader of {req.name}"),
        rating=req.rating,
        health=75,
        traits=[FactionTrait(trait=t) for t in (req.traits or [])],
        relationships=[],
    )
    session.factions[fid] = new_faction
    return serialize_faction(new_faction)


@router.delete("/factions/{faction_id}", status_code=status.HTTP_204_NO_CONTENT)
def dissolve_faction_live(
    user_id: str,
    faction_id: str,
    current_user: User = Depends(get_current_user),
):
    if user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    _check_not_running(user_id)
    session = require_session(user_id)
    if faction_id not in session.factions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faction not found")
    session.factions.pop(faction_id)


@router.post("/events/trigger")
def trigger_event(
    user_id: str,
    req: EventTriggerRequest,
    current_user: User = Depends(get_current_user),
):
    if user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    _check_not_running(user_id)
    session = require_session(user_id)

    known_events = {"power_vacuum"}
    if req.event_name not in known_events:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown event '{req.event_name}'. Known: {sorted(known_events)}",
        )

    # power_vacuum events are retired (factions are permanent) — accepted as a no-op.

    return {"detail": f"Event '{req.event_name}' triggered."}
