"""
api/schemas.py — Pydantic request and response models.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    description: str = ""


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Users ─────────────────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    user_id: str
    username: str
    description: str
    is_gm: bool

    model_config = {"from_attributes": True}


# ── Cities ────────────────────────────────────────────────────────────────────

class CityResponse(BaseModel):
    city_id: str
    city_name: str
    author: str
    description: str
    setting: str
    is_official: bool
    published: bool
    owner_id: Optional[str] = None
    faction_count: int = 0
    factions_json: Optional[str] = None

    model_config = {"from_attributes": True}


class CityLoadRequest(BaseModel):
    city_id: str


# ── Sim ───────────────────────────────────────────────────────────────────────

class SimStatusResponse(BaseModel):
    run_id: str
    current_cycle: int
    status: str
    city_name: str = ""
    description: str = ""
    llm_profile_id: Optional[str] = None
    difficulty: str = "normal"
    end_cause: str = ""           # why a finished run ended (fail-states_spec); "" while running


class SimStartRequest(BaseModel):
    llm_profile_id: Optional[str] = None   # None = stub mode
    player_name: Optional[str] = None      # None/blank → "Kallisto"
    player_title: Optional[str] = None     # None/blank → "Prytanis"
    difficulty: Optional[str] = None       # None/unknown → "normal" (see engine/balance.py)


class SimPatchRequest(BaseModel):
    city_name: Optional[str] = None
    description: Optional[str] = None


class SimRunDetail(BaseModel):
    run_id: str
    city_id: str
    city_name: str
    current_cycle: int
    status: str
    updated_at: str


class SimStepResponse(BaseModel):
    cycle: int
    events_count: int
    dramatic_count: int
    game_over: bool = False       # the run ended this step (fail-states_spec)
    end_cause: str = ""


class SimRunResponse(BaseModel):
    cycles_run: int
    final_cycle: int
    stopped_early: bool
    stop_reason: Optional[str] = None


# ── City Create / Patch ───────────────────────────────────────────────────────

class CityNewRequest(BaseModel):
    city_name: str
    description: str = ""
    setting: str = "DnD"
    details: str = ""
    mode: str = "gm"


class CityPatchRequest(BaseModel):
    city_name: Optional[str] = None
    description: Optional[str] = None
    setting: Optional[str] = None
    details: Optional[str] = None


# ── City Builder — Factions ───────────────────────────────────────────────────

class FactionCreateRequest(BaseModel):
    name: str
    domain_primary: str
    rating: int = 1
    traits: List[str] = []
    description: str = ""


class FactionPatchRequest(BaseModel):
    name: Optional[str] = None
    domain_primary: Optional[str] = None
    rating: Optional[int] = None
    traits: Optional[List[str]] = None
    description: Optional[str] = None


# ── City Builder — Units ──────────────────────────────────────────────────────

class DomainRatingIn(BaseModel):
    domain_id: str
    rating: float


class UnitCreateRequest(BaseModel):
    name: str
    domains: List[DomainRatingIn]
    traits: List[str] = []
    description: str = ""
    is_npc: bool = True
    edge: int = 10
    grit: int = 10
    health: int = 75
    faction_id: Optional[str] = None


class UnitPatchRequest(BaseModel):
    name: Optional[str] = None
    health: Optional[int] = None
    traits: Optional[List[str]] = None
    edge: Optional[int] = None
    grit: Optional[int] = None
    description: Optional[str] = None
    is_npc: Optional[bool] = None
    domains: Optional[List[DomainRatingIn]] = None
    faction_id: Optional[str] = None


# ── State ─────────────────────────────────────────────────────────────────────

class CycleSnapshotMeta(BaseModel):
    cycle_number: int
    snapshot_id: str

    model_config = {"from_attributes": True}


# ── Events ────────────────────────────────────────────────────────────────────

class EventTriggerRequest(BaseModel):
    event_name: str
    target_id: Optional[str] = None
    domain: Optional[str] = None


# ── Treasury ─────────────────────────────────────────────────────────────────

class TreasuryResponse(BaseModel):
    gold: int
    domain_tax_rates: Dict[str, float]
    debt: int
    debt_rate: float
    invested: int
    invest_cycles_remaining: int
    invest_return_rate: float
    income_this_cycle: int
    expenditure_this_cycle: int
    max_tax_rate: float


class TaxRateRequest(BaseModel):
    domain_id: str
    rate: float


class BorrowRequest(BaseModel):
    amount: int


class InvestRequest(BaseModel):
    amount: int
    term: int  # 3, 6, or 12


class PublicWorksRequest(BaseModel):
    pass


# ── Mayor ─────────────────────────────────────────────────────────────────────

class MayorResponse(BaseModel):
    action_points: int
    action_cap: int
    reputation: Dict[str, int]
    cooldowns: Dict[str, int]
    exemptions: Dict[str, int]
    committed_actions: List[dict]
    deals: Dict[str, dict] = {}


class ExemptFactionRequest(BaseModel):
    faction_id: str
    cycles: int  # 1–10


VALID_MAYOR_ACTIONS = {
    "MeetWithFaction", "PubliclyEndorse", "PubliclyCondemn",
    "GrantTaxExemption", "Sabotage", "BuildProject", "BreakADeal",
}


class MayorActRequest(BaseModel):
    action: str
    target_id: str = ""      # faction_id or domain_id
    target_id_2: str = ""    # second target for BrokerADeal / PlantARumor
    cycles: int = 5          # for GrantTaxExemption (1–10)


class MayorActResponse(BaseModel):
    action: str
    outcome: str             # "decisive" | "partial" | "fail" | "no_op"
    narrative: str
    action_points: int       # remaining AP after action
    dramatic: bool = False


class AudienceDebug(BaseModel):
    system: str
    messages: list[dict]
    raw_response: str


class AudienceBeginRequest(BaseModel):
    faction_id: str


class AudienceBeginResponse(BaseModel):
    faction_id: str
    step1_narrative: str
    action_points: int
    debug: Optional[AudienceDebug] = None


class AudienceReplyRequest(BaseModel):
    mayor_opening: str


class AudienceReplyResponse(BaseModel):
    step3_narrative: str
    debug: Optional[AudienceDebug] = None


class AudienceConcludeRequest(BaseModel):
    mayor_closing: str


class AudienceConcludeResponse(BaseModel):
    step1_narrative: str
    step3_narrative: str
    step5_narrative: str
    accepted: bool
    finalized: bool = True
    proposed_mayor_terms: list[dict] = []
    proposed_faction_terms: list[dict] = []
    deal_id: Optional[str] = None
    memory_note: str = ""
    parse_error: str = ""
    action_points: int
    debug: Optional[AudienceDebug] = None


class AudienceFinalizeRequest(BaseModel):
    mayor_accepts: bool


class AudienceFinalizeResponse(BaseModel):
    accepted: bool
    deal_id: Optional[str] = None
    memory_note: str = ""
    action_points: int


class SimSetProfileRequest(BaseModel):
    llm_profile_id: Optional[str] = None


# ── Projects ─────────────────────────────────────────────────────────────────

class ProjectResponse(BaseModel):
    id: str
    name: str
    domain: str
    category: str
    status: str
    health: int
    build_progress: int
    build_cost: int
    build_time: int
    faction_build_actions: int
    cycles_built: int
    maintenance_cost: int
    tax_level: int
    initiated_by: str


class BaseStackResponse(BaseModel):
    """A domain's base-project stack (projects_spec v6). The /projects list returns one
    of these per domain; the frontend derives the pool/front view from count/completed/progress."""
    name: str
    domain: str
    domains: List[str]
    count: int
    completed: bool
    progress: float
    build_step: int
    initiated_by: str


