"""
api/routes/llm_profiles.py — LLM profile CRUD + connection test.

GET    /llm-profiles                List all profiles (api_key never returned)
POST   /llm-profiles                Create a profile
PUT    /llm-profiles/{profile_id}   Update a profile
DELETE /llm-profiles/{profile_id}   Delete a profile
POST   /llm-profiles/{profile_id}/test  Test the connection
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.deps import get_current_user
from db.models import LLMProfile, User
from db.session import get_db
from engine.llm.crypto import decrypt_api_key, encrypt_api_key

router = APIRouter(tags=["llm-profiles"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class LLMProfileCreate(BaseModel):
    name: str
    provider: str                           # "anthropic" | "openai_compat"
    model: str
    api_key: str = ""                       # plaintext; empty for local models
    base_url: str = ""
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(default=500, ge=1)
    timeout: int = Field(default=30, ge=1)


class LLMProfileUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None           # None = keep existing
    base_url: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    timeout: Optional[int] = Field(default=None, ge=1)


class LLMProfileResponse(BaseModel):
    profile_id: str
    name: str
    provider: str
    model: str
    has_api_key: bool
    base_url: str
    temperature: float
    max_tokens: int
    timeout: int


def _to_response(p: LLMProfile) -> LLMProfileResponse:
    return LLMProfileResponse(
        profile_id=p.profile_id,
        name=p.name,
        provider=p.provider,
        model=p.model,
        has_api_key=bool(p.encrypted_api_key),
        base_url=p.base_url,
        temperature=p.temperature,
        max_tokens=p.max_tokens,
        timeout=p.timeout,
    )


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/llm-profiles", response_model=List[LLMProfileResponse])
def list_profiles(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    profiles = db.query(LLMProfile).order_by(LLMProfile.created_at).all()
    return [_to_response(p) for p in profiles]


@router.post("/llm-profiles", response_model=LLMProfileResponse, status_code=201)
def create_profile(
    body: LLMProfileCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    if db.query(LLMProfile).filter(LLMProfile.name == body.name).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Profile name already exists")
    profile = LLMProfile(
        name=body.name,
        provider=body.provider,
        model=body.model,
        encrypted_api_key=encrypt_api_key(body.api_key) if body.api_key else "",
        base_url=body.base_url,
        temperature=body.temperature,
        max_tokens=body.max_tokens,
        timeout=body.timeout,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return _to_response(profile)


@router.put("/llm-profiles/{profile_id}", response_model=LLMProfileResponse)
def update_profile(
    profile_id: str,
    body: LLMProfileUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    profile = db.query(LLMProfile).filter(LLMProfile.profile_id == profile_id).first()
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    if body.name is not None:
        existing = db.query(LLMProfile).filter(
            LLMProfile.name == body.name,
            LLMProfile.profile_id != profile_id,
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Profile name already exists")
        profile.name = body.name

    if body.provider is not None:
        profile.provider = body.provider
    if body.model is not None:
        profile.model = body.model
    if body.api_key is not None:
        profile.encrypted_api_key = encrypt_api_key(body.api_key) if body.api_key else ""
    if body.base_url is not None:
        profile.base_url = body.base_url
    if body.temperature is not None:
        profile.temperature = body.temperature
    if body.max_tokens is not None:
        profile.max_tokens = body.max_tokens
    if body.timeout is not None:
        profile.timeout = body.timeout

    db.commit()
    db.refresh(profile)
    return _to_response(profile)


@router.delete("/llm-profiles/{profile_id}", status_code=204)
def delete_profile(
    profile_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    profile = db.query(LLMProfile).filter(LLMProfile.profile_id == profile_id).first()
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    db.delete(profile)
    db.commit()


@router.post("/llm-profiles/{profile_id}/test")
def test_profile(
    profile_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    profile = db.query(LLMProfile).filter(LLMProfile.profile_id == profile_id).first()
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    from engine.llm.client import LLMClient, LLMConfig, LLMError
    try:
        config = LLMConfig.from_profile(profile)
        client = LLMClient(config)
        response = client.complete(
            system="You are a test assistant. Reply with exactly: ok",
            messages=[{"role": "user", "content": "ping"}],
        )
        return {"ok": True, "response": response[:100]}
    except LLMError as exc:
        return {"ok": False, "error": str(exc)}
    except Exception as exc:
        return {"ok": False, "error": f"Unexpected error: {exc}"}
