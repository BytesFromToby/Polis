# /city/load self-heals stale domain caps — 2026-06-07

## What
`POST /city/load` now re-derives each domain's `base_cap`/`cap` from the template's
starting factions when a game is created from a template, instead of copying the
template's stored `domains_json` verbatim. New helper `_refrozen_domains_json`
(in `api/routes/city.py`) deserializes the template domains + factions, recomputes
utilization, and runs `_freeze_base_caps` — the same freeze `load_state_from_json`
applies for the CLI path. The stale official "Polis" template row in `polis.db` was
also updated in place to the derived caps.

## Why
Domain `cap` in `data/domains.json` is an authored placeholder (`300`) that the
projects-v6 design intentionally ignores — real caps are `round(starting Σlevel ×
CAP_HEADROOM_MULT)`, frozen at game start. `_freeze_base_caps` enforces that on the
CLI/seed path, but:

- The official template is seeded into the DB **once** (`seed_official_cities` skips
  existing rows), so the row seeded before the freeze logic kept `cap=300` and no
  `base_cap`.
- `/city/load` copied that row verbatim, so every new game started at `util/300`,
  then dropped to `cap=0` after one cycle (`base_cap(0) + contribution(0)`), which the
  faction-panel header hides (`v-if="d.cap"`).

Freezing on load makes the path conform to the existing design and is
self-correcting: any future stale template still yields correct caps without a
reseed. Chosen over "reseed only" because reseeding alone leaves the same bug latent
for any template that goes stale again.

## Test
`tests/test_city_load_cap_freeze.py` — a stale template (placeholder `cap=300`, no
`base_cap`) yields derived caps after `_refrozen_domains_json`.
