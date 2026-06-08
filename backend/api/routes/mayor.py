"""
api/routes/mayor.py — Mayor, Treasury, and Projects endpoints.

GET  /users/{user_id}/treasury
PATCH /users/{user_id}/treasury/tax-rate
POST /users/{user_id}/treasury/borrow
POST /users/{user_id}/treasury/invest
POST /users/{user_id}/treasury/public-works
POST /users/{user_id}/treasury/guard-surge

GET  /users/{user_id}/mayor
POST /users/{user_id}/mayor/exempt

GET  /users/{user_id}/projects
GET  /users/{user_id}/projects/catalog
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_current_user
from api.schemas import (
    TreasuryResponse, TaxRateRequest, BorrowRequest, InvestRequest,
    MayorResponse, ExemptFactionRequest,
    MayorActRequest, MayorActResponse, VALID_MAYOR_ACTIONS,
    AudienceBeginRequest, AudienceBeginResponse,
    AudienceReplyRequest, AudienceReplyResponse,
    AudienceConcludeRequest, AudienceConcludeResponse,
    AudienceFinalizeRequest, AudienceFinalizeResponse,
    ProjectResponse, BaseStackResponse,
)
from api.sessions import SimSession, get_session
from db.models import User
from db.session import get_db
from engine.llm.audience_log import log_audience
from engine.mayor.treasury import (
    borrow_from_moneylender, invest_with_moneylender,
    spend_public_works, spend_emergency_guard_surge,
)
from engine.mayor.actions import execute_mayor_actions, ACTION_COSTS
from engine.projects import mayor_build_or_repair
from loaders import load_projects

router = APIRouter(prefix="/users/{user_id}", tags=["mayor"])

_CATALOG: dict = {}  # lazy-loaded once


def _get_catalog() -> dict:
    global _CATALOG
    if not _CATALOG:
        _CATALOG = load_projects()
    return _CATALOG


def _auth(user_id: str, current_user: User) -> None:
    if user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


def _get_session(user_id: str, db: Session) -> SimSession:
    """Return session, auto-restoring from DB if not in memory."""
    from api.routes.sim import _restore_session
    session = get_session(user_id)
    if session is not None:
        return session
    try:
        return _restore_session(user_id, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ── Treasury ──────────────────────────────────────────────────────────────────

@router.get("/treasury", response_model=TreasuryResponse)
def get_treasury(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _auth(user_id, current_user)
    session = _get_session(user_id, db)
    t = session.treasury
    max_rate = t.max_tax_rate(session.projects or {})
    return TreasuryResponse(
        gold=t.gold,
        domain_tax_rates=dict(t.domain_tax_rates),
        debt=t.debt,
        debt_rate=t.debt_rate,
        invested=t.invested,
        invest_cycles_remaining=t.invest_cycles_remaining,
        invest_return_rate=t.invest_return_rate,
        income_this_cycle=t.income_this_cycle,
        expenditure_this_cycle=t.expenditure_this_cycle,
        max_tax_rate=max_rate,
    )


@router.patch("/treasury/tax-rate")
def set_tax_rate(
    user_id: str,
    req: TaxRateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _auth(user_id, current_user)
    session = _get_session(user_id, db)
    try:
        session.treasury.set_rate(req.domain_id, req.rate, session.projects or {})
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return {"detail": f"Tax rate for {req.domain_id} set to {req.rate}"}


@router.post("/treasury/borrow")
def borrow(
    user_id: str,
    req: BorrowRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _auth(user_id, current_user)
    session = _get_session(user_id, db)
    result = borrow_from_moneylender(session.treasury, req.amount)
    if result.outcome == "fail":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.narrative)
    return {"detail": result.narrative, "gold": session.treasury.gold, "debt": session.treasury.debt}


@router.post("/treasury/invest")
def invest(
    user_id: str,
    req: InvestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _auth(user_id, current_user)
    session = _get_session(user_id, db)
    result = invest_with_moneylender(session.treasury, req.amount, req.term)
    if result.outcome == "fail":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.narrative)
    return {"detail": result.narrative, "gold": session.treasury.gold, "invested": session.treasury.invested}


@router.post("/treasury/public-works")
def public_works(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _auth(user_id, current_user)
    session = _get_session(user_id, db)
    result = spend_public_works(session.treasury, session.mayor)
    if result.outcome == "fail":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.narrative)
    return {"detail": result.narrative, "gold": session.treasury.gold}


@router.post("/treasury/guard-surge")
def guard_surge(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _auth(user_id, current_user)
    session = _get_session(user_id, db)
    result = spend_emergency_guard_surge(session.treasury, session.mayor)
    if result.outcome == "fail":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.narrative)
    return {"detail": result.narrative, "gold": session.treasury.gold}


# ── Mayor ──────────────────────────────────────────────────────────────────────

@router.get("/mayor", response_model=MayorResponse)
def get_mayor(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _auth(user_id, current_user)
    session = _get_session(user_id, db)
    m = session.mayor
    return MayorResponse(
        action_points=m.action_points,
        action_cap=m.action_cap,
        reputation=dict(m.reputation),
        cooldowns=dict(m.cooldowns),
        exemptions=dict(m.exemptions),
        committed_actions=list(m.committed_actions),
        deals={did: _deal_to_dict(d) for did, d in m.deals.items()},
    )


def _deal_to_dict(d) -> dict:
    """Serialize an engine Deal for the UI (keys match what the frontend reads)."""
    from engine.llm.audiences import _term_to_dict
    return {
        "deal_id": d.id,
        "faction_id": d.faction_id,
        "status": d.status,
        "cycles_remaining": d.cycles_remaining,
        "total_duration": d.total_duration,
        "rep_cost_if_broken": d.rep_cost_if_broken,
        "mayor_terms": [_term_to_dict(t) for t in d.mayor_terms],
        "faction_terms": [_term_to_dict(t) for t in d.faction_terms],
    }


@router.post("/mayor/exempt")
def grant_exemption(
    user_id: str,
    req: ExemptFactionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _auth(user_id, current_user)
    session = _get_session(user_id, db)
    factions = session.factions or {}
    target = factions.get(req.faction_id)
    if target is None:
        raise HTTPException(status_code=404, detail=f"Faction {req.faction_id} not found")
    domain = target.domain_primary
    for fid in session.mayor.exemptions:
        f = factions.get(fid)
        if f and f.domain_primary == domain and fid != req.faction_id:
            raise HTTPException(
                status_code=400,
                detail=f"Domain {domain} already has an active exemption"
            )
    ok = session.mayor.grant_exemption(req.faction_id, req.cycles)
    if not ok:
        raise HTTPException(status_code=400, detail="Insufficient action points")
    return {"detail": f"Exemption granted to {req.faction_id} for {req.cycles} cycles",
            "action_points": session.mayor.action_points}


@router.post("/mayor/act", response_model=MayorActResponse)
def mayor_act(
    user_id: str,
    req: MayorActRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Execute a single mayor action immediately against the live session."""
    _auth(user_id, current_user)

    if req.action not in VALID_MAYOR_ACTIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown action: {req.action!r}",
        )

    session = _get_session(user_id, db)
    mayor = session.mayor
    factions = session.factions or {}
    domains = session.domains or {}
    treasury = session.treasury

    # ── BreakADeal — 0 AP, handled separately ────────────────────────────────
    if req.action == "BreakADeal":
        deal_id = req.target_id
        deal = mayor.deals.get(deal_id)
        if deal is None:
            raise HTTPException(status_code=404, detail=f"Deal {deal_id} not found")
        cost = deal.rep_cost_if_broken
        mayor.adjust_reputation(deal.faction_id, -cost)
        mayor.adjust_reputation("the_public", -8)
        domain = (factions.get(deal.faction_id) or type("", (), {"domain_primary": ""})()).domain_primary
        for fid, f in factions.items():
            if fid != deal.faction_id and getattr(f, "domain_primary", "") == domain:
                mayor.adjust_reputation(fid, -3)
        deal.status = "broken_by_mayor"
        from engine.cycle.end_of_cycle import _clear_deal_effects
        _clear_deal_effects(deal, mayor, factions)
        return MayorActResponse(
            action="BreakADeal",
            outcome="decisive",
            narrative=f"Deal with {deal.faction_id} broken: rep -{cost}; public -8",
            action_points=mayor.action_points,
            dramatic=True,
        )

    # ── GrantTaxExemption — mirrors /mayor/exempt but via unified endpoint ────
    if req.action == "GrantTaxExemption":
        fid = req.target_id
        target = factions.get(fid)
        if target is None:
            raise HTTPException(status_code=404, detail=f"Faction {fid} not found")
        domain = target.domain_primary
        for exempt_fid in mayor.exemptions:
            f = factions.get(exempt_fid)
            if f and f.domain_primary == domain and exempt_fid != fid:
                raise HTTPException(
                    status_code=400,
                    detail=f"Domain {domain} already has an active exemption",
                )
        cycles = max(1, min(10, req.cycles))
        ok = mayor.grant_exemption(fid, cycles)
        if not ok:
            raise HTTPException(status_code=400, detail="Insufficient action points")
        return MayorActResponse(
            action="GrantTaxExemption",
            outcome="decisive",
            narrative=f"Tax exemption granted to {fid} for {cycles} cycles",
            action_points=mayor.action_points,
        )

    # ── BuildProject — context-aware (initiate/fund/repair) on the domain's stack ──
    if req.action == "BuildProject":
        base_stacks = session.base_stacks or {}
        r = mayor_build_or_repair(req.target_id, base_stacks, treasury, mayor)
        session.base_stacks = base_stacks
        if r.outcome == "fail":
            raise HTTPException(status_code=400, detail=r.narrative)
        return MayorActResponse(
            action="BuildProject",
            outcome=r.outcome,
            narrative=r.narrative,
            action_points=mayor.action_points,
            dramatic=bool(r.dramatic),
        )

    # ── All other actions via execute_mayor_actions ───────────────────────────
    from engine.models import MayorAction

    ma = MayorAction(
        action=req.action,
        target_id=req.target_id,
        cost=ACTION_COSTS.get(req.action, 1),
    )
    results = execute_mayor_actions([ma], mayor, treasury, factions, domains)

    if not results:
        raise HTTPException(status_code=500, detail="Action produced no result")

    r = results[0]
    if r.outcome == "fail":
        raise HTTPException(status_code=400, detail=r.narrative)

    return MayorActResponse(
        action=r.action,
        outcome=r.outcome,
        narrative=r.narrative,
        action_points=mayor.action_points,
        dramatic=bool(r.dramatic),
    )


