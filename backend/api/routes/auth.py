"""
api/routes/auth.py — Registration and login.

POST /auth/register
POST /auth/login
POST /auth/logout  (client-side token drop; stub)
POST /auth/guest   (create or login as local guest user — no credentials needed)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.auth import create_access_token, hash_password, verify_password
from api.schemas import LoginRequest, RegisterRequest, TokenResponse
from db.models import User
from db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )
    user = User(
        username=req.username,
        email=req.email,
        password_hash=hash_password(req.password),
        description=req.description,
        is_gm=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.user_id, user.username)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    token = create_access_token(user.user_id, user.username)
    return TokenResponse(access_token=token)


@router.post("/logout")
def logout():
    # Tokens are stateless JWTs — client drops the token on logout.
    return {"detail": "Logged out"}


_GUEST_USERNAME = "guest"
_GUEST_PASSWORD = "guest-local-only"


@router.post("/guest", response_model=TokenResponse)
def guest_login(db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == _GUEST_USERNAME).first()
    if user is None:
        user = User(
            username=_GUEST_USERNAME,
            email="guest@localhost",
            password_hash=hash_password(_GUEST_PASSWORD),
            is_gm=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    token = create_access_token(user.user_id, user.username)
    return TokenResponse(access_token=token)
