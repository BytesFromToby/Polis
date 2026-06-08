# Inspection Report — Audience Build-Target Info (Final Sign-Off)

- Feature: Audience Build-Target Info
- Spec: `Planning/specs/audience-build-target-info_spec.md`
- Blueprint: `Planning/blueprints/audience-build-target-info_BP.md`
- Date: 2026-06-08
- Inspector: fresh-eyes sign-off (did not build the feature)
- Verdict: **4 PASS (automated) · 1 needs-human**

## Test runs

Feature tests: `cd backend && py -m pytest tests/test_base_project_description.py tests/test_audience_terms.py -v`
→ **10 passed in 0.22s**

Full suite: `cd backend && py -m pytest tests/ -q`
→ **372 passed in 1.07s**

---

## Done-when items

### 1. `[automated]` — PASS
> `base_project_description(domain_id)` returns a non-empty one-line string for every domain in `BASE_PROJECT_NAMES`, and a sensible default for an unknown domain

- Test: `tests/test_base_project_description.py::test_description_for_every_base_project` (loops every domain in `BASE_PROJECT_NAMES`, asserts non-empty + no `\n`) and `::test_unknown_domain_returns_default` (unknown id → non-empty default). Both PASSED.
- Impl: `engine/projects/processing.py:289-301` — `BASE_PROJECT_DESCRIPTIONS` dict + `base_project_description(domain_id)` helper with generic default `"Raises the {label} domain's capacity, giving its factions room to grow."`. Exported via `engine/projects/__init__.py:4` (`base_project_description`, `BASE_PROJECT_DESCRIPTIONS`).

### 2. `[automated]` — PASS
> The built prompt for a faction contains its own domain's base-project name (e.g. a `harbor` faction's prompt contains "Docks") and that project's description text

- Test: `tests/test_audience_terms.py::test_prompt_names_own_buildable_and_domain_target` — trade faction's prompt contains `"Agora"` and `base_project_description("trade")`. Also `::test_prompt_explains_each_term` asserts `"Agora"` present. Both PASSED.
- Impl: `engine/llm/prompt_builder.py:267-269` formats `VALID_FACTION_TERMS_TEMPLATE` with `base_project_name(faction.domain_primary)` + `base_project_description(faction.domain_primary)`. Template bullet at `:82`.

### 3. `[automated]` — PASS
> The built prompt's BuildProject `<deal>` target instruction references the faction's domain id and contains no free-text "project id" placeholder and no `dock_expansion`

- Test: `tests/test_audience_terms.py::test_prompt_names_own_buildable_and_domain_target` — asserts BuildProject line contains `"target_id": "trade"`, and `"<a project id>"` and `"dock_expansion"` are absent from the prompt. PASSED.
- Impl: `engine/llm/prompt_builder.py:128` — `<deal>` schema BuildProject line uses `"target_id": "{domain}"`, which `SYSTEM_TEMPLATE.format` substitutes with `faction.domain_primary` (the domain id).

### 4. `[automated]` — PASS
> A faction's prompt does not enumerate other domains' base projects (only its own buildable appears)

- Test: `tests/test_audience_terms.py::test_prompt_names_own_buildable_and_domain_target` — asserts `"Docks"` and `"Barracks"` absent from the trade faction's prompt. PASSED.

### 5. `[human-required]` — needs-human (evidence supports PASS)
> `audience_spec.md` no longer contains `dock_expansion`, and its BuildProject term describes building the faction's own-domain project targeted by domain id

- `grep -n "dock_expansion" Planning/specs/audience_spec.md` → no matches (exit 1). Confirmed absent.
- `Planning/specs/audience_spec.md:109` — Valid Deal Terms row:
  `| committed_action · BuildProject | The faction works to build **its own domain's** base project (named in the prompt) | its domain id |`
- `:112` — "Only `BuildProject` (target = the faction's own domain id) ... take a target."
- `:163` — `<deal>` example: `{ "type": "committed_action", "action": "BuildProject", "target_id": "harbor", "duration": 4 }` (domain id, not a stale project id).
- Routed as needs-human per the `[human-required]` tag; all evidence matches the criterion.

---

## Engine targeting unchanged (spec "Does NOT" guard) — confirmed
- `engine/npc/behavior.py:231-234` — `_committed_plan` still hardcodes `target_id=faction.domain_primary` for BuildProject. `git diff --stat` shows no modifications to `behavior.py`. Resolver untouched.

## Summary
4 automated Done-when items PASS (backed by committed tests; all green). 1 human-required item routed for human confirmation with supporting evidence (no `dock_expansion`; own-domain + domain-id BuildProject term). Full suite: 372 passed. Engine build targeting verified unchanged.