def _get_llm_config(session, db):
    """Resolve LLMConfig from session's llm_profile_id, or None for stub."""
    from engine.llm.client import LLMConfig
    if not session.llm_profile_id:
        return None
    from db.models import LLMProfile
    profile = db.query(LLMProfile).filter_by(profile_id=session.llm_profile_id).first()
    return LLMConfig.from_profile(profile) if profile else None


def _get_city_description(session, db) -> str:
    from db.models import SimRun, City as CityModel
    run = db.query(SimRun).filter_by(run_id=session.run_id).first()
    if run:
        city_row = db.query(CityModel).filter_by(city_id=run.city_id).first()
        if city_row:
            return city_row.description or ""
    return ""


def _get_audience_identity(session, db) -> tuple[str, str, str]:
    """Return (city_name, player_name, player_title) for the prompt, with defaults."""
    from db.models import SimRun, City as CityModel
    run = db.query(SimRun).filter_by(run_id=session.run_id).first()
    player_name = (run.player_name if run and run.player_name else "Kallisto")
    player_title = (run.player_title if run and run.player_title else "Prytanis")
    city_name = "Polis"
    if run:
        city_row = db.query(CityModel).filter_by(city_id=run.city_id).first()
        if city_row and city_row.city_name:
            city_name = city_row.city_name
    return city_name, player_name, player_title


