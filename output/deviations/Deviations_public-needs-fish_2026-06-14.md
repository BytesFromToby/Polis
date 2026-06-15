# Deviations — Public Needs: fish slice
Blueprint: Planning/blueprints/public-needs-fish_BP.md
Date: 2026-06-14

| Slice | Step | Deviation | Why |
|-------|------|-----------|-----|
| 1 | — | The `[inspect]` gate was flowed past (single inspector pass at the end) | User instruction "build on all slices". The re-tune (Slice 1 Step 4) leaves the legibility dynamics test transiently red until its repair in Final Slice Step 2 — a known cross-slice sequence, not a regression. |
| Final | 2 | Legibility dynamics test repaired by changing the induced shortage from a one-time *halve* to a *sustained pin at 1.0* (cycles 10–19), then restore | In the two-source world the NPC estates regrow after a one-time halve and fish cushions it, so a transient halve no longer registers a band drop — that's the redundancy working. The test's property (visible within 5 cycles, recovers within 15) is unchanged; only the shortage is made real/sustained. Not a weakening. |

No other deviations. No constant tuning was needed — `HARVEST_PER_LEVEL=2`, `FISH_PER_LEVEL=3`,
`FISH_FED_PER_UNIT=1.0` satisfied all four redundancy bands on the first try; stability and
Toil-matters passed unchanged.
