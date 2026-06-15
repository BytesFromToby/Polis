# Planning — Orientation

The project's source of truth and its supporting tiers. Start here, then go to the right tier.

## What lives where

| Path | Holds |
|------|-------|
| `specs/` | **Source of truth for behavior** — one `[feature]_spec.md` per feature, with inline **Done when:** items |
| `reference/` | As-built truth specs cite (not testable): `data-models.md` (entities), `formulas.md` (contest math), `architecture.md` (system map) |
| `proposals/` | Forward-looking design docs for not-yet-built features (subsystems / cross-cutting mechanics) |
| `blueprints/` | Per-feature build plans from `foreman` (`[feature]_BP.md`) — holds only the **current/most-recent** build; shipped ones retire to `archive/blueprints/` |
| `decisions/` | Decision log (`YYYY-MM-DD-title.md`) — append-only, point-in-time record |
| `archive/` | Retired docs — shipped proposals, superseded/consolidated specs, and shipped blueprints (`archive/blueprints/`) |

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
- [audience](specs/audience_spec.md) — Mayor↔leader LLM negotiation; the only path to binding deals (subsumes the former build-target-info / deal-card / training-log / tax-exemption-shelve satellites — now archived)

**World & content**
- [special-factions](specs/special-factions_spec.md) — The Public, moneylender, external threats
- [public-needs](specs/public-needs_spec.md) — the barley run: population + fed/happy/health needs, the harvest chain, Toil, band-gated events
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
- [resource-chains](proposals/resource-chains.md) — the full resource map (second pass 2026-06-12): three sinks, food redundancy, Withhold, imports, capability pools, tuning doctrine; v1 slice **shipped** as [public-needs](specs/public-needs_spec.md) (archived: [barley-run](archive/barley-run.md))
- [faction-resource-map](proposals/faction-resource-map.md) — per-faction resource jobs + the 2026-06-14 cut-test roster (41→28 factions, 9→7 domains; design intent, not built)
- [public-model](proposals/public-model.md) — the Public as a subsystem: belief-as-mechanic, the seven scales (fed/happy/health/piety/confidence/unrest/consumption), band matrix, extreme-crisis events
- [crisis-and-stance](proposals/crisis-and-stance.md) — disasters as crisis generators + bounded LLM stance layer (rejects LLM-decides-everything; records why)
- [elections-and-titles](proposals/elections-and-titles.md) — recurring election endgame + dynamic title ladder threaded into the audience prompt
- [ui-pottery-art-direction](proposals/ui-pottery-art-direction.md) — Geometric-pottery visual direction for the UI redo (band grammar, two-glaze themes); competes with the Wine-Dark system in `docs/Polis Design/`

## Spec organization (convention)

`specs/` is kept **flat — one spec per subsystem** (the 16 above). It stays flat on purpose: the
specs cross-reference each other by bare same-dir filename and the Plumbline skills glob
`specs/*.md`, so subfolders would break links and tooling for little gain. The index groups above
are the "virtual folders."

- **Amendments fold into their parent.** A small follow-on tweak to an existing subsystem updates
  that subsystem's spec (a new section) — it does **not** become a new `*_spec.md`. This is what
  keeps the folder from filling with satellites (4 were consolidated into `audience_spec.md` on
  2026-06-13; the originals live in `archive/` for their full context).
- **Real subfolders wait for a tripwire:** revisit per-cluster subfolders only when one group
  passes ~6–8 specs (likely first when `resource-chains` spawns fish / withhold / imports / piety),
  and pay the link-rewrite cost once, for that cluster, deliberately.

## Quick pointers

- Entities / fields → `reference/data-models.md`
- Formulas / thresholds → `reference/formulas.md`
- How a cycle actually runs → `specs/cycle-runner_spec.md` (authoritative) + `reference/architecture.md`
- Why a past choice was made → `decisions/`
