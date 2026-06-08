# Deviations — Audience Build-Target Info
Blueprint: Planning/blueprints/audience-build-target-info_BP.md
Date: 2026-06-08

| Slice | Step | Deviation | Why |
|-------|------|-----------|-----|
| —     | —    | None.     | —   |

Implemented as written. `base_project_description` + `BASE_PROJECT_DESCRIPTIONS` added and
exported; `VALID_FACTION_TERMS_TEMPLATE` BuildProject bullet parameterized with the faction's
own project name + description; the `<deal>` schema target reuses the existing `{domain}`
substitution (= faction.domain_primary, the domain id) so no new substitution was needed; the
stale "name the project" assertion updated to assert the faction's own buildable ("Agora").
Engine targeting untouched. Full suite 372 passed.
