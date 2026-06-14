# Spec: Audience Build-Target Info

> **ARCHIVED 2026-06-13 — consolidated into `../specs/audience_spec.md`** ("BuildProject — the
> faction's own buildable"), which carries the live rule + Done-when items. Kept here for full
> problem-statement context. Non-authoritative.

A faction can only build its **own domain's** base project (the resolver gates on
`domain_primary`; `_committed_plan` hardcodes the target to the faction's domain). But the
audience prompt tells the LLM nothing about what it can build — it just says "name the project"
and the `<deal>` schema asks for a free-text "project id" (the `audience_spec` example even shows
the pre-v6 `dock_expansion`). So the LLM negotiates blind and may agree to build a project in
another domain or a nonexistent one; the engine ignores the named target and builds the faction's
own-domain project anyway — making the **agreed deal terms mismatch what is actually built** (and
polluting the deal card / confirm box / training log with incoherent targets). This feature gives
the LLM the one project it can build (name + a one-line effect) and aligns the deal target with
the engine's domain-id model, so the agreed terms match the outcome. Engine behavior is unchanged.

## Scope
- Does: add a single-sourced one-line description per base project; inject the audience faction's
  **own** buildable (name + description) into the prompt; make the `<deal>` BuildProject `target_id`
  the faction's **domain id**; update the `audience_spec` `<deal>` example off the stale project id.
- Does NOT: change the engine's build targeting (`_committed_plan` already builds own-domain), the
  resolver, or which projects a faction can build; list the whole project catalog in the prompt
  (only the faction's own buildable — one line); add cross-domain building; touch Sabotage.

## Feature: Per-project description (single source)
A one-line description per base project, keyed by domain, parallel to `BASE_PROJECT_NAMES` in
`engine/projects/processing.py` — a `BASE_PROJECT_DESCRIPTIONS` dict plus a
`base_project_description(domain_id)` helper. It defaults to a generic sentence (all v6 base
projects do the same thing mechanically — building raises the domain's cap), e.g.
`"Raises {Domain}'s capacity, giving its factions room to grow."` This is the one place the
effect text lives, so prompt/UI/docs can't drift.

- Input: a `domain_id` (and the domain's display name for the sentence).
- Output: a one-line human-readable effect string.

**Done when:**
- `base_project_description(domain_id)` returns a non-empty one-line string for every domain in `BASE_PROJECT_NAMES`, and a sensible default for an unknown domain  `[automated]`

## Feature: Prompt names the faction's own buildable
The audience system prompt's "what you can commit to" BuildProject line (currently the static
`VALID_FACTION_TERMS_TEMPLATE` bullet "work to build a specific city project; name the project") is
parameterized with **this faction's own** base-project name and its description — exactly one
buildable, scoped to the faction (no full catalog). The `<deal>` schema's BuildProject `target_id`
instruction names the faction's **domain id** (matching `base_stacks` keys / the engine), not a
free-text project id.

- Input: the audience `faction` (its `domain_primary` → project name + description + target id).
- Output: a system prompt whose BuildProject term line states the faction's own project name +
  effect, and whose `<deal>` schema shows the domain id as the BuildProject target.

**Done when:**
- The built prompt for a faction contains its own domain's base-project name (e.g. a `harbor` faction's prompt contains "Docks") and that project's description text  `[automated]`
- The built prompt's BuildProject `<deal>` target instruction references the faction's domain id and contains no free-text "project id" placeholder and no `dock_expansion`  `[automated]`
- A faction's prompt does not enumerate other domains' base projects (only its own buildable appears)  `[automated]`

## Feature: Spec coherence
`audience_spec.md` Valid Deal Terms and the `<deal>` example reflect the new model: BuildProject
builds the faction's own-domain project, targeted by the domain id; the example no longer uses
`dock_expansion`. A light note in `llm-system_spec.md` if it describes the prompt's project section.

**Done when:**
- `audience_spec.md` no longer contains `dock_expansion`, and its BuildProject term describes building the faction's own-domain project targeted by domain id  `[human-required]`
