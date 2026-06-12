# Decisions: Public Needs (The Barley Run)
Spec: Planning/specs/public-needs_spec.md · Proposal: Planning/proposals/barley-run.md
Date: 2026-06-12

- **Public needs replace supply gauges.** The resource-chains "gauge" entities were dropped;
  the gauges *are* `ThePublic.fed/happy/health`. One fewer concept, and shortage pressure
  lands directly on the entity that already carries support/disposition.
- **Wine, not beer; Winepressers, not a new Brewers faction.** The discussion's barley → beer
  example mapped onto the existing roster (`winepressers`) — right Greek flavor, zero new
  factions. Mechanics identical (low fed + happy conversion).
- **Capacity-limited split, not pure proportional.** Processors take raw in proportion to
  capacity but never beyond it (`CAPACITY_PER_LEVEL × level`). Pure proportional was rejected
  because it breaks the design intuition that a level-2 Ovenmen can feed 3,000 but not 30,000.
- **Supply parity targets the Fed/Well-fed boundary (75), not 100.** Exactly meeting demand
  should read "Fed," with surplus required for "Well fed" — `fed_target = min(100, 75 × supply/demand)`.
- **Traits drift (max `DRIFT_STEP`/cycle) instead of snapping to target.** The drift is the
  granary: one bad cycle dents, only sustained shortage starves. This also justifies storing
  the traits without violating the no-persistent-derived-fields decision — drifted values
  have memory.
- **Toil = cycle-only flag consumed by the needs step.** Toil resolves in the action loop but
  production derives at end-of-cycle, so the action just sets `faction.toiling`; the needs
  step applies ×1.5. Rejected: immediate resolution effects (nothing to apply to yet).
- **Needs step is orchestration item 5b — after state updates, before events.** So a cycle
  that starves the city can roll a Starving-gated event the same cycle. Placing it inside the
  existing Public processing (item 11) was rejected for the one-cycle gating lag.
- **"Drunk" is an additional descriptor, not a replacement happy band** — "Well fed, drunk,
  Miserable" must be expressible (per design discussion).
- **`reference/formulas.md` and `reference/architecture.md` updates deferred to build
  completion.** Reference tier is as-built truth; the spec owns the numbers until the
  engine does. (Deviation from the proposal's Spec Impact list, which named formulas.md.)
- All constants (`HARVEST_PER_LEVEL=3`, `CAPACITY_PER_LEVEL=6`, `TOIL_MULT=1.5`,
  conversion profiles, `DRIFT_STEP=10`, parity 75, `BASE_HAPPY=30`, `DRUNK_THRESHOLD=0.25`,
  pop ±2%) are **provisional — tune by feel** against the dynamics tests; tests must import
  them, not copy them.
