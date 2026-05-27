# Decisions: Greek Theme Conversion
Spec: Planning/specs/theme-conversion_spec.md
Date: 2026-05-26

- **Default mechanical values, not a design pass** — caps (300), drift (0.0), a uniform
  Neutral relationship matrix (self = Foe), and uniform faction ratings (3.0/80/75). Chosen to
  ship the re-skin fast; deliberate balancing is deferred to a later spec. Rejected: authoring a
  bespoke 8×8 relationship matrix and balanced per-faction numbers now — too much for a
  short conversion, and easier to tune once the Greek roster is live and observable.
- **Faction relationships left empty** — the engine does not consume static faction-to-faction
  relationships (`get_faction_relationship` is dead code; rivalry flows through domain-Foe and
  emergent relational traits). Seeding them would be inert, so `relationships: []`. Wiring them
  up is its own future feature.
- **"Mayor" term kept; rank-ladder reflavor deferred** — the Prytanis→Basileus ladder is a
  separate future feature that touches UI and specs. This spec is content/data only.
- **Delete Rivers Point and all old saved games** — both reference the retired theme/roster and
  would break against the new domains. Clean slate: drop the Rivers Point seed entry and data,
  and delete the default `polis.db` so it re-seeds fresh. Rejected: migrating old saves — there
  is nothing worth preserving in placeholder/medieval data.
- **`city-generation_spec` updated but kept FUTURE** — it is not scheduled, but leaving it on
  the old 14 domains and the dead `scr/data` path is actively misleading, so it is refreshed to
  the 8 Greek domains while retaining its FUTURE-FEATURE status.
