# Inspection Report — Shelve Tax Exemption (Final Sign-off)

- Feature: Shelve Tax Exemption (dormant-hide)
- Spec: `Planning/specs/tax-exemption-shelve_spec.md`
- Blueprint: `Planning/blueprints/tax-exemption-shelve_BP.md`
- Inspector: fresh-eyes (did not build)
- Date: 2026-06-08

## Evidence runs
- `cd backend && py -m pytest tests/test_audience_terms.py -v` → 7 passed
- `cd backend && py -m pytest tests/ -q` → **369 passed** (full suite green)
- `cd frontend && npm run build` → built in 165ms, no errors (dist emitted)

## Done-when verdicts

### 1. [automated] PASS
"The built audience system prompt's offer section contains 'endorsement' and contains neither 'tax exemption' nor 'tax_exemption' (case-insensitive)"
- Test: `tests/test_audience_terms.py::test_prompt_offers_only_endorsement` (PASSED).
  Asserts `"endorsement" in p.lower()`, `"tax exemption" not in p.lower()`, `"tax_exemption" not in p.lower()` (lines 62-66).
- Source: `engine/llm/prompt_builder.py:74-75` — `VALID_MAYOR_TERMS_TEMPLATE` offers only
  "Public endorsement (immediate +10 reputation with the {title})"; no `{tax_line}` placeholder.

### 2. [automated] PASS
"The `<deal>` schema text in the built prompt shows `endorsement` as the only mayor_terms type (no `tax_exemption` example)"
- Test: `tests/test_audience_terms.py::test_prompt_offers_only_endorsement` (PASSED).
  Extracts the `("mayor_terms")` schema line and asserts it contains `endorsement` and not `tax_exemption` (lines 67-70).
- Source: `engine/llm/prompt_builder.py:122` — `- {title} terms ("mayor_terms"): {{"type": "endorsement"}}` (only endorsement).

### 3. [automated] PASS
"The response parser still parses a `<deal>` whose mayor_terms include `tax_exemption` without error (dormant path intact)"
- Test: `tests/test_audience_terms.py::test_budget_term_dropped_deal_seals` (PASSED).
  Parses a deal whose mayor_terms include `{"type": "tax_exemption", "duration": 4}` and asserts
  `r.accepted` and `r.mayor_terms[0].type == "tax_exemption"` (lines 115-124). Dormant parse path unchanged.
- Source: `engine/llm/response_parser.py:18` — `VALID_MAYOR_TERM_TYPES` still includes `"tax_exemption"`.

### 4. [automated] PASS
"`cd frontend && npm run build` succeeds with no errors"
- Run output: `vite v8.0.3 ... ✓ 47 modules transformed ... ✓ built in 165ms`. No errors.

### 5. [human-required] PASS (needs-human, evidence captured)
"The Mayor Actions panel shows no 'Grant Tax Exemption' action (only Political, Economic, Construction, Deals)"
- Static inspection of `frontend/src/components/MayorActionsModal.vue`:
  - Grep for `Grant Tax Exemption|exemptFaction|exemptCycles|GrantTaxExemption|tax_exemption|tax exemption`
    (case-insensitive) → **no matches**.
  - Rendered action rows are: Endorse a Faction (`MayorActionsModal.vue:34-44`), Condemn a Faction (48-58),
    Build Project (67-78), Sabotage (93-103), and Break in the Active Deals section (115).
  - No Grant Tax Exemption row and no `exemptFaction`/`exemptCycles` data refs.
- Build verifies no dangling references. A live human glance at the rendered modal is the formal sign-off,
  but static evidence shows the control is fully removed.

### 6. [human-required] PARTIAL — needs-human (one gap)
"`audience_spec.md`, `treasury_spec.md`, and `game-ui_spec.md` each carry the tax-exemption-deferred note,
and audience_spec's 'Valid Deal Terms' Done-when reflects endorsement-only"
- `audience_spec.md`: PASS. Deferred note at lines 96-99 ("`tax_exemption` is deferred (shelved 2026-06-08)...
  parser keeps the `tax_exemption` term (dormant)"); Done-when at line 123 rewritten to "lists only
  `endorsement` as a Mayor term (`tax_exemption` deferred — see note above)".
- `game-ui_spec.md`: PASS. Line 123 — "(Grant Tax Exemption is deferred/shelved 2026-06-08 — no UI row...)";
  Done-when line 144 names "the deferred Grant Tax Exemption" as not rendered.
- `mayor_spec.md` (extra, per blueprint): PASS. Lines 81-83 mark Grant Tax Exemption "deferred/dormant
  (shelved 2026-06-08)... backend lever and engine machinery remain dormant".
- `llm-system_spec.md` (extra, per blueprint): PASS. Lines 294-295 — `VALID_MAYOR_TERM_TYPES` comment
  "tax_exemption dormant: still parsed if present, but no longer offered in the prompt".
- **`treasury_spec.md`: GAP.** The spec's Done-when names treasury_spec as one of the three that must carry
  the deferral note, and blueprint Final-Slice Step 2 instructs adding a "Faction Tax Exemption" deferred note.
  treasury_spec.md has a "Deferred to future" section (lines 133-147) covering per-domain tax-rate tiers,
  moneylender, etc., but **no mention of tax exemption / faction tax exemption** (grep for
  "[Tt]ax [Ee]xemption|[Ee]xemption" → no matches). The faction-exemption shelving is not explicitly noted there.
  This Done-when clause is therefore not fully met for treasury_spec. Flagged for human to add a one-line note.

## Dormant paths — confirmed NOT removed (spec "Does NOT" scope)
- `engine/llm/response_parser.py:18,31,142,153` — `VALID_MAYOR_TERM_TYPES` has `tax_exemption`,
  string map, parse branch, domain-conflict reject branch — all intact.
- `engine/models.py:509,515,522` — `tick_exemptions`, `grant_exemption`, `is_exempt` intact.
- `engine/cycle/end_of_cycle.py:233-236,241-252` — deal-linked exemption removal + `apply_domain_jealousy` intact.
- `engine/llm/audiences.py:388` — `_apply_mayor_terms` `tax_exemption` branch intact.

## Summary
- Automated items: 4 / 4 PASS.
- Human-required items: 1 PASS (UI control removed, evidence captured); 1 PARTIAL/needs-human
  (audience + game-ui + bonus mayor/llm-system specs carry deferral; **treasury_spec.md lacks the note** —
  a Done-when clause not fully met).

Signed: Inspector (fresh-eyes), 2026-06-08.
