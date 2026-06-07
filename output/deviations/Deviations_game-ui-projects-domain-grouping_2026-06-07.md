# Deviations — Game UI Projects Panel Domain-Grouping
Blueprint: Planning/blueprints/game-ui-projects-domain-grouping_BP.md
Date: 2026-06-07

| Slice | Step | Deviation | Why |
|-------|------|-----------|-----|
| 1 | 1 | Removed unused `buildingProjects`/`otherProjects` (Step 4's work) and the already-dead `activeProjects` in the same edit that added `projectsByDomain`. | `projectsByDomain` replaced the same computed block; folding the removal in avoided an intermediate half-edited block. Net result identical; Step 4 explicitly allowed removing `activeProjects` if trivially safe (grep confirmed no references). |
| 1 | 3 | Live play-screen confirmation deferred to inspector. | Driving the full UI (login + game setup + screenshots) is the inspector's evidence-capture role for the `[human-required]` items. Build passes exit 0; click-to-open-modal and `refresh()` modal-sync wiring left untouched. |
| 1 | 4 | Executed as part of Step 1 (see Step 1 row). | Same edit removed the computeds; post-build grep confirms no remaining references. |
