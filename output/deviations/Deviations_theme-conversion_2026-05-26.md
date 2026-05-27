# Deviations — Greek Theme Conversion
Blueprint: Planning/blueprints/theme-conversion_BP.md
Date: 2026-05-26

| Slice | Step | Deviation | Why |
|-------|------|-----------|-----|
| 2 | 1 | Also changed `setting="DnD"` → `setting="Greek"` in `seed.py` | Legacy theme label on the seeded City row, adjacent to the edited city def; part of the re-skin though not named in the step. |
| 2 / 3 | 3 / 2 | Consolidated Slice 3's fresh-DB assertions into `tests/test_seed_official.py` alongside the Slice 2 seeding test, instead of a separate test module | Same observable coverage (single official "Polis", 8 Greek domains, 41 factions, no legacy domain ids); avoids a near-duplicate test file. |
| Final | 2 | Also changed the legacy `registry` domain → `professions` in `treasury_spec.md` (beyond the named "Rivers Point starts with 2" line) | `registry` is a Rivers Point domain id; under the Greek theme tax-farming belongs to the Quillsworn in the `professions` domain. |

## Scope expansion (user-approved)
- **Final Step 4** was escalated: the grep over all of `Planning/specs/` found legacy domain ids in specs the conversion spec's Feature 4 did NOT enumerate. The user chose to expand scope ("update the examples with the new stuff"). Beyond the three named files, the following were re-themed to Greek domains/factions:
  - `projects_spec.md` — example projects remapped (transportation/finance/political/underworld/street/religion → harbor/trade/military/aristocracy/temples/guilds); "docks/Stevedores" → "wharves/Quaymen"; starting projects → Harbor Wharves / City Walls / The Agora.
  - `special-factions_spec.md` — moneylender pseudo-domain `finance` → `trade`; Bandits chaos `street/underworld` → `harbor/trade`; Rival City `dock` → `harbor`; Plague Vector `health` → `professions` (Asklepiads).
  - `events_spec.md` — "Iron Mine Disaster"/ironmongers/industry → "The Great Forge Fire"/bronzehands/guilds; Plague `health_domain` → `professions_domain`; "Trade Ship Seized" `docks_domain` → `harbor_domain`; deck example `mine_disaster`/industry → `forge_fire`/guilds.
  - `reference/data-models.md` — relational-trait example `target_id: "traders_compact"` → `"pyrrhidai"`.
  - Domains deferred (Assembly/Council) or cut (Underworld/street) had no 1:1 target, so those examples were rewritten to the nearest live Greek domain, not mechanically mapped.
  - Historical decision logs (e.g. `2026-04-17-rating-cap-5.md`, which names Star Tribune) were left untouched — append-only point-in-time records, not current docs.
