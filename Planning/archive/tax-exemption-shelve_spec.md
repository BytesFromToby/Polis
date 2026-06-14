# Spec: Shelve Tax Exemption

> **ARCHIVED 2026-06-13 — non-authoritative record.** The shelving is complete; its live facts
> are stated self-sufficiently in `../specs/audience_spec.md`, `../specs/treasury_spec.md`,
> `../specs/mayor_spec.md`, and `../specs/game-ui_spec.md`. Kept here as the full shelving record.

The Grant Tax Exemption action has **no effect on income** under treasury_spec v3 — income is
`BASE_INCOME + TAX_OFFICE_INCOME × Tax Offices` and `_calc_income` never reads factions or
`mayor.is_exempt`. So the control lies about its name, and "tax_exemption" deal terms pollute the
audience training log. This shelves it (dormant-hide, like the Moneylender): it is removed from
the player's actions and from what the LLM offers factions, while the parser/engine machinery
stays intact but unreached. Revive it if/when a faction-based tax returns.

## Scope
- Does: remove the Grant Tax Exemption action from the Mayor Actions UI; stop the audience prompt
  offering `tax_exemption` to factions (endorsement becomes the only Mayor term offered); mark it
  deferred in the affected specs.
- Does NOT: remove or change the response parser's `VALID_MAYOR_TERM_TYPES`, `Mayor.grant_exemption`/
  `is_exempt`/`tick_exemptions`, the domain-jealousy −3 rep in `end_of_cycle.py`, or the
  `_apply_mayor_terms` tax_exemption branch — these stay dormant (a stray `tax_exemption` still
  parses harmlessly). Does NOT change income, and does NOT add a backend migration.

## Feature: Shelve Tax Exemption (dormant-hide)
- Input: the current audience prompt (offers tax exemption + endorsement) and the Mayor Actions UI
  (has a Grant Tax Exemption action).
- Output: a prompt that offers only endorsement, and a UI with no tax-exemption control; the
  dormant parser/engine paths untouched.

Changes:
- `engine/llm/prompt_builder.py`: the "What the {title} can offer you" term list (`VALID_MAYOR_TERMS_TEMPLATE`
  + the tax-exemption availability line ~229-230) no longer offers tax exemption — only endorsement.
  The `<deal>` schema example (~line 123) lists `{"type": "endorsement"}` as the only mayor_terms type.
- `frontend/src/components/MayorActionsModal.vue`: remove the Grant Tax Exemption action-row and its
  `exemptFaction`/`exemptCycles` state and the `GrantTaxExemption` Act call. (`api.js` exempt method and
  the backend route may remain dormant.)
- Specs: `audience_spec.md` Valid Deal Terms — Mayor offers only `endorsement` for the demo, tax_exemption
  marked deferred, and the Done-when that says the prompt "lists only tax_exemption and endorsement as
  Mayor terms" rewritten to "only endorsement". `treasury_spec.md` Faction Tax Exemption — marked deferred.
  `game-ui_spec.md` mayor-actions list — Grant Tax Exemption dropped from the demo action set + its Done-when.

**Done when:**
- The built audience system prompt's offer section contains "endorsement" and contains neither "tax exemption" nor "tax_exemption" (case-insensitive)  `[automated]`
- The `<deal>` schema text in the built prompt shows `endorsement` as the only mayor_terms type (no `tax_exemption` example)  `[automated]`
- The response parser still parses a `<deal>` whose mayor_terms include `tax_exemption` without error (dormant path intact — existing behaviour unchanged)  `[automated]`
- `cd frontend && npm run build` succeeds with no errors  `[automated]`
- The Mayor Actions panel shows no "Grant Tax Exemption" action (only Political, Economic, Construction, Deals)  `[human-required]`
- `audience_spec.md`, `treasury_spec.md`, and `game-ui_spec.md` each carry the tax-exemption-deferred note, and audience_spec's "Valid Deal Terms" Done-when reflects endorsement-only  `[human-required]`
