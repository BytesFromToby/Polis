# Decisions: Public Needs — fish slice
Spec: Planning/specs/public-needs_spec.md (v2)
Date: 2026-06-14

First build slice of the Resource+Public program. Source design: `proposals/resource-chains.md`
(Food: three sources) + `proposals/public-model.md`. Netmenders already exist in `data/factions.json`
(harbor), so no roster restructure is required for this slice.

- **Fish feeds `fed` directly, no processor** — chosen per the proposal's "zero new mechanics."
  Fish is eaten fresh; salting (a Tanners processor) is explicitly deferred. Implemented by reusing
  the existing unprocessed/porridge path (a chain with no processors routes all raw to the need at
  its `fed_per_unit`), so the engine change is minimal.
- **Producers can be `faction_id`-keyed, not only `domain`-keyed** — fish comes from one faction
  (Netmenders), and the Port/harbor domain holds other factions that don't fish. A `domain`-keyed
  producer would wrongly count them. So `compute_chain`'s producer summing gains a `faction_id`
  branch. Rejected: a `domain: harbor` producer (over-counts); a Netmenders-only sub-domain (heavier).
- **Barley re-tuned down (`HARVEST_PER_LEVEL` 3 → 2)** — the load-bearing point of redundancy is
  that *each* source is insufficient alone. With barley left at 3 it already ≈ feeds the city
  (~75% of demand), so adding fish would make the city over-fed and fish non-load-bearing (losing
  it wouldn't matter). Re-tuning barley to partial (~50%) + fish (~30%) makes both matter and
  yields the target: lose either → Hungry, lose both → Starving. This is inherent to adding a
  load-bearing second source, not an incidental nerf.
  - Consequence: a shipped barley test that baked in the literal `3` must move to reference
    `HARVEST_PER_LEVEL`; the shipped dynamics tests (property-based) must re-pass under the new
    constants. Both are in the spec's Done-when.
- **Build to the final three-source proportions now (~barley 50 / fish 30 / flocks 20)** rather
  than making barley + fish fully feed the city — so the standard city runs slightly lean ("Fed,
  not Well-fed") until the flocks slice closes the ~20% gap. Avoids re-tuning both sources down
  again when flocks lands. Recorded as an intentional interim state, not a gap.
- **Redundancy is specified as a property, not exact values** — the Done-when asserts band
  outcomes (one source out → Hungry, not Starving from a Fed start; both out → Starving) with the
  constants provisional and tuned to satisfy it. Same discipline as the shipped dynamics tests.
