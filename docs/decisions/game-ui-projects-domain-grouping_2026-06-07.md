# Decisions: Game UI — Projects Panel Domain-Grouping
Spec: Planning/specs/game-ui_spec.md
Date: 2026-06-07

- **Group projects by `domain`, not by initiating faction** — the original ask was "divide by
  faction," but a project's only faction link is `initiated_by` ("mayor" | faction_id), and the
  player thinks of projects as belonging to a domain (base projects are one repeatable type per
  domain). Grouping by domain is internally consistent with the data model and mirrors the
  faction panel's domain grouping on the left column. Grouping by `initiated_by` was rejected as
  not matching how projects are owned; `initiated_by` stays visible only in the details modal.
- **Show every domain, always (even empty)** — chosen over "only domains with projects" so the
  panel reads as a stable, complete list of the city's domains, symmetric with the faction panel.
  Empty domains show a "No projects" placeholder.
- **Collapsible, expanded by default** — over collapsed-by-default (the faction panel's behaviour)
  so all projects are visible on load; over always-expanded so long lists can still be tidied.
- **Flat list within each domain group** — the prior under-construction-first split is dropped
  inside a group; build status is conveyed per-row (% for under-construction, status label
  otherwise). Per-row domain text is removed as redundant under the domain header.
- **No backend change** — `ProjectResponse` already carries `domain` and `build_progress`; this is
  pure frontend work over the existing `/projects` endpoint. The existing
  `tests/test_projects_api.py` (build_progress in response) remains the only automated Done-when.
