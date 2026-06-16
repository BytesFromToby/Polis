"""
engine/needs/chain.py — the Food production chains (food-supply_spec).

A pure function from live faction state + population to supply targets.
Derived every cycle, never persisted. All constants are provisional —
tune by feel against tests/test_needs_dynamics.py; tests must import
them, never copy values.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from engine.models import Faction

TOIL_MULT = 1.5              # contribution multiplier while toiling
PARITY_TARGET = 75           # supply == demand sits at the Fed/Well-fed boundary
BASE_HAPPY = 30              # happy target with zero happy supply
DRUNK_THRESHOLD = 0.25       # wine happy contribution per demand ≥ this → drunk
POP_PER_SUPPLY_UNIT = 1000   # 1 supply unit feeds 1000 people


@dataclass
class ChainOutput:
    fed_target: float = 100.0
    happy_target: float = 100.0
    drunk: bool = False
    raw: float = 0.0
    units: Dict[str, float] = field(default_factory=dict)   # label → units processed


def chain_role_faction_ids(chains: List[dict], factions: Dict[str, "Faction"]) -> Set[str]:
    """Faction ids with a chain role: producer-domain members + named processors."""
    ids: Set[str] = set()
    for chain in chains:
        producers = chain.get("producers", {})
        producer_domain = producers.get("domain")
        producer_faction = producers.get("faction_id")
        for fid, f in factions.items():
            if producer_domain and f.domain_primary == producer_domain:
                ids.add(fid)
        if producer_faction and producer_faction in factions:
            ids.add(producer_faction)
        for proc in chain.get("processors", []):
            if proc["faction_id"] in factions:
                ids.add(proc["faction_id"])
    return ids


def compute_chain(
    factions: Dict[str, "Faction"],
    population: int,
    chains: List[dict],
) -> ChainOutput:
    """Pure — reads faction levels and toiling/withholding flags, mutates nothing."""
    fed_supply = 0.0
    happy_supply = 0.0
    wine_happy = 0.0
    total_raw = 0.0
    units: Dict[str, float] = {}

    for chain in chains:
        producers = chain.get("producers", {})
        per_level = producers.get("per_level", 0)
        prod_domain = producers.get("domain")
        prod_faction = producers.get("faction_id")
        raw = 0.0
        for fid, f in factions.items():
            if (prod_domain and f.domain_primary == prod_domain) or (prod_faction and fid == prod_faction):
                contribution = per_level * f.level
                if f.withholding:           # Withhold wins over Toil: zero contribution this cycle
                    contribution = 0.0
                elif f.toiling:
                    contribution *= TOIL_MULT
                raw += contribution
        total_raw += raw

        processors = chain.get("processors", [])
        capacities = []
        for proc in processors:
            f = factions.get(proc["faction_id"])
            cap = proc["per_level_capacity"] * f.level if f else 0.0
            if f and f.withholding:         # Withhold wins over Toil: zero capacity this cycle
                cap = 0.0
            elif f and f.toiling:
                cap *= TOIL_MULT
            capacities.append(cap)
        total_capacity = sum(capacities)

        processed_total = 0.0
        for proc, cap in zip(processors, capacities):
            if total_capacity <= 0 or raw <= 0:
                share = 0.0
            elif total_capacity >= raw:
                share = raw * (cap / total_capacity)
            else:
                share = cap
            processed_total += share
            units[proc["label"]] = units.get(proc["label"], 0.0) + share
            fed_supply += share * proc.get("fed_per_unit", 0.0)
            proc_happy = share * proc.get("happy_per_unit", 0.0)
            happy_supply += proc_happy
            if proc["label"] == "wine":
                wine_happy += proc_happy

        leftover = raw - processed_total
        unprocessed = chain.get("unprocessed", {})
        label = unprocessed.get("label", "porridge")
        units[label] = units.get(label, 0.0) + leftover
        fed_supply += leftover * unprocessed.get("fed_per_unit", 0.0)

    demand = population / POP_PER_SUPPLY_UNIT
    if demand <= 0:
        return ChainOutput(raw=total_raw, units=units)

    fed_target = min(100.0, PARITY_TARGET * fed_supply / demand)
    happy_target = max(0.0, min(100.0, BASE_HAPPY + PARITY_TARGET * happy_supply / demand))
    drunk = (wine_happy / demand) >= DRUNK_THRESHOLD

    return ChainOutput(
        fed_target=fed_target,
        happy_target=happy_target,
        drunk=drunk,
        raw=total_raw,
        units=units,
    )
