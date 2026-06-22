"""
api/routes/sim.py — Sim control endpoints.

POST /users/{user_id}/sim/start       Initialize sim from current city
POST /users/{user_id}/sim/step        Run one cycle
POST /users/{user_id}/sim/run/{n}     Run N cycles (max 100, stops on Crisis)
POST /users/{user_id}/sim/pause       Request pause between cycles
POST /users/{user_id}/sim/reset       Reset to starting city (cycle 0)
GET  /users/{user_id}/sim/status      Current cycle, running/paused state
"""
from __future__ import annotations
import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_current_user
from api.schemas import SimStatusResponse, SimStepResponse, SimRunResponse, SimRunDetail, SimPatchRequest, SimStartRequest, SimSetProfileRequest
from api.sessions import SimSession, get_session, set_session, clear_session, require_session, dev_mode
from db.models import City, SimRun, CycleSnapshot, NarrativeLog, User
from db.session import get_db
from engine.cycle.runner import run_cycle
from engine.balance import get_profile
from engine.models import Mayor, Treasury
from loaders import load_projects, load_chains, load_the_public, load_event_deck

# Chain definitions and the event deck are static data — load once per process.
_CHAINS = load_chains()
_EVENT_DECK = load_event_deck()
from engine.projects import new_base_stacks
from serializer import serialize_state, serialize_cycle_event, deserialize_state

router = APIRouter(prefix="/users/{user_id}", tags=["sim"])

_MAX_RUN_CYCLES = 100


def _restore_session(user_id: str, db: Session, run_id: str | None = None) -> SimSession:
    """Restore an in-memory session from a DB snapshot.
    If run_id is given, restore that specific run; otherwise find the latest active one."""
    if run_id:
        run = db.query(SimRun).filter_by(run_id=run_id, user_id=user_id).first()
        if run is None or run.status not in ("running", "paused"):
            raise ValueError(f"Run {run_id} not found or not active")
    else:
        run = db.query(SimRun).filter(
            SimRun.user_id == user_id,
            SimRun.status.in_(["running", "paused"]),
        ).order_by(SimRun.created_at.desc()).first()
        if run is None:
            raise ValueError(f"No active run to restore for user {user_id}")

    snapshot = (
        db.query(CycleSnapshot)
        .filter_by(run_id=run.run_id)
        .order_by(CycleSnapshot.cycle_number.desc())
        .first()
    )
    if snapshot is None:
        raise ValueError("No snapshots found to restore from")

    world, factions, domains, mayor, treasury, projects, base_stacks, public = deserialize_state(json.loads(snapshot.state_json))
    # Snapshots pre-dating mayor/treasury support will deserialize as None — provide fresh defaults
    if mayor is None:
        mayor = Mayor()
    if treasury is None:
        treasury = Treasury()
    if not projects:
        projects = load_projects()
    if not base_stacks:
        base_stacks = new_base_stacks(domains)
    if public is None:
        public = load_the_public()
    session = SimSession(
        run_id=run.run_id, world=world, factions=factions, domains=domains,
        mayor=mayor, treasury=treasury, projects=projects, base_stacks=base_stacks,
        public=public, llm_profile_id=run.llm_profile_id,
        difficulty=run.difficulty or "normal",
    )
    set_session(user_id, session)
    return session


def _get_or_restore_session(user_id: str, db: Session, run_id: str | None = None) -> SimSession:
    """Return existing session or restore from DB if missing.
    If run_id is given and the current session is for a different run, switch."""
    session = get_session(user_id)
    if session is not None:
        if run_id and session.run_id != run_id:
            clear_session(user_id)
            return _restore_session(user_id, db, run_id)
        return session
    return _restore_session(user_id, db, run_id)


def _get_active_run(user_id: str, db: Session) -> SimRun:
    """Get the active SimRun row. Uses the in-memory session's run_id if available
    so we always target the correct run, not just the latest one."""
    session = get_session(user_id)
    if session:
        run = db.query(SimRun).filter_by(run_id=session.run_id).first()
        if run and run.status in ("running", "paused"):
            return run
    # Fallback: latest active run
    run = db.query(SimRun).filter(
        SimRun.user_id == user_id,
        SimRun.status.in_(["running", "paused"]),
    ).order_by(SimRun.created_at.desc()).first()
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active sim run. Use /sim/start first.",
        )
    return run


