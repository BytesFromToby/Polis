"""
api/routes/cities.py — City template endpoints.

GET  /cities                         List available templates
GET  /cities/{city_id}               Get a template
POST /users/{user_id}/city/publish   Publish user's active city as a template
"""
from __future__ import annotations
import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from api.deps import get_current_user
from api.schemas import CityResponse
from api.sessions import require_session
from db.models import City, User, SimRun
from db.session import get_db
from serializer import serialize_state

router = APIRouter(tags=["cities"])


def _with_counts(city: City) -> CityResponse:
    """Build a CityResponse with a faction count from the JSON blob."""
    try:
        faction_count = len(json.loads(city.factions_json or "{}"))
    except Exception:
        faction_count = 0
    return CityResponse(
        city_id=city.city_id,
        city_name=city.city_name,
        author=city.author,
        description=city.description,
        setting=city.setting,
        is_official=city.is_official,
        published=city.published,
        faction_count=faction_count,
    )


@router.get("/cities", response_model=List[CityResponse])
def list_cities(db: Session = Depends(get_db)):
    cities = db.query(City).filter(
        (City.is_official == True) | (City.published == True)
    ).all()
    return [_with_counts(c) for c in cities]


@router.get("/cities/{city_id}", response_model=CityResponse)
def get_city(city_id: str, db: Session = Depends(get_db)):
    city = db.query(City).filter(City.city_id == city_id).first()
    if city is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="City not found")
    return _with_counts(city)


@router.post("/users/{user_id}/city/publish", response_model=CityResponse)
def publish_city(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    run = db.query(SimRun).filter_by(user_id=user_id).order_by(SimRun.created_at.desc()).first()
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active city to publish")

    city = db.query(City).filter_by(city_id=run.city_id).first()
    if city is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="City not found")

    # If sim has run, snapshot the live session state into a new city template
    try:
        session = require_session(user_id)
        snapshot_data = serialize_state(
            session.world, session.factions, session.domains
        )
        published_city = City(
            city_name=city.city_name,
            author=current_user.username,
            description=city.description,
            setting=city.setting,
            details=city.details,
            is_official=False,
            published=True,
            domains_json=json.dumps({did: d for did, d in snapshot_data["domains"].items()}),
            factions_json=json.dumps({fid: f for fid, f in snapshot_data["factions"].items()}),
            world_state_json=json.dumps(snapshot_data["world"]),
        )
    except ValueError:
        # No live session — publish from city template directly
        published_city = City(
            city_name=city.city_name,
            author=current_user.username,
            description=city.description,
            setting=city.setting,
            details=city.details,
            is_official=False,
            published=True,
            domains_json=city.domains_json,
            factions_json=city.factions_json,
            world_state_json=city.world_state_json,
        )

    db.add(published_city)
    db.commit()
    db.refresh(published_city)
    return published_city
