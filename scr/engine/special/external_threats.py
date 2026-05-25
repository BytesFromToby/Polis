"""
External Threats — apply per-cycle pressure effects, expire timed threats.
"""
from typing import Dict, List
from engine.models import ExternalThreat, Faction, Domain, WorldState, Treasury, Mayor, ActionResult


def process_external_threats(
    threats: List[ExternalThreat],
    factions: Dict[str, Faction],
    domains: Dict[str, Domain],
    world: WorldState,
    treasury: Treasury,
    mayor: Mayor,
) -> List[ActionResult]:
    """Apply active threat effects and tick durations. Returns results."""
    results = []

    for threat in list(threats):
        if not threat.active:
            continue

        # Apply each effect
        for eff in threat.effects:
            _apply_threat_effect(eff, factions, domains, world, treasury, mayor, threat.threat_level)

        results.append(ActionResult(
            action="ThreatEffect",
            actor_id=threat.id,
            target_id=None,
            outcome="no_op",
            narrative=f"{threat.name} (level {threat.threat_level}) applying pressure",
        ))

        # Tick duration
        if threat.duration > 0:
            threat.duration -= 1
            if threat.duration == 0:
                threat.active = False
                results.append(ActionResult(
                    action="ThreatExpired",
                    actor_id=threat.id,
                    target_id=None,
                    outcome="no_op",
                    narrative=f"{threat.name} has passed",
                ))

    return results


def _apply_threat_effect(
    eff,
    factions: Dict[str, Faction],
    domains: Dict[str, Domain],
    world: WorldState,
    treasury: Treasury,
    mayor: Mayor,
    threat_level: int,
) -> None:
    scaled_value = eff.value * threat_level

    if eff.target_type == "domain":
        if eff.field == "chaos":
            current = world.chaos.get(eff.target_id, 0.0)
            world.chaos[eff.target_id] = max(0.0, min(10.0, current + scaled_value))

    elif eff.target_type == "faction":
        faction = factions.get(eff.target_id)
        if faction:
            if eff.field == "health":
                faction.health = max(0, min(100, faction.health + int(scaled_value)))
            elif eff.field == "entrench":
                faction.entrench = max(0, min(100, faction.entrench + int(scaled_value)))

    elif eff.target_type == "world":
        if eff.field == "chaos":
            for domain_id in world.chaos:
                world.chaos[domain_id] = max(0.0, min(10.0, world.chaos[domain_id] + scaled_value))

    elif eff.target_type == "treasury":
        if eff.field == "gold_per_cycle":
            amount = int(scaled_value)
            treasury.gold = max(0, treasury.gold + amount)
            if amount < 0:
                treasury.expenditure_this_cycle += abs(amount)


def make_bandit_threat(threat_level: int = 2, duration: int = 0) -> ExternalThreat:
    from engine.models import ThreatEffect
    return ExternalThreat(
        id="bandits",
        name="Bandit Activity",
        type="bandits",
        threat_level=threat_level,
        duration=duration,
        effects=[
            ThreatEffect(target_type="domain", target_id="street", field="chaos", value=0.5),
            ThreatEffect(target_type="treasury", target_id="treasury", field="gold_per_cycle", value=-5.0),
        ],
    )


def make_rival_city_threat(threat_level: int = 2, duration: int = 0) -> ExternalThreat:
    from engine.models import ThreatEffect
    return ExternalThreat(
        id="rival_city",
        name="Rival City Pressure",
        type="rival_city",
        threat_level=threat_level,
        duration=duration,
        effects=[
            ThreatEffect(target_type="world", target_id="world", field="chaos", value=0.2),
            ThreatEffect(target_type="treasury", target_id="treasury", field="gold_per_cycle", value=-3.0),
        ],
    )
