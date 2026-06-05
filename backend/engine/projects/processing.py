"""
Project processing — construction, effects, health, destruction.
"""
import random
from typing import Dict, List, Optional
from engine.models import Project, ProjectEffect, Faction, Domain, Treasury, Mayor, ActionResult


# ── Construction ──────────────────────────────────────────────────────────────

def tick_projects(
    projects: Dict[str, Project],
    factions: Dict[str, Faction],
    domains: Dict[str, Domain],
    treasury: Treasury,
    logger=None,
) -> List[ActionResult]:
    """Advance all projects one cycle. Returns results for logging."""
    results = []
    for pid, project in list(projects.items()):
        if project.status == "under_construction":
            results.extend(_tick_construction(project, factions, domains, logger))
        elif project.status in ("active", "damaged"):
            results.extend(_tick_active(project, treasury, logger))
        elif project.status == "critical":
            project.health = max(0, project.health - 5)
            if project.health == 0:
                project.status = "destroyed"
                results.append(ActionResult(
                    action="ProjectDestroyed", actor_id=project.id, target_id=None,
                    outcome="decisive", dramatic=True,
                    narrative=f"{project.name} has collapsed and been destroyed",
                ))
        # Per-cycle build counter resets after ticking (it only grants defense for the
        # cycle in which the builds happened — see cycle-runner_spec Break Resolution / §3).
        project.build_actions_this_cycle = 0
    return results


def _tick_construction(
    project: Project,
    factions: Dict[str, Faction],
    domains: Dict[str, Domain],
    logger=None,
) -> List[ActionResult]:
    results = []
    project.cycles_built += 1
    if project.health >= 100 or project.cycles_built >= project.build_time:
        project.status = "active"
        project.health = 100
        results.append(ActionResult(
            action="ProjectComplete", actor_id=project.id, target_id=None,
            outcome="decisive", dramatic=True,
            narrative=f"{project.name} construction complete — now active",
        ))
    return results


def _tick_active(
    project: Project,
    treasury: Treasury,
    logger=None,
) -> List[ActionResult]:
    results = []
    # Maintenance already deducted in treasury step 0; here we check if it was skipped
    # Health decay for critical status
    if project.status == "damaged" and project.health <= 20:
        project.status = "critical"
    if project.health <= 0:
        project.status = "destroyed"
        results.append(ActionResult(
            action="ProjectDestroyed", actor_id=project.id, target_id=None,
            outcome="decisive", dramatic=True,
            narrative=f"{project.name} has been destroyed",
        ))
    return results


# ── Active Effects ────────────────────────────────────────────────────────────

def apply_project_effects(
    projects: Dict[str, Project],
    factions: Dict[str, Faction],
    domains: Dict[str, Domain],
    treasury: Treasury,
    mayor_reputation: Optional[Dict[str, int]] = None,
) -> List[ActionResult]:
    """Apply active project effects to world state. Called each cycle after tick_projects."""
    results = []
    for pid, project in projects.items():
        if project.status not in ("active", "damaged", "critical"):
            continue
        mult = project.effect_multiplier()
        if mult == 0:
            continue
        for eff in project.effects:
            if eff.condition == "active" and project.status != "active":
                continue
            if eff.condition == "damaged" and project.status not in ("damaged", "critical"):
                continue
            _apply_single_effect(eff, mult, factions, domains, treasury, mayor_reputation)
    return results


def _apply_single_effect(
    eff: ProjectEffect,
    mult: float,
    factions: Dict[str, Faction],
    domains: Dict[str, Domain],
    treasury: Treasury,
    mayor_reputation: Optional[Dict[str, int]],
) -> None:
    scaled = eff.value * mult

    if eff.target == "domain":
        domain = domains.get(eff.target_id)
        if domain and hasattr(domain, eff.field):
            setattr(domain, eff.field, getattr(domain, eff.field) + scaled)

    elif eff.target == "faction":
        faction = factions.get(eff.target_id)
        if faction and hasattr(faction, eff.field):
            current = getattr(faction, eff.field)
            setattr(faction, eff.field, current + scaled)

    elif eff.target == "treasury":
        if eff.field == "gold_per_cycle":
            treasury.gold += int(scaled)
            treasury.income_this_cycle += int(scaled)

    elif eff.target == "world":
        pass  # world chaos handled by event system


# ── Damage & Repair ───────────────────────────────────────────────────────────