def _save_cycle(db: Session, run_id: str, world, factions, domains, events,
                mayor=None, treasury=None, projects=None, base_stacks=None,
                public=None, published: bool = True) -> None:
    snapshot = CycleSnapshot(
        run_id=run_id,
        cycle_number=world.cycle,
        state_json=json.dumps(serialize_state(world, factions, domains, mayor, treasury, projects, base_stacks, public=public)),
    )
    db.add(snapshot)

    log_entry = NarrativeLog(
        run_id=run_id,
        cycle_number=world.cycle - 1,
        events_json=json.dumps([serialize_cycle_event(e) for e in events]),
        published=published,
    )
    db.add(log_entry)
    db.commit()


# ── Start ─────────────────────────────────────────────────────────────────────

@router.get("/runs", response_model=list[SimRunDetail])
def list_runs(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    runs = (
        db.query(SimRun)
        .filter_by(user_id=user_id)
        .order_by(SimRun.updated_at.desc())
        .all()
    )
    result = []
    for r in runs:
        city = db.query(City).filter_by(city_id=r.city_id).first()
        result.append(SimRunDetail(
            run_id=r.run_id,
            city_id=r.city_id,
            city_name=city.city_name if city else "Unknown",
            current_cycle=r.current_cycle,
            status=r.status,
            updated_at=r.updated_at.isoformat(),
        ))
    return result


@router.post("/sim/start", response_model=SimStatusResponse)
def start_sim(
    user_id: str,
    req: SimStartRequest = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    setup_run = db.query(SimRun).filter_by(user_id=user_id, status="setup").order_by(
        SimRun.created_at.desc()
    ).first()
    if setup_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No city in setup. Use /city/load or /city/new first.",
        )

    city = db.query(City).filter_by(city_id=setup_run.city_id).first()
    if city is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="City not found")

    # Deserialize city template into live engine state
    state_data = {
        "world": json.loads(city.world_state_json),
        "factions": json.loads(city.factions_json),
        "domains": json.loads(city.domains_json),
    }
    world, factions, domains, _, _, _, _, _ = deserialize_state(state_data)

    mayor = Mayor()
    treasury = Treasury()
    projects = load_projects()
    base_stacks = new_base_stacks(domains)
    public = load_the_public()

    setup_run.status = "running"
    setup_run.current_cycle = 0
    setup_run.player_name = (
        req.player_name.strip() if req and req.player_name and req.player_name.strip()
        else "Kallisto"
    )
    setup_run.player_title = (
        req.player_title.strip() if req and req.player_title and req.player_title.strip()
        else "Prytanis"
    )
    if req and req.llm_profile_id:
        from db.models import LLMProfile
        profile = db.query(LLMProfile).filter_by(profile_id=req.llm_profile_id).first()
        if profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="LLM profile not found")
        setup_run.llm_profile_id = req.llm_profile_id
    else:
        setup_run.llm_profile_id = None

    # Difficulty (balance profile) — unknown/None falls back to "normal" (see engine/balance.py)
    from engine.balance import get_profile
    setup_run.difficulty = get_profile(req.difficulty if req else None).name

    db.commit()

    session = SimSession(
        run_id=setup_run.run_id,
        world=world,
        factions=factions,
        domains=domains,
        mayor=mayor,
        treasury=treasury,
        projects=projects,
        base_stacks=base_stacks,
        public=public,
        llm_profile_id=setup_run.llm_profile_id,
        difficulty=setup_run.difficulty,
    )
    set_session(user_id, session)

    # Save cycle-0 snapshot
    _save_cycle(db, setup_run.run_id, world, factions, domains, [],
                mayor=mayor, treasury=treasury, projects=projects, base_stacks=base_stacks,
                public=public)

    return SimStatusResponse(
        run_id=setup_run.run_id,
        current_cycle=world.cycle,
        status="running",
    )