@router.post("/mayor/audience/begin", response_model=AudienceBeginResponse)
def audience_begin(
    user_id: str,
    req: AudienceBeginRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Step 1 — spend AP, run faction opening, store state in session."""
    _auth(user_id, current_user)
    session = _get_session(user_id, db)
    mayor = session.mayor
    factions = session.factions or {}

    # Active-AI requirement (audience_spec v5): an audience needs a valid active AI.
    # _get_llm_config returns None when llm_profile_id is unset or does not resolve to
    # an existing profile. Reject before any AP is spent.
    if _get_llm_config(session, db) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active AI is set for this game. Set an AI to hold audiences.",
        )

    faction = factions.get(req.faction_id)
    if faction is None:
        raise HTTPException(status_code=404, detail=f"Faction {req.faction_id} not found")
    if req.faction_id in mayor.cooldowns:
        raise HTTPException(
            status_code=400,
            detail=f"On cooldown: {mayor.cooldowns[req.faction_id]} cycles remaining",
        )
    from engine.mayor.actions import ACTION_COSTS
    if not mayor.spend(ACTION_COSTS.get("MeetWithFaction", 1)):
        raise HTTPException(status_code=400, detail="Insufficient action points")

    from engine.llm.audiences import begin_audience_step, AudienceError
    city_name, player_name, player_title = _get_audience_identity(session, db)
    try:
        state = begin_audience_step(
            faction=faction, mayor=mayor,
            run_id=session.run_id, cycle=session.world.cycle,
            db=db, factions=factions, domains=session.domains or {},
            city_description=_get_city_description(session, db),
            city_name=city_name, player_name=player_name, player_title=player_title,
            llm_config=_get_llm_config(session, db),
        )
    except AudienceError as exc:
        mayor.action_points += ACTION_COSTS.get("MeetWithFaction", 1)  # refund on failure
        raise HTTPException(status_code=500, detail=str(exc))

    state["faction_id"] = req.faction_id
    session.audience_state = state
    return AudienceBeginResponse(
        faction_id=req.faction_id,
        step1_narrative=state["step1_narrative"],
        action_points=mayor.action_points,
        debug=state.get("debug_begin"),
    )


@router.post("/mayor/audience/reply", response_model=AudienceReplyResponse)
def audience_reply(
    user_id: str,
    req: AudienceReplyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Step 3 — add mayor's opening offer, run faction counter-response."""
    _auth(user_id, current_user)
    session = _get_session(user_id, db)
    if not session.audience_state:
        raise HTTPException(status_code=400, detail="No audience in progress. Call /begin first.")

    from engine.llm.audiences import reply_audience_step, AudienceError
    try:
        updated = reply_audience_step(state=session.audience_state, mayor_opening=req.mayor_opening)
    except AudienceError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    session.audience_state = updated
    return AudienceReplyResponse(
        step3_narrative=updated["step3_narrative"],
        debug=updated.get("debug_reply"),
    )


@router.post("/mayor/audience/conclude", response_model=AudienceConcludeResponse)
def audience_conclude(
    user_id: str,
    req: AudienceConcludeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Step 5 — add mayor's closing, run faction conclusion + deal resolution."""
    _auth(user_id, current_user)
    session = _get_session(user_id, db)
    if not session.audience_state:
        raise HTTPException(status_code=400, detail="No audience in progress. Call /begin first.")

    state = session.audience_state
    faction_id = state.get("faction_id", "")
    faction = (session.factions or {}).get(faction_id)
    if faction is None:
        raise HTTPException(status_code=404, detail=f"Faction {faction_id} not found")

    from engine.llm.audiences import conclude_audience_step, AudienceError, _term_to_dict
    try:
        result = conclude_audience_step(
            state=state,
            mayor_closing=req.mayor_closing,
            faction=faction,
            mayor=session.mayor,
            run_id=session.run_id,
            cycle=session.world.cycle,
            db=db,
        )
    except AudienceError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    # Faction declined → already finalised (memory + cooldown set in the engine); clear state.
    # Faction accepted → keep state for the Mayor's confirmation via /finalize.
    if result.finalized:
        log_audience(state, faction, session.run_id, session.world.cycle,
                     outcome="faction_declined")
        session.audience_state = None

    return AudienceConcludeResponse(
        step1_narrative=result.step1_narrative,
        step3_narrative=result.step3_narrative,
        step5_narrative=result.step5_narrative,
        accepted=result.accepted,
        finalized=result.finalized,
        proposed_mayor_terms=[_term_to_dict(t) for t in result.mayor_terms],
        proposed_faction_terms=[_term_to_dict(t) for t in result.faction_terms],
        deal_id=result.deal_id,
        memory_note=result.memory_note,
        parse_error=result.parse_error,
        action_points=session.mayor.action_points,
        debug=state.get("debug_conclude"),
    )


@router.post("/mayor/audience/finalize", response_model=AudienceFinalizeResponse)
def audience_finalize(
    user_id: str,
    req: AudienceFinalizeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mayor confirmation — seal or discard a faction-accepted deal."""
    _auth(user_id, current_user)
    session = _get_session(user_id, db)
    state = session.audience_state
    if not state or not state.get("pending_parsed"):
        raise HTTPException(status_code=400, detail="No audience awaiting confirmation.")

    faction_id = state.get("faction_id", "")
    faction = (session.factions or {}).get(faction_id)
    if faction is None:
        raise HTTPException(status_code=404, detail=f"Faction {faction_id} not found")

    from engine.llm.audiences import finalize_audience, AudienceError
    try:
        result = finalize_audience(
            state=state,
            mayor_accepts=req.mayor_accepts,
            faction=faction,
            mayor=session.mayor,
            run_id=session.run_id,
            cycle=session.world.cycle,
            db=db,
        )
    except AudienceError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    log_audience(state, faction, session.run_id, session.world.cycle,
                 outcome=("accepted_confirmed" if req.mayor_accepts else "accepted_mayor_declined"))
    session.audience_state = None

    return AudienceFinalizeResponse(
        accepted=result.accepted,
        deal_id=result.deal_id,
        memory_note=result.memory_note,
        action_points=session.mayor.action_points,
    )


# ── Projects ──────────────────────────────────────────────────────────────────

@router.get("/projects", response_model=list[BaseStackResponse])
def list_projects(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _auth(user_id, current_user)
    session = _get_session(user_id, db)
    stacks = session.base_stacks or {}
    return [
        BaseStackResponse(
            name=s.name, domain=s.domain, domains=list(s.domains),
            count=s.count, completed=s.completed, progress=s.progress,
            build_step=s.build_step, initiated_by=s.initiated_by,
        )
        for s in stacks.values()
    ]


@router.get("/projects/catalog", response_model=list[ProjectResponse])
def projects_catalog(
    user_id: str,
    current_user: User = Depends(get_current_user),
):
    """Return all projects from the catalog (not session-specific)."""
    _auth(user_id, current_user)
    catalog = _get_catalog()
    return [
        ProjectResponse(
            id=p.id, name=p.name, domain=p.domain, category=p.category,
            status=p.status, health=p.health, build_progress=p.build_progress,
            build_cost=p.build_cost,
            build_time=p.build_time, faction_build_actions=p.faction_build_actions,
            cycles_built=p.cycles_built, maintenance_cost=p.maintenance_cost,
            tax_level=p.tax_level, initiated_by=p.initiated_by,
        )
        for p in catalog.values()
    ]


# Project building is now driven by the BuildProject mayor action (see mayor_act,
# context-aware initiate/fund/repair). The old catalog-deepcopy + build_cost
# /projects/commission endpoint was retired with the projects rework.
