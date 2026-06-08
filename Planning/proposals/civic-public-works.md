# Proposal: Civic Public Works (deferred)

**Status:** Deferred — future feature (shelved 2026-06-08). Not built.

## Idea
Let factions (not just the Mayor) contribute construction to the faction-less `civic`
domain's **Tax Office** stack — both autonomously (a small weight) and via a Mayor audience
deal (`committed_action: BuildProject → civic`). Intent: make the treasury income lever
reachable without the Mayor having to fund every Tax Office himself.

## Why it's deferred
Prototyped and probed; the autonomous side has **no equilibrium**. A flat per-turn civic-build
chance makes Tax Offices accumulate without bound — insolvency never damages civic (by design),
and nothing tells factions to stop once the city is solvent, so income runs away. A 200-cycle
headless probe (passive Mayor) showed:

| `CIVIC_BUILD_WEIGHT` | Tax Offices @200 | income/cycle @200 | gold @200 |
|---|---|---|---|
| 12 | 50 | 1000 | 68,680 |
| 3  | 13 | 280  | 19,528 |
| 1  | 4  | 100  | 1,946 (still trending up) |

Lowering the weight only slows the runaway; it never stabilises. So the feature needs a
**brake** before it's viable.

## What a future version needs
A self-limiting trigger so civic building tapers when the city doesn't need it. Candidates:
- **Need-based** (preferred): factions only do civic public works when the treasury is low
  (e.g. gold below a threshold / recently insolvent) — a relief valve, naturally bounded.
- **Soft cap** on Tax Office count (diminishing/stop building past a small N).
- Tie civic building to a faction trait (e.g. `industrious`) plus a need gate.

The Mayor-negotiated deal path (`committed_action: BuildProject → civic`) is the less risky
half and could ship independently — it's player-gated, so no runaway.

## Current decision (what ships instead)
Factions **cannot** build the Tax Office. The civic domain and Tax Office remain
**Mayor-only** (treasury_spec v3): the player must spend actions/gold to build Tax Offices to
keep the city solvent. That is the intended player challenge for the demo.

## Prototype evidence
Probe script kept at `output/inspect/drive_civic_balance.py` (the table above).
The prototype code (resolver exception, autonomous `CIVIC_BUILD_WEIGHT`, committed-target
path) was reverted; see git history around 2026-06-08 if resurrecting.
