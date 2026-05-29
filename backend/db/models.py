"""
db/models.py — SQLAlchemy ORM table definitions.

Tables: users, cities, sim_runs, cycle_snapshots,
        narrative_log, faction_memory, deals, llm_profiles
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer, String, Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id:       Mapped[str]  = mapped_column(String, primary_key=True, default=_uuid)
    username:      Mapped[str]  = mapped_column(String, unique=True, nullable=False)
    email:         Mapped[str | None] = mapped_column(String, nullable=True)
    password_hash: Mapped[str]  = mapped_column(String, nullable=False)
    description:   Mapped[str]  = mapped_column(String, default="")
    is_gm:         Mapped[bool] = mapped_column(Boolean, default=True)

    sim_runs: Mapped[list[SimRun]] = relationship("SimRun", back_populates="user")


class City(Base):
    __tablename__ = "cities"

    city_id:          Mapped[str]  = mapped_column(String, primary_key=True, default=_uuid)
    city_name:        Mapped[str]  = mapped_column(String, nullable=False)
    author:           Mapped[str]  = mapped_column(String, nullable=False)
    description:      Mapped[str]  = mapped_column(String, default="")
    setting:          Mapped[str]  = mapped_column(String, default="DnD")
    details:          Mapped[str]  = mapped_column(String, default="")
    is_official:      Mapped[bool] = mapped_column(Boolean, default=False)
    published:        Mapped[bool] = mapped_column(Boolean, default=False)

    owner_id:         Mapped[str | None] = mapped_column(
        String, ForeignKey("users.user_id"), nullable=True,
    )

    # Serialized engine state blobs
    domains_json:     Mapped[str]  = mapped_column(Text, nullable=False)
    factions_json:    Mapped[str]  = mapped_column(Text, nullable=False)
    world_state_json: Mapped[str]  = mapped_column(Text, nullable=False)

    # LLM provider config — JSON-serialised LLMConfig; null means use server env vars
    llm_config_json:  Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    owner:    Mapped[User | None]  = relationship("User", foreign_keys=[owner_id])
    sim_runs: Mapped[list[SimRun]] = relationship("SimRun", back_populates="city")


class SimRun(Base):
    __tablename__ = "sim_runs"

    run_id:        Mapped[str]  = mapped_column(String, primary_key=True, default=_uuid)
    user_id:       Mapped[str]  = mapped_column(String, ForeignKey("users.user_id"), nullable=False)
    city_id:       Mapped[str]  = mapped_column(String, ForeignKey("cities.city_id"), nullable=False)
    current_cycle: Mapped[int]  = mapped_column(Integer, default=0)
    # status values: "setup" | "running" | "paused" | "complete"
    status:        Mapped[str]  = mapped_column(String, default="setup")

    # Carried from the city template at run creation
    setting:     Mapped[str] = mapped_column(String, default="DnD")
    description: Mapped[str] = mapped_column(String, default="")
    details:     Mapped[str] = mapped_column(String, default="")

    # Player identity (set at new-game start; title is a fixed default until the
    # rank-ladder system exists — see reference/theming.md)
    player_name:  Mapped[str] = mapped_column(String, default="Kallisto")
    player_title: Mapped[str] = mapped_column(String, default="Prytanis")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    # LLM profile selected at run creation (null = stub mode)
    llm_profile_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("llm_profiles.profile_id"), nullable=True, default=None,
    )

    user: Mapped[User]            = relationship("User", back_populates="sim_runs")
    city: Mapped[City]            = relationship("City", back_populates="sim_runs")
    llm_profile: Mapped["LLMProfile | None"] = relationship("LLMProfile")
    snapshots: Mapped[list[CycleSnapshot]] = relationship(
        "CycleSnapshot", back_populates="run", order_by="CycleSnapshot.cycle_number"
    )
    narrative:  Mapped[list[NarrativeLog]] = relationship(
        "NarrativeLog", back_populates="run", order_by="NarrativeLog.cycle_number"
    )


class CycleSnapshot(Base):
    __tablename__ = "cycle_snapshots"

    snapshot_id:   Mapped[str]      = mapped_column(String, primary_key=True, default=_uuid)
    run_id:        Mapped[str]      = mapped_column(String, ForeignKey("sim_runs.run_id"), nullable=False)
    cycle_number:  Mapped[int]      = mapped_column(Integer, nullable=False)
    state_json:    Mapped[str]      = mapped_column(Text, nullable=False)
    created_at:    Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    run: Mapped[SimRun] = relationship("SimRun", back_populates="snapshots")


class NarrativeLog(Base):
    __tablename__ = "narrative_log"

    log_id:       Mapped[str]      = mapped_column(String, primary_key=True, default=_uuid)
    run_id:       Mapped[str]      = mapped_column(String, ForeignKey("sim_runs.run_id"), nullable=False)
    cycle_number: Mapped[int]      = mapped_column(Integer, nullable=False)
    events_json:  Mapped[str]      = mapped_column(Text, nullable=False)
    published:    Mapped[bool]     = mapped_column(Boolean, default=True)
    created_at:   Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    run: Mapped[SimRun] = relationship("SimRun", back_populates="narrative")


class FactionMemory(Base):
    __tablename__ = "faction_memory"

    id:         Mapped[str]      = mapped_column(String, primary_key=True, default=_uuid)
    run_id:     Mapped[str]      = mapped_column(String, ForeignKey("sim_runs.run_id"), nullable=False)
    faction_id: Mapped[str]      = mapped_column(String, nullable=False)
    cycle:      Mapped[int]      = mapped_column(Integer, nullable=False)
    note:       Mapped[str]      = mapped_column(String, nullable=False)   # <=10 words
    is_summary: Mapped[bool]     = mapped_column(Boolean, default=False)
    type:       Mapped[str]      = mapped_column(String, nullable=False)   # audience|event|summary
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    run: Mapped[SimRun] = relationship("SimRun")


class LLMProfile(Base):
    __tablename__ = "llm_profiles"

    profile_id:        Mapped[str]      = mapped_column(String, primary_key=True, default=_uuid)
    name:              Mapped[str]      = mapped_column(String, unique=True, nullable=False)
    provider:          Mapped[str]      = mapped_column(String, nullable=False)   # anthropic | openai_compat
    model:             Mapped[str]      = mapped_column(String, nullable=False)
    encrypted_api_key: Mapped[str]      = mapped_column(Text, default="")         # Fernet token; "" for local
    base_url:          Mapped[str]      = mapped_column(String, default="")
    temperature:       Mapped[float]    = mapped_column(Float, default=0.7)
    max_tokens:        Mapped[int]      = mapped_column(Integer, default=500)
    timeout:           Mapped[int]      = mapped_column(Integer, default=30)
    created_at:        Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Deal(Base):
    __tablename__ = "deals"

    deal_id:           Mapped[str]      = mapped_column(String, primary_key=True, default=_uuid)
    run_id:            Mapped[str]      = mapped_column(String, ForeignKey("sim_runs.run_id"), nullable=False)
    faction_id:        Mapped[str]      = mapped_column(String, nullable=False)
    cycle_created:     Mapped[int]      = mapped_column(Integer, nullable=False)
    total_duration:    Mapped[int]      = mapped_column(Integer, nullable=False)
    cycles_remaining:  Mapped[int]      = mapped_column(Integer, nullable=False)
    # active | fulfilled | broken_by_mayor | broken_by_faction | suspended
    status:            Mapped[str]      = mapped_column(String, default="active")
    mayor_terms_json:  Mapped[str]      = mapped_column(Text, nullable=False)   # JSON [DealTerm]
    faction_terms_json: Mapped[str]     = mapped_column(Text, nullable=False)   # JSON [DealTerm]
    rep_cost_if_broken: Mapped[int]     = mapped_column(Integer, default=20)
    suspension_streak: Mapped[int]      = mapped_column(Integer, default=0)
    created_at:        Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at:        Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    run: Mapped[SimRun] = relationship("SimRun")
