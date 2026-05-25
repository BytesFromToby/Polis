# Decision: Multi-Domain Health Penalty Fix + Domain Cap

**Date:** 2026-04-03
**Status:** Accepted

## Context

The multi-domain health penalty in `end_of_cycle.py` uses `len(unit.domains)` — the number of domain *ratings* a unit has. This is wrong. Generated units can have ratings in 2–3 domains without ever acting in more than one per cycle, causing spurious -5 to -10 HP/cycle drain. After 20 cycles most named units were at hp=1.

The design intent (from `2026-03-31-action-economy-rework.md`) is that the penalty fires for domains a unit **actively uses** each cycle, not for domains they merely have ratings in.

Additionally, the health-based domain cap from the same doc was never implemented.

## Decision

### 1. Penalty uses active domains

Count unique domains a unit actually acted in during the cycle (from their resolved NPCPlans). Apply `(active_domain_count - 1) * 5` penalty instead of `(len(unit.domains) - 1) * 5`.

Since all NPC action selection currently assigns plans to primary domain only, active domain count will be 1 for all units — no penalty fires until multi-domain action selection is actually implemented.

### 2. Health-based domain cap

In `select_npc_actions()`, after building plans, enforce:
- `unit.health >= 50` → all domains allowed
- `25 <= unit.health < 50` → cap at 2 active domains
- `unit.health < 25` → cap at 1 active domain (primary only)

Plans in excess of the cap are dropped, keeping the highest-weight actions in the primary domain.

## Rationale

The penalty misfired because it checked domain ownership rather than domain activity. Fixing it to reflect actual use is correct and consistent with the design. The health cap gives weakening units a natural retreat path — they consolidate into their primary domain as they decline.

## Consequences

- Units with multiple domain ratings no longer take spurious HP drain
- Health crash after 20 cycles should be resolved
- Multi-domain penalty will fire correctly once multi-domain action selection is implemented
- Health cap is in place and ready for that feature
