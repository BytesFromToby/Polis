"""
models.py — All dataclasses for Polis v3.

v3 changes (2026-05-17):
  - Unit removed entirely (DomainRating, FactionSlot, FocusSlot, NPCPlan removed)
  - Leader embedded in Faction
  - FactionTrait added (trait + intensity + optional target)
  - Faction: leader_id, member_ids, level_1_count replaced by leader + traits as FactionTrait list
  - WorldState: sm_attention, sm_state removed
  - Domain: is_sm() removed
  - CycleResult: unit_actions, retirements, new_units removed
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict


# ── Sub-objects ────────────────────────────────────────────────────────────────

@dataclass
class FactionTrait:
    trait: str
    intensity: str = "moderate"      # "slight" | "moderate" | "strong" | "very"
    target_id: Optional[str] = None  # faction_id if relational; None if general


@dataclass
class Leader:
    name: str
    traits: List[str] = field(default_factory=list)
    status: str = "present"          # "present" | "weakened" | "absent"
    personality_notes: List[str] = field(default_factory=list)


@dataclass
class FactionRelationship:
    """Faction-specific relationship override — supersedes domain default."""
    faction_id: str
    trait: str  # "Friend" | "Foe" | "Neutral"


@dataclass
class DomainRelationship:
    """Per-domain relationship. Self-referential entry = intra-domain default."""
    domain_id: str
    trait: str  # "Friend" | "Foe" | "Hide" | "Client" | "Neutral"


# ── Core Entities ─────────────────────────────────────────────────────────────

@dataclass
class Faction:
    id: str
    name: str
    domain_primary: str
    leader: Leader
    rating: float = 1.0
    health: int = 75               # 1-100
    entrench: int = 75             # 1-100; organizational entrenchment
    traits: List[FactionTrait] = field(default_factory=list)
    relationships: List[FactionRelationship] = field(default_factory=list)

    blurb: str = ""                # short gloss (left-panel); from theming.md
    description: str = ""          # full identity line (audience + prompt); from theming.md

    floor: int = -1                # last confirmed level; -1 = auto-init
    active_block_target: str = ""  # faction_id of standing block trap; "" if none

    # Deal commitment fields (persistent — cleared when deal expires/breaks)
    committed_action: str = ""     # action name faction must take each turn; "" if none
    committed_target: str = ""     # target id for committed_action; "" if no target
    committed_deal_id: str = ""    # deal id this commitment comes from
    committed_abstain_action: str = ""   # action faction must not take; "" if none
    committed_abstain_target: str = ""   # target faction id for abstain commitment

    # Cycle-only state (reset each cycle, not persisted)
    action_cancelled: bool = False
    action_downgraded: bool = False
    unstable_stacks: int = 0       # -1 per stack to rolls, max 3

    def __post_init__(self):
        if self.floor == -1:
            self.floor = int(self.rating)

    @property
    def floor_rating(self) -> int:
        return int(self.rating)

    def is_leaderless(self) -> bool:
        return self.leader.status == "absent"

    def get_faction_relationship(self, faction_id: str) -> Optional[str]:
        for r in self.relationships:
            if r.faction_id == faction_id:
                return r.trait
        return None

    def get_trait(self, name: str) -> Optional[FactionTrait]:
        for t in self.traits:
            if t.trait == name and t.target_id is None:
                return t
        return None

    def get_relational_trait(self, name: str, target_id: str) -> Optional[FactionTrait]:
        for t in self.traits:
            if t.trait == name and t.target_id == target_id:
                return t
        return None

    def reset_cycle_state(self):
        self.action_cancelled = False
        self.action_downgraded = False
        self.unstable_stacks = 0


@dataclass
class Domain:
    id: str
    name: str
    cap: int
    utilization: float = 0.0
    drift: float = 0.0
    relationships: List[DomainRelationship] = field(default_factory=list)

    def get_relationship(self, domain_id: str) -> str:
        for r in self.relationships:
            if r.domain_id == domain_id:
                return r.trait
        return "Neutral"

    def intra_domain_default(self) -> str:
        return self.get_relationship(self.id)


@dataclass
class WorldState:
    cycle: int = 0
    chaos: Dict[str, float] = field(default_factory=dict)          # domain_id -> 0.0-10.0
    power_vacuums: List[dict] = field(default_factory=list)         # {domain_id, cycles_remaining}
    initiative_order: List[str] = field(default_factory=list)       # cycle-only; faction ids in turn order


# ── CycleEvent — Formal Output ────────────────────────────────────────────────

@dataclass
class CycleEvent:
    """
    Formal output event produced by every action resolution.
    dramatic: 0=routine, 1=notable, 2=significant, 3=major
    """
    cycle: int
    actor_id: str
    action: str
    target_id: Optional[str] = None
    domain: Optional[str] = None
    narrative: str = ""
    dramatic: int = 0


# ── Internal Result Objects ───────────────────────────────────────────────────

@dataclass
class ActionResult:
    """Internal computation type. Converted to CycleEvent for logging."""
    action: str
    actor_id: str
    target_id: Optional[str]
    outcome: str    # "decisive" | "partial" | "fail" | "blocked" | "no_op"
    margin: int = 0
    delta: float = 0.0
    dramatic: bool = False
    narrative: str = ""
    domain: Optional[str] = None
    roll_attacker: int = 0
    roll_defender: int = 0


@dataclass
class FactionPlan:
    faction_id: str
    action: str
    target_id: Optional[str] = None
    domain: Optional[str] = None
    cancelled: bool = False


@dataclass
class CycleResult:
    cycle: int
    events: List[CycleEvent] = field(default_factory=list)
    faction_actions: int = 0


# ── Projects ─────────────────────────────────────────────────────────────────

@dataclass
class ProjectEffect:
    target: str       # "domain" | "faction" | "treasury" | "world"
    target_id: str    # id of the entity
    field: str        # what is modified (e.g. "drift", "rating", "gold_per_cycle")
    value: float
    condition: str = "always"  # "always" | "active" | "damaged"


@dataclass
class Project:
    id: str
    name: str
    domains: List[str]              # domains this project belongs to (multi-domain supported)
    build_cost: int
    build_time: int
    faction_build_actions: int = 4  # successful faction actions required to complete
    cycles_built: int = 0
    category: str = "standard"       # "standard" | "tax_collection"
    tax_level: int = 0               # 1–5 for tax_collection projects; 0 otherwise
    faction_level: bool = False      # True = effects apply only to initiated_by faction
    status: str = "under_construction"  # "under_construction"|"active"|"damaged"|"critical"|"destroyed"
    health: int = 0  # build progress 0→100 during construction; structural health 0→100 when active
    effects: List[ProjectEffect] = field(default_factory=list)
    maintenance_cost: int = 10
    initiated_by: str = "mayor"     # "mayor" | faction_id; owner for faction_level effects

    # Cycle-only (not persisted)
    build_actions_this_cycle: int = 0

    @property
    def domain(self) -> str:
        """Backwards-compat: first domain in list."""
        return self.domains[0] if self.domains else ""

    def defense_rating(self) -> int:
        """d20 defense modifier for SabotageProject. Health 1-20=1, 21-40=2, ... 81-100=5."""
        return max(1, self.health // 20)

    def defense_bonus(self) -> int:
        """Build actions this cycle grant +1 each, capped at +2."""
        return min(2, self.build_actions_this_cycle)

    def health_tier(self) -> str:
        if self.health >= 51: return "intact"
        if self.health >= 21: return "damaged"
        if self.health >= 1:  return "critical"
        return "destroyed"

    def effect_multiplier(self) -> float:
        tier = self.health_tier()
        if tier == "intact":    return 1.0
        if tier == "damaged":   return 0.5
        if tier == "critical":  return 0.25
        return 0.0


# ── Events ────────────────────────────────────────────────────────────────────

@dataclass
class EventEffect:
    field: str        # "rating" | "health" | "entrench" | "action_weight" | "chaos"
    target_id: str
    value: float
    label: str = ""
    one_time: bool = False   # applied once on activation, not each cycle


@dataclass
class CascadeSpec:
    delay: int
    target_id: str
    effects: List[EventEffect] = field(default_factory=list)


@dataclass
class GameEvent:
    id: str
    name: str
    type: str             # "random" | "scripted" | "mayor_triggered"
    trigger: str
    target_type: str      # "faction" | "domain" | "project" | "world"
    target_id: str
    duration: int
    cycles_remaining: int = 0
    effects: List[EventEffect] = field(default_factory=list)
    cascade: Optional[CascadeSpec] = None
    status: str = "pending"   # "pending"|"active"|"cascading"|"resolved"
    cascade_delay_remaining: int = 0


# ── Special Factions ──────────────────────────────────────────────────────────

@dataclass
class ThePublic:
    support: int = 0           # -50 to +50; mirrors Mayor.reputation["the_public"]
    disposition: str = "neutral"  # "content"|"neutral"|"restless"|"angry"
    traits: List[FactionTrait] = field(default_factory=list)
    health: int = 100

    def derive_disposition(self) -> str:
        if self.support >= 20:   return "content"
        if self.support >= -19:  return "neutral"
        if self.support >= -34:  return "restless"
        return "angry"

    def update_disposition(self) -> None:
        self.disposition = self.derive_disposition()


@dataclass
class ThreatEffect:
    target_type: str   # "domain" | "faction" | "world" | "treasury"
    target_id: str
    field: str
    value: float       # delta per cycle


@dataclass
class ExternalThreat:
    id: str
    name: str
    type: str           # "bandits"|"rival_city"|"foreign_agent"|"plague_vector"
    threat_level: int   # 1-5
    active: bool = True
    duration: int = 0   # 0 = indefinite; >0 = cycles remaining
    effects: List[ThreatEffect] = field(default_factory=list)


# ── Deals ─────────────────────────────────────────────────────────────────────

@dataclass
class DealTerm:
    type: str           # "tax_exemption"|"endorsement"|"budget_allocation"|"committed_action"|"committed_abstain"
    action: str = ""    # action name for committed_action / committed_abstain
    target_id: str = "" # faction/project id for committed_action target or committed_abstain target
    duration: int = 0   # cycles; 1-10


@dataclass
class Deal:
    id: str
    faction_id: str
    mayor_terms: List[DealTerm]
    faction_terms: List[DealTerm]
    cycles_remaining: int
    total_duration: int
    status: str = "active"          # active|fulfilled|broken_by_mayor|broken_by_faction|suspended
    rep_cost_if_broken: int = 20    # mayor reputation penalty if mayor breaks; set by LLM (10-35)
    cycle_created: int = 0
    suspension_streak: int = 0     # consecutive suspended cycles; deal expires fulfilled at 3


# ── Mayor & Treasury ──────────────────────────────────────────────────────────

@dataclass
class Treasury:
    gold: int = 500
    domain_tax_rates: Dict[str, float] = field(default_factory=dict)  # domain_id → rate; missing = 0.20
    debt: int = 0
    debt_rate: float = 0.05
    invested: int = 0
    invest_cycles_remaining: int = 0
    invest_return_rate: float = 0.0

    income_this_cycle: int = 0
    expenditure_this_cycle: int = 0

    TAX_DEFAULT: float = 0.20
    TAX_LEVELS: tuple = (0.00, 0.10, 0.20, 0.30, 0.40, 0.50)

    def get_rate(self, domain_id: str) -> float:
        return self.domain_tax_rates.get(domain_id, self.TAX_DEFAULT)

    def max_tax_rate(self, projects: dict) -> float:
        """Return the highest tax rate unlocked by active tax_collection projects."""
        highest = 0
        for p in projects.values():
            if getattr(p, "category", "standard") == "tax_collection" and p.status == "active":
                highest = max(highest, getattr(p, "tax_level", 0))
        return self.TAX_LEVELS[min(highest, len(self.TAX_LEVELS) - 1)]

    def set_rate(self, domain_id: str, rate: float, projects: dict = None) -> None:
        if rate not in self.TAX_LEVELS:
            raise ValueError(f"Tax rate {rate} not a valid level: {self.TAX_LEVELS}")
        if projects is not None:
            cap = self.max_tax_rate(projects)
            if rate > cap:
                raise ValueError(f"Tax rate {rate} exceeds unlocked maximum {cap}")
        self.domain_tax_rates[domain_id] = rate

    def reset_cycle_totals(self):
        self.income_this_cycle = 0
        self.expenditure_this_cycle = 0


@dataclass
class Mayor:
    action_points: int = 1
    action_cap: int = 6
    # faction_id / "the_public" / "moneylender" -> -50 to +50
    reputation: Dict[str, int] = field(default_factory=dict)
    # active multi-cycle action commitments: {action, cycles_remaining, target_id}
    committed_actions: List[dict] = field(default_factory=list)
    # cooldowns: faction_id -> cycles_until_available (for Meet With Faction)
    cooldowns: Dict[str, int] = field(default_factory=dict)
    # exemptions: faction_id -> cycles_remaining (excluded from tax income)
    exemptions: Dict[str, int] = field(default_factory=dict)
    # deals: deal_id -> Deal (all statuses retained for history within a run)
    deals: Dict[str, "Deal"] = field(default_factory=dict)

    def get_reputation(self, faction_id: str) -> int:
        return self.reputation.get(faction_id, 0)

    def set_reputation(self, faction_id: str, value: int) -> None:
        self.reputation[faction_id] = max(-50, min(50, value))

    def adjust_reputation(self, faction_id: str, delta: int) -> None:
        current = self.get_reputation(faction_id)
        self.set_reputation(faction_id, current + delta)

    def reputation_label(self, faction_id: str) -> str:
        score = self.get_reputation(faction_id)
        if score >= 30:
            return "trusted"
        if score >= 10:
            return "favorable"
        if score >= -9:
            return "neutral"
        if score >= -29:
            return "suspicious"
        return "hostile"

    def refill(self) -> None:
        """Add 1 action point each cycle, capped at action_cap."""
        self.action_points = min(self.action_cap, self.action_points + 1)

    def spend(self, cost: int) -> bool:
        """Spend action points. Returns False if insufficient."""
        if self.action_points < cost:
            return False
        self.action_points -= cost
        return True

    def tick_cooldowns(self) -> None:
        for fid in list(self.cooldowns):
            self.cooldowns[fid] -= 1
            if self.cooldowns[fid] <= 0:
                del self.cooldowns[fid]

    def tick_exemptions(self) -> None:
        for fid in list(self.exemptions):
            self.exemptions[fid] -= 1
            if self.exemptions[fid] <= 0:
                del self.exemptions[fid]

    def grant_exemption(self, faction_id: str, cycles: int) -> bool:
        """Spend 1 AP to grant a faction tax exemption. Returns False if insufficient AP."""
        if not self.spend(1):
            return False
        self.exemptions[faction_id] = max(1, min(cycles, 10))
        return True

    def is_exempt(self, faction_id: str) -> bool:
        return faction_id in self.exemptions

    def tick_commitments(self) -> None:
        for c in self.committed_actions:
            c["cycles_remaining"] -= 1
        self.committed_actions = [c for c in self.committed_actions if c["cycles_remaining"] > 0]


@dataclass
class MayorAction:
    """A single mayor action submitted for this cycle."""
    action: str          # see mayor_spec for valid action names
    target_id: str = ""  # faction_id, domain_id, or "" if not applicable
    cost: int = 1        # action points spent
