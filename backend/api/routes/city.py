"""
api/routes/city.py — User city setup (pre-sim).

POST  /users/{user_id}/city/load              Load from template
POST  /users/{user_id}/city/new               Start blank city
GET   /users/{user_id}/city                   Get current city config
PATCH /users/{user_id}/city                   Edit city settings

POST   /users/{user_id}/city/factions         Add faction
PATCH  /users/{user_id}/city/factions/{id}    Edit faction
DELETE /users/{user_id}/city/factions/{id}    Remove faction
"""
from __future__ import annotations
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_current_user
from api.schemas import (
    CityResponse, CityLoadRequest, CityNewRequest, CityPatchRequest,
    FactionCreateRequest, FactionPatchRequest,
)
from db.models import City, SimRun, User
from db.session import get_db
from engine.models import Faction, FactionTrait, Leader, WorldState
from serializer import serialize_faction, serialize_world_state

router = APIRouter(prefix="/users/{user_id}", tags=["city"])


def _get_setup_run(user_id: str, db: Session) -> SimRun:
    run = db.query(SimRun).filter_by(user_id=user_id, status="setup").order_by(
        SimRun.created_at.desc()
    ).first()
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No city in setup. Use /city/load or /city/new first.",
        )
    return run


def _get_city(run: SimRun, db: Session) -> City:
    city = db.query(City).filter_by(city_id=run.city_id).first()
    if city is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="City not found")
    return city


# ── City Setup ────────────────────────────────────────────────────────────────

@router.post("/city/load", response_model=CityResponse)
def load_city(
    user_id: str,
    req: CityLoadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    template = db.query(City).filter_by(city_id=req.city_id).first()
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="City template not found")

    city = City(
        city_name=template.city_name,
        author=current_user.username,
        description=template.description,
        setting=template.setting,
        details=template.details,
        is_official=False,
        published=False,
        owner_id=current_user.user_id,
        domains_json=template.domains_json,
        factions_json=template.factions_json,
        world_state_json=template.world_state_json,
    )
    db.add(city)
    db.flush()

    run = SimRun(
        user_id=user_id,
        city_id=city.city_id,
        status="setup",
        setting=city.setting,
        description=city.description,
        details=city.details,
    )
    db.add(run)
    db.commit()
    db.refresh(city)
    return city


@router.post("/city/new", response_model=CityResponse)
def new_city(
    user_id: str,
    req: CityNewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    blank_world = WorldState(cycle=0, chaos={}, power_vacuums=[])
    city = City(
        city_name=req.city_name,
        author=current_user.username,
        description=req.description,
        setting=req.setting,
        details=req.details,
        is_official=False,
        published=False,
        owner_id=current_user.user_id,
        domains_json="{}",
        factions_json="{}",
        world_state_json=json.dumps(serialize_world_state(blank_world)),
    )
    db.add(city)
    db.flush()

    run = SimRun(
        user_id=user_id,
        city_id=city.city_id,
        status="setup",
        setting=req.setting,
        description=req.description,
        details=req.details,
    )
    db.add(run)
    db.commit()
    db.refresh(city)
    return city


@router.get("/city", response_model=CityResponse)
def get_city(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    run = _get_setup_run(user_id, db)
    return _get_city(run, db)


@router.patch("/city", response_model=CityResponse)
def patch_city(
    user_id: str,
    req: CityPatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    run = _get_setup_run(user_id, db)
    city = _get_city(run, db)

    if req.city_name is not None:
        city.city_name = req.city_name
    if req.description is not None:
        city.description = req.description
    if req.setting is not None:
        city.setting = req.setting
    if req.details is not None:
        city.details = req.details

    db.commit()
    db.refresh(city)
    return city


# ── City Builder — Factions ───────────────────────────────────────────────────

@router.post("/city/factions")
def add_faction(
    user_id: str,
    req: FactionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    run = _get_setup_run(user_id, db)
    city = _get_city(run, db)

    factions = json.loads(city.factions_json)
    fid = f"faction_{str(uuid.uuid4())[:8]}"
    new_faction = Faction(
        id=fid,
        name=req.name,
        domain_primary=req.domain_primary,
        leader=Leader(name=f"Leader of {req.name}"),
        rating=req.rating,
        floor=int(req.rating),
        entrench=75,
        health=75,
        traits=[FactionTrait(trait=t) for t in (req.traits or [])],
        relationships=[],
    )
    serialized = serialize_faction(new_faction)
    factions[fid] = serialized
    city.factions_json = json.dumps(factions)
    db.commit()
    return factions[fid]


@router.patch("/city/factions/{faction_id}")
def patch_faction_setup(
    user_id: str,
    faction_id: str,
    req: FactionPatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    run = _get_setup_run(user_id, db)
    city = _get_city(run, db)

    factions = json.loads(city.factions_json)
    if faction_id not in factions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faction not found")

    f = factions[faction_id]
    if req.name is not None:
        f["name"] = req.name
    if req.domain_primary is not None:
        f["domain_primary"] = req.domain_primary
    if req.rating is not None:
        f["rating"] = req.rating
        f["floor"] = int(req.rating)
    if req.entrench is not None:
        f["entrench"] = req.entrench

    city.factions_json = json.dumps(factions)
    db.commit()
    return f


@router.delete("/city/factions/{faction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_faction_setup(
    user_id: str,
    faction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    run = _get_setup_run(user_id, db)
    city = _get_city(run, db)

    factions = json.loads(city.factions_json)
    if faction_id not in factions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faction not found")
    del factions[faction_id]
    city.factions_json = json.dumps(factions)
    db.commit()
