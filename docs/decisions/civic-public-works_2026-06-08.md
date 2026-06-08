# Decisions: Civic Public Works — DEFERRED
Proposal: Planning/proposals/civic-public-works.md
Date: 2026-06-08

- **Shelved as a future feature.** Prototyped "any faction can build the civic Tax Office"
  (resolver exception + autonomous CIVIC_BUILD_WEIGHT + committed-target deal path). A
  200-cycle balance probe showed the autonomous side has no equilibrium: Tax Offices
  accumulate without bound (insolvency never damages civic; nothing stops building when the
  city is solvent), so Mayor income runs away. Lowering the weight only slows it (weight 12 →
  50 offices / 68k gold; weight 1 → 4 offices / 2k and still climbing). No flat weight gives
  both solvency and no-runaway.
- **Reverted the prototype code** (engine/actions/faction.py, engine/cycle/resolution.py,
  engine/npc/behavior.py) and removed the spec + blueprint from the active tiers. Design and
  probe evidence preserved in the proposal + `output/inspect/drive_civic_balance.py`.
- **What ships instead:** factions cannot build the Tax Office; the civic domain stays
  Mayor-only (treasury_spec v3). The player must spend actions/gold to build Tax Offices to
  keep the city solvent — the intended demo challenge.
- **A future version needs a brake** before it's viable — a need-based trigger (factions
  pitch in only when the treasury is low) is the preferred self-limiting design. The
  Mayor-negotiated deal path (committed BuildProject → civic) is player-gated and could ship
  on its own without runaway risk.
