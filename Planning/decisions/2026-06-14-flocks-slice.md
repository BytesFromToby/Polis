# Decisions: Public Needs — flocks slice
Spec: Planning/specs/public-needs_spec.md (v3)
Date: 2026-06-14

Third Food source, completing the three-source redundancy. Eumelidai already exist in
`data/factions.json` (aristocracy), so no roster change. Source design: `proposals/resource-chains.md`
(Food: three sources) + `proposals/public-model.md`.

- **Mixed estate, NOT full per-estate differentiation** — the Eumelidai produce flocks (this
  chain) *and* still contribute barley via the harvest chain's `domain: aristocracy` producer.
  Chosen because:
  1. It keeps flocks **purely additive** — barley and fish are byte-for-byte unchanged (the fish
     slice already left the ~20% gap), so no re-tune and no regression risk to the shipped balance.
  2. The estates' sizes (Eumelidai 4 / Pyrrhidai 3 / Skiadai 2) **don't map onto the 50/30/20
     source proportions** if each estate owns one food: making the *biggest* estate the flocks
     (smallest, 20%) source would invert the design.
  3. Clean differentiation needs a producer-list schema (barley from two named factions) plus a
     multi-constant re-tune — disproportionate for this slice.
  - A great landed house holding both grainfields and herds is realistic; "well-flocked" emphasizes
    the herds without excluding grain. The clean one-estate-one-food split is **deferred to the
    roster restructure**, which reworks the estates holistically anyway.
- **Flocks feed `fed` directly as fresh meat, no processor** — same as fish. Butchering (Tanners)
  and temple sacrifice are the richer processed forms, deferred. Wool (the Eumelidai's other
  output) is a future *Goods* chain, not Food — out of scope.
- **Additive tuning targets the three sources summing to ≈ demand** — the city sits at the top of
  Fed / into Well-fed, engaging the population treadmill (grows while well-fed → demand rises →
  settles toward Fed). Provisional: `FLOCKS_PER_LEVEL = 1`, `MEAT_FED_PER_UNIT = 1.0`.
- **Mixed-estate consequence for the redundancy test** — because the Eumelidai produce both barley
  and flocks, "remove the aristocracy" now drops barley *and* flocks together (→ fish only →
  Hungry). The clean single-source isolation for flocks is via removing the pastoral *chain* (a
  disaster model), if a test needs it. The fish-slice two-source `Redundancy` Done-when is
  superseded by the three-source version (losing fish now leaves the city Fed — the resilience
  gain, not Hungry).
