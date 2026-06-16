# Spec restructure: split public-needs into public-needs (state) + food-supply (chains)

**Date:** 2026-06-16
**Trigger:** about to build the Public's piety + unrest scales; `public-needs_spec.md` was 313
lines titled "The Barley Run" and tangled two separable concerns. (User call: "split into two
specs," ahead of the piety+unrest build.)

## What

`public-needs_spec.md` (v3) carried both the **Food production chains** (harvest/fishery/pastoral
+ `compute_chain`) and the **Public's needs state** (fed/happy/health scales, bands, drift,
consequences, cycle step). The three chain features were extracted into a new
**`food-supply_spec.md`**; `public-needs_spec.md` (v4) keeps the Public-state side and was
retitled off "The Barley Run."

The seam is the chain's output: `food-supply` computes `fed_target`/`happy_target`; `public-needs`
owns the scales that **drift** toward them.

## Why this division (and not the others)

- **Why keep the `public-needs_spec.md` filename for the state side, not the chains:** the state
  scales are what's actively growing (piety/unrest next), so they keep the stable, well-known name
  (~60 of the 96 repo references cite it for *bands/fed-state*, which stay put); only the
  chain-specific references repoint to the new spec. Lower churn, correct names — "public needs"
  genuinely describes fed/happy/health/piety.
- **Why not move the Public *entity* out of `special-factions_spec.md`:** that spec still owns the
  `ThePublic` dataclass + `support`/`disposition` (the confidence axis). The existing division
  (entity in special-factions, needs-behavior in public-needs) is preserved; we did not create a
  third Public home. `public-needs` references the entity rather than redefining it.
- **Why a real file split, not just a rename:** the user chose it over "keep one spec + rename."
  The food chains are a cohesive, well-bounded cluster (the `engine/needs/` chain code points at
  one spec); the Public-state side is about to roughly double (piety/unrest/consumption). The
  Planning convention predicted paying the link-rewrite cost once, deliberately, for this cluster.

## Behavior

None. Pure documentation + comment restructure; full suite **474 green** unchanged. The only code
touch is `engine/needs/chain.py`'s module docstring (now cites `food-supply_spec`).

## Repointed

Index (`Planning/CLAUDE.md`), `cycle-runner_spec` item 5b, `actions_spec` Toil/Withhold chain-×
cites, `reference/architecture.md` `needs/` annotations, `chain.py` docstring → `food-supply_spec`.
Band/state references left on `public-needs_spec`. Also corrected a stale cycle-integration line
in `public-needs_spec` (active-event effects now precede the needs step, item 5a — from the
Withhold slice).
