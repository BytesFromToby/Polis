# Planning — Orientation

The project's source of truth and its supporting tiers. Start here, then go to the right tier.

## What lives where

| Path | Holds |
|------|-------|
| `specs/` | **Source of truth for behavior** — one `[feature]_spec.md` per feature, with inline **Done when:** items |
| `reference/` | As-built truth specs cite (not testable): `data-models.md` (entities), `formulas.md` (contest math), `architecture.md` (system map) |
| `proposals/` | Forward-looking design docs for not-yet-built features (subsystems / cross-cutting mechanics) |
| `blueprints/` | Per-feature build plans from `foreman` (`[feature]_BP.md`) |
| `decisions/` | Decision log (`YYYY-MM-DD-title.md`) — append-only, point-in-time record |
| `archive/` | Retired docs — shipped proposals, superseded specs |

## Spec index

Read top-down within a group; `cycle-runner` is the entry point.

**Sim core — the spine**
- [cycle-runner](specs/cycle-runner_spec.md) — orchestrates one cycle (sequential initiative); delegates to the rest
- [actions](specs/actions_spec.md) — faction action types and how each resolves
- [faction-behavior](specs/faction-behavior_spec.md) — NPC weight building, action selection, targeting
- [personality-system](specs/personality-system_spec.md) — trait structure; how personality drives/evolves behavior

**Governance — the Mayor (player)**
- [mayor](specs/mayor_spec.md) — indirect, costly actions that pressure the city
- [treasury](specs/treasury_spec.md) — gold, taxes, the moneylender
- [projects](specs/projects_spec.md) — buildable city infrastructure + effects
- [audience](specs/audience_spec.md) — Mayor↔leader LLM negotiation; the only path to binding deals

**World & content**
- [special-factions](specs/special-factions_spec.md) — The Public, moneylender, external threats
- [events](specs/events_spec.md) — timed pressure sequences injected into the faction system

**LLM layer**
- [llm-system](specs/llm-system_spec.md) — translation between engine and any model provider (stub mode without one)
- [llm-profiles](specs/llm-profiles_spec.md) — saved configs, key encryption, selection at game start

**Setup & presentation**
- [player-identity](specs/player-identity_spec.md) — new-game capture of player + city name and title; threaded into the prompt
- [faction-descriptions](specs/faction-descriptions_spec.md) — faction blurb/description in the audience prompt and UI
- [game-ui](specs/game-ui_spec.md) — the Vue browser interface

**Not built** (see `proposals/`)
- [city-generation](proposals/city-generation.md) — procedural city/domain/faction generation

## Quick pointers

- Entities / fields → `reference/data-models.md`
- Formulas / thresholds → `reference/formulas.md`
- How a cycle actually runs → `specs/cycle-runner_spec.md` (authoritative) + `reference/architecture.md`
- Why a past choice was made → `decisions/`