@router.patch("/sim/llm-profile")
def set_sim_llm_profile(
    user_id: str,
    req: SimSetProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change the LLM profile for the active run (can be swapped mid-game)."""
    if user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    if req.llm_profile_id:
        from db.models import LLMProfile
        profile = db.query(LLMProfile).filter_by(profile_id=req.llm_profile_id).first()
        if profile is None:
            raise HTTPException(status_code=404, detail="LLM profile not found")
    run = _get_active_run(user_id, db)
    run.llm_profile_id = req.llm_profile_id
    db.commit()
    session = get_session(user_id)
    if session:
        session.llm_profile_id = req.llm_profile_id
    return {"llm_profile_id": req.llm_profile_id}


# ── Step ──────────────────────────────────────────────────────────────────────

@router.post("/sim/step", response_model=SimStepResponse)
def step_sim(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    session = _get_or_restore_session(user_id, db)
    if session.is_running:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A multi-cycle run is in progress.",
        )

    run = _get_active_run(user_id, db)

    result = run_cycle(session.world, session.factions, session.domains,
                       mayor=session.mayor, treasury=session.treasury,
                       projects=session.projects, base_stacks=session.base_stacks,
                       public=session.public, chains=_CHAINS,
                       event_deck=_EVENT_DECK, active_events=session.active_events,
                       balance=get_profile(session.difficulty))

    run.current_cycle = session.world.cycle
    if session.world.game_over and run.status != "complete":
        run.status = "complete"
        run.end_cause = session.world.end_cause

    _save_cycle(db, run.run_id, session.world, session.factions, session.domains,
                result.events, mayor=session.mayor, treasury=session.treasury,
                projects=session.projects, base_stacks=session.base_stacks,
                public=session.public)

    return SimStepResponse(
        cycle=result.cycle,
        events_count=len(result.events),
        dramatic_count=sum(1 for e in result.events if e.dramatic > 0),
        game_over=session.world.game_over,
        end_cause=session.world.end_cause,
    )


# ── Run N ─────────────────────────────────────────────────────────────────────

@router.post("/sim/run/{n}", response_model=SimRunResponse)
def run_n(
    user_id: str,
    n: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    if n < 1 or n > _MAX_RUN_CYCLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"n must be between 1 and {_MAX_RUN_CYCLES}",
        )

    session = _get_or_restore_session(user_id, db)
    if session.is_running:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A multi-cycle run is already in progress.",
        )

    run = _get_active_run(user_id, db)

    session.is_running = True
    cycles_run = 0
    stopped_early = False
    stop_reason: str | None = None

    try:
        for _ in range(n):
            # Check pause flag
            if not session.is_running:
                stopped_early = True
                stop_reason = "paused"
                break

            result = run_cycle(session.world, session.factions, session.domains,
                               mayor=session.mayor, treasury=session.treasury,
                               projects=session.projects, base_stacks=session.base_stacks,
                               public=session.public, chains=_CHAINS,
                               event_deck=_EVENT_DECK, active_events=session.active_events,
                               balance=get_profile(session.difficulty))
            cycles_run += 1

            run.current_cycle = session.world.cycle
            # Terminal fail state — set status before saving so the commit persists it.
            game_over = session.world.game_over
            if game_over:
                run.status = "complete"
                run.end_cause = session.world.end_cause
            _save_cycle(db, run.run_id, session.world, session.factions, session.domains,
                        result.events, mayor=session.mayor, treasury=session.treasury,
                        projects=session.projects, base_stacks=session.base_stacks,
                        public=session.public)
            if game_over:
                stopped_early = True
                stop_reason = "game_over"
                break

    finally:
        session.is_running = False

    return SimRunResponse(
        cycles_run=cycles_run,
        final_cycle=session.world.cycle,
        stopped_early=stopped_early,
        stop_reason=stop_reason,
    )


# ── Pause ─────────────────────────────────────────────────────────────────────

@router.post("/sim/pause")
def pause_sim(
    user_id: str,
    current_user: User = Depends(get_current_user),
):
    if user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    session = get_session(user_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active session")

    session.is_running = False
    return {"detail": "Pause requested. Will stop after current cycle completes."}


# ── Reset ─────────────────────────────────────────────────────────────────────

@router.post("/sim/reset", response_model=SimStatusResponse)
def reset_sim(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    run = db.query(SimRun).filter(
        SimRun.user_id == user_id,
        SimRun.status.in_(["running", "paused"]),
    ).order_by(SimRun.created_at.desc()).first()

    if run:
        run.status = "setup"
        run.current_cycle = 0
        db.commit()

    clear_session(user_id)

    return SimStatusResponse(
        run_id=run.run_id if run else "",
        current_cycle=0,
        status="setup",
    )


# ── Delete Run ────────────────────────────────────────────────────────────────

@router.delete("/runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_run(
    user_id: str,
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a sim run and all its snapshots/logs. Also deletes the city
    if it's a user-created (non-official, non-published) city with no other runs."""
    if user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    run = db.query(SimRun).filter_by(run_id=run_id, user_id=user_id).first()
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

    # Clear in-memory session if this is the active one
    session = get_session(user_id)
    if session and session.run_id == run_id:
        clear_session(user_id)

    city_id = run.city_id

    # Delete child rows first
    db.query(CycleSnapshot).filter_by(run_id=run_id).delete()
    db.query(NarrativeLog).filter_by(run_id=run_id).delete()
    db.delete(run)

    # If the city is user-created and no other runs reference it, clean it up
    city = db.query(City).filter_by(city_id=city_id).first()
    if city and not city.is_official and not city.published:
        other_runs = db.query(SimRun).filter_by(city_id=city_id).count()
        if other_runs == 0:
            db.delete(city)

    db.commit()


def _build_status(run: SimRun, db: Session, user_id: str) -> SimStatusResponse:
    """Build a SimStatusResponse including city name and description."""
    session = get_session(user_id)
    current_cycle = session.world.cycle if session else run.current_cycle
    city = db.query(City).filter_by(city_id=run.city_id).first()
    return SimStatusResponse(
        run_id=run.run_id,
        current_cycle=current_cycle,
        status=run.status,
        city_name=city.city_name if city else "",
        description=run.description or "",
        llm_profile_id=run.llm_profile_id,
        difficulty=run.difficulty or "normal",
        end_cause=run.end_cause or "",
        dev_mode=dev_mode(),
    )


# ── Status ────────────────────────────────────────────────────────────────────

@router.post("/sim/switch/{run_id}", response_model=SimStatusResponse)
def switch_run(
    user_id: str,
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Switch the active in-memory session to a specific run."""
    if user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    run = db.query(SimRun).filter_by(run_id=run_id, user_id=user_id).first()
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    if run.status not in ("running", "paused"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Run is in '{run.status}' state, not resumable.",
        )

    # Clear old session and restore from this run's snapshots
    clear_session(user_id)
    try:
        _restore_session(user_id, db, run_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return _build_status(run, db, user_id)


@router.get("/sim/status", response_model=SimStatusResponse)
def sim_status(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    # Use session's run_id if available, otherwise latest
    session = get_session(user_id)
    if session:
        run = db.query(SimRun).filter_by(run_id=session.run_id).first()
    else:
        run = db.query(SimRun).filter(
            SimRun.user_id == user_id,
        ).order_by(SimRun.created_at.desc()).first()

    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No sim run found")

    return _build_status(run, db, user_id)


@router.patch("/sim/info", response_model=SimStatusResponse)
def patch_sim_info(
    user_id: str,
    req: SimPatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Edit city name and description from the dashboard."""
    if user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    run = db.query(SimRun).filter(
        SimRun.user_id == user_id,
        SimRun.status.in_(["running", "paused"]),
    ).order_by(SimRun.created_at.desc()).first()
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active run")

    city = db.query(City).filter_by(city_id=run.city_id).first()
    if req.city_name is not None and city:
        city.city_name = req.city_name
    if req.description is not None:
        run.description = req.description

    db.commit()
    return _build_status(run, db, user_id)