def harm_project(
    project: Project,
    attacker: Faction,
    dc: int = 12,
) -> ActionResult:
    """Faction attacks a project. Returns ActionResult with damage dealt."""
    import random
    roll = random.randint(1, 20) + int(attacker.rating)
    margin = roll - dc

    if margin >= 5:
        damage = 25
        outcome = "decisive"
    elif margin >= 1:
        damage = 10
        outcome = "partial"
    else:
        damage = 0
        outcome = "fail"

    if damage > 0:
        project.health = max(0, project.health - damage)
        _update_project_status(project)

    return ActionResult(
        action="HarmProject",
        actor_id=attacker.id,
        target_id=project.id,
        outcome=outcome,
        margin=margin,
        delta=-float(damage),
        dramatic=(damage >= 25),
        narrative=(
            f"{attacker.name} attacked {project.name}: "
            f"{damage} damage (roll {roll} vs DC {dc}); health now {project.health}"
        ) if damage > 0 else f"{attacker.name} attack on {project.name} failed",
    )


def repair_project(project: Project, treasury: Treasury, mayor: "Mayor") -> ActionResult:
    """Mayor spends 30 gold + 1 action point to restore 25 health."""
    cost_gold = 30
    cost_ap = 1
    if not mayor.spend(cost_ap):
        return ActionResult(
            action="RepairProject", actor_id="mayor", target_id=project.id,
            outcome="fail", narrative="Repair failed: insufficient action points",
        )
    if treasury.gold < cost_gold:
        mayor.action_points += cost_ap  # refund
        return ActionResult(
            action="RepairProject", actor_id="mayor", target_id=project.id,
            outcome="fail", narrative="Repair failed: insufficient gold",
        )
    treasury.gold -= cost_gold
    treasury.expenditure_this_cycle += cost_gold
    project.health = min(100, project.health + 25)
    _update_project_status(project)
    return ActionResult(
        action="RepairProject", actor_id="mayor", target_id=project.id,
        outcome="decisive", delta=-float(cost_gold),
        narrative=f"{project.name} repaired: health now {project.health}",
    )


def _update_project_status(project: Project) -> None:
    if project.health == 0:
        project.status = "destroyed"
    elif project.health <= 20:
        project.status = "critical"
    elif project.health <= 50:
        project.status = "damaged"
    else:
        project.status = "active"


# ── Commission ────────────────────────────────────────────────────────────────

def commission_project(
    project_template: dict,
    treasury: Treasury,
    mayor: "Mayor",
    initiated_by: str = "mayor",
) -> tuple[Optional[Project], ActionResult]:
    """Mayor commissions a new project from a template dict. Returns (project, result)."""
    build_cost = project_template.get("build_cost", 0)
    build_time = project_template.get("build_time", 1)

    # Action point cost by build time
    if build_time <= 2:
        ap_cost = 2
    elif build_time <= 5:
        ap_cost = 1  # per-cycle during construction; pay upfront for first cycle
    else:
        ap_cost = 1  # every other cycle; pay first cycle

    if not mayor.spend(ap_cost):
        return None, ActionResult(
            action="CommissionProject", actor_id="mayor", target_id=project_template.get("id"),
            outcome="fail", narrative="Commission failed: insufficient action points",
        )
    if treasury.gold < build_cost:
        mayor.action_points += ap_cost
        return None, ActionResult(
            action="CommissionProject", actor_id="mayor", target_id=project_template.get("id"),
            outcome="fail", narrative=f"Commission failed: need {build_cost} gold, have {treasury.gold}",
        )

    treasury.gold -= build_cost
    treasury.expenditure_this_cycle += build_cost

    effects = [
        ProjectEffect(**e) for e in project_template.get("effects", [])
    ]
    domains = project_template.get("domains") or [project_template.get("domain", "")]
    project = Project(
        id=project_template["id"],
        name=project_template["name"],
        domains=domains,
        build_cost=build_cost,
        build_time=build_time,
        maintenance_cost=project_template.get("maintenance_cost", 10),
        effects=effects,
        initiated_by=initiated_by,
    )
    return project, ActionResult(
        action="CommissionProject", actor_id="mayor", target_id=project.id,
        outcome="decisive", delta=-float(build_cost),
        narrative=f"Project commissioned: {project.name} ({build_time} cycles to build)",
    )
