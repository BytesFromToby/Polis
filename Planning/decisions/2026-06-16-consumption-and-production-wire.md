# Consumption scale + the Public→production wire

**Date:** 2026-06-16
**Spec:** `public-needs_spec.md` (Features: Consumption, The Public→production wire),
`food-supply_spec.md` (the efficiency multiplier + `wine_happy` output), `events_spec.md`
(consumption gates + Wells Sicken / Drunken Riot), `special-factions_spec.md` (field).
**Proposal:** `../proposals/public-model.md` (Layer-3 balance-axis + the two production wires).
**Scope call (user):** "Consumption + both production wires."

## Decisions

**Consumption is the U-shaped scale — both ends bite.** Dry → bad-water illness (period-true:
weak wine meant dangerous water); Sodden → work stops + drunken violence. Tempered is the sweet
spot. This is the proposal's one mid-good scale.

**Driver = wine supply only (first cut, deliberately).** `consumption_target` tracks the food
chain's `wine_happy` per demand. **No misery→drink feedback** — that closed loop (unhappiness
raises drinking AND drinking cuts output → spiral) is the doom-loop the proposal explicitly flags.
Tracking wine supply only keeps the loop open; a drink-to-cope term waits behind a governor.

**Consumption subsumes the old `drunk` flag.** Previously `drunk` was an ad-hoc threshold
(`wine_happy/demand ≥ 0.25`) computed in the chain. Now wine drives the consumption *scale*, and
`drunk` derives from its band (Tipsy/Sodden). One source of truth; unrest's drunk-pressure keeps
working unchanged. The chain's `drunk` computation is removed; it now reports `wine_happy` for the
driver.

**Both production wires as ONE efficiency multiplier.** The proposal pairs health→output↑ and
consumption→output↓ as "a single global efficiency multiplier." Built once, read from the Public's
**start-of-cycle** bands (the chain runs before the needs drift), applied to food-chain output:
`efficiency = 1.0 + health_bonus − consumption_penalty`, clamped `[EFF_MIN, EFF_MAX]`. Health
Robust/Thriving lift it; consumption Tipsy/Sodden cut it. A Healthy+Tempered city = ×1.0 (no
change), so the wire is a *nudge*, not a regime change.

**Magnitudes deliberately small.** The shipped three-source redundancy + dynamics tests are the
guardrail: the wire's bonuses/penalties are tuned so those properties still hold. Any breakage is
the anticipated coupling (same discipline as the fish/flocks regime-shift repairs) — adjust the
property's fixture, never mask a real regression.

**Scope this slice:** the multiplier applies to **food** production only (the measurable, tested
output). Extending it to other production (piety supply, etc.) is deferred.

## Deferred
Misery→drink feedback (+ its governor); the multiplier on non-food production; confidence's
band-consequences; the richer event deck. Consumption is the **last of the seven scales** — after
this, the Public's state model from `public-model.md` is structurally complete (confidence aside,
which is the existing `support`).
