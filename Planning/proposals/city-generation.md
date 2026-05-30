# City Generation — Proposal

**Version:** v2
**Date:** 2026-05-17
**Supersedes:** v1 (2026-03-29)
**Status:** PROPOSAL — not built, not scheduled. Cities are currently hand-authored JSON templates
in `backend/data/`. This is a forward-looking design doc for the procedural generation system for
when that changes. Promote via a Spec Impact section when scheduled (see `proposals/README.md`).

Units removed. Leader embedded in Faction. SM domain removed. Starting projects added.

---

## Overview

City generation creates the starting state for a simulation run. Output is three JSON files: `domains.json`, `factions.json`, `world_state.json`.

Generation runs in 5 steps in fixed order.

---

## Step 1 — Initialize Domains

Create all 8 domain records of the canonical ancient-Greek theme (see
`Planning/reference/theming.md`).

**The 8 domains:**

Aristocracy, Guilds, Trade, The Professions, Temples, Military, Academy, Harbor

**For each domain:**

| Field | Value |
|---|---|
| `id` | Kebab-case identifier (e.g. `aristocracy`, `professions`) |
| `name` | Display name |
| `cap` | Random integer 500–1000 |
| `utilization` | 0 |
| `drift` | From the per-domain drift table (defaults to 0.0 until tuned) |
| `relationships` | From static domain relationship arrays (full row to every domain) |

**Drift values:** all domains default to `0.0`; per-domain drift is set during the balancing
pass, not at first generation.

---

## Step 2 — Generate Factions Per Domain

For each domain, generate factions until remaining capacity falls below minimum.

```
for domain in domains:
    remaining_capacity = domain.cap
    while remaining_capacity > minimum_faction_capacity:
        claim_pct = random.uniform(0.25, 0.75)
        target_weight = remaining_capacity * claim_pct
        faction_rating = reverse_lookup(target_weight)

        if floor(faction_rating) < 3:
            break

        faction = Faction(
            id=generate_id(),
            name=generate_faction_name(domain),
            domain_primary=domain.id,
            rating=faction_rating,
            health=random.uniform(70, 100),
            entrench=75,
            leader=None,          # assigned in step 3
            leadership_need=0.0,
            traits=[],             # assigned in step 3
            relationships=[]
        )

        remaining_capacity -= faction_weight(floor(faction_rating))
```

Minimum faction capacity: floor 3 weight. Factions below floor 3 are not generated.

---

## Step 3 — Assign Leaders and Traits

For each faction:

**Leader generation:**

```python
leader = Leader(
    name=generate_name(),
    traits=random_leader_traits(count=random.choice([1, 2, 3])),
    status="present",
    personality_notes=[]
)
faction.leader = leader
```

**Faction trait generation:**

Each faction gets 2–4 starting traits from the trait list. Traits start at `moderate` intensity. No relational traits at generation — those emerge during play.

Trait count distribution: 2 traits: 40%, 3 traits: 40%, 4 traits: 20%.

Available starting traits: `aggressive`, `defensive`, `ambitious`, `paranoid`, `opportunistic`, `expansionary`, `conservative`, `corrupt`.

---

## Step 4 — Initialize World State

```python
WorldState(
    cycle=0,
    chaos={domain.id: 0.0 for domain in domains},
    power_vacuums=[]
)
```

---

## Step 5 — Starting Projects (City Infrastructure)

Each city begins with a set of pre-built projects that define its baseline stats. These are defined in the city template, not randomly generated.

**Example starting projects for Polis:**

| Project | Effect |
|---|---|
| The Agora | Trade capacity baseline |
| City Walls | Safety baseline |
| The Acropolis Temple | Temples domain bonus |
| The Harbor Mole | Harbor capacity baseline |

Projects are stored in `projects.json`. See `projects_spec.md` (forthcoming) for full structure.

At generation, starting projects are loaded and their effects applied to world state and domain modifiers.

---

## Summary: Generation Output

After city generation:

- All 8 domains exist with caps, drift, and relationships
- At least one faction per domain (usually 2–5)
- Every faction has a leader and 2–4 personality traits
- No relational traits at start — emerge during play
- WorldState at cycle 0, all-zero chaos, no vacuums
- No units file — units are gone
