# Blueprint: Shelve Tax Exemption
Spec: Planning/specs/tax-exemption-shelve_spec.md
Date: 2026-06-08

---

## Builder instructions
- Execute steps in order. Do not skip, reorder, or read ahead into the next slice.
- Check off each step when complete: [ ] → [x]
- One step = one logical concern. If a step can't be tested on its own, it's too small — merge it. If it touches more than one concern, split it.
- Deviation: if you do something differently than the step says, note it inline and keep going.
- Stuck: stop immediately. Do not try alternative approaches. Report exactly where and why.
- Backend test: `cd backend && py -m pytest tests/ -q` · Frontend: `cd frontend && npm run build`

---

## Slice 1: Prompt no longer offers tax exemption
**Scope:** The built audience system prompt offers only endorsement as a Mayor term; the dormant parser/engine paths are untouched.

### Step 1: Drop tax exemption from the offered terms + deal schema
**Build:** In `engine/llm/prompt_builder.py`:
- `VALID_MAYOR_TERMS_TEMPLATE` (~line 74): remove the `{tax_line}` line so the template is just:
  `What the {title} can offer you:\n- Public endorsement (immediate +10 reputation with the {title})`.
- In `PromptBuilder.build` (~lines 276-278): remove the `tax_line = _tax_line(...)` line and the `tax_line=tax_line` kwarg from the `VALID_MAYOR_TERMS_TEMPLATE.format(...)` call.
- Delete the now-unused `_tax_line` helper (~lines 220-235) — no dead code (CLAUDE.md).
- The `<deal>` schema line (~line 123): change `- {title} terms ("mayor_terms"): {{"type": "tax_exemption", "duration": <1-10>}} or {{"type": "endorsement"}}` to offer only endorsement: `- {title} terms ("mayor_terms"): {{"type": "endorsement"}}`.
- Do NOT touch `response_parser.py`, `engine/models.py` exemption methods, `end_of_cycle.py` jealousy, or `audiences.py` `_apply_mayor_terms` — they stay dormant.
**Test:** `cd backend && py -m pytest tests/ -q`
**Done When:** Full suite runs; any failures are only prompt/term-list assertions to be updated in Step 2 (not parser/engine).
**Stuck If:** A non-prompt test fails (e.g. the dormant parser test at test_audience_terms.py ~107-113) — that means the parser/engine was disturbed; stop.
- [x] Complete
**Deviation:** Also removed the now-unused `domain=faction.domain_primary` kwarg from the `VALID_MAYOR_TERMS_TEMPLATE.format(...)` call (only `title` is used after dropping the tax line) — pure cleanup, same result.

### Step 2: Prompt tests
**Build:** In `backend/tests/test_audience_terms.py`, add a test `test_prompt_offers_only_endorsement` that builds the system prompt with `PromptBuilder` (mirror the existing build used by the `"endorsement" in p.lower()` assertion at ~line 58: same stub `Faction`/`Leader`/`Mayor`/`domains`). Assert on the built prompt string `p`:
- `"endorsement" in p.lower()`
- `"tax exemption" not in p.lower()` and `"tax_exemption" not in p.lower()`
- the `<deal>` schema's mayor_terms line shows `endorsement` and not `tax_exemption`.
Leave the existing case that parses a `<deal>` containing a `tax_exemption` term (~lines 107-113) UNCHANGED — it encodes the dormant-parser Done-when item ("parser still parses a tax_exemption term without error"). If any existing assertion expected tax exemption to appear in the prompt, update it to endorsement-only.
**Test:** `cd backend && py -m pytest tests/test_audience_terms.py -q`
**Done When:** New prompt test passes; the dormant-parser test still passes; full suite green.
**Stuck If:** The dormant-parser test can only pass by changing `VALID_MAYOR_TERM_TYPES` — stop (that contradicts the dormant-hide decision).
- [x] Complete

---
⛔ End of Slice 1. Run **inspector** on this slice before continuing.

---

## Final Slice: Remove the UI action + spec deferral, verify
**Scope:** The Mayor Actions panel has no Grant Tax Exemption control; the affected specs carry the deferral; everything verified.

### Step 1: Remove the Grant Tax Exemption UI action
**Build:** In `frontend/src/components/MayorActionsModal.vue`: remove the "Grant Tax Exemption" `action-row` block (right/Economic column), and the now-unused `exemptFaction` / `exemptCycles` data fields and any `GrantTaxExemption` Act handler/usage. Leave `api.js` exempt method and the backend route dormant (do not chase them).
**Test:** `cd frontend && npm run build`
**Done When:** Build succeeds; no Grant Tax Exemption control remains in the template; no references to removed `exemptFaction`/`exemptCycles` linger.
**Stuck If:** `exemptFaction`/`exemptCycles` are referenced elsewhere in the component beyond the removed row — report where.
- [x] Complete

### Step 2: Spec deferral edits
**Build:** Mark tax exemption deferred coherently:
- `Planning/specs/audience_spec.md` "Valid Deal Terms": Mayor offers only `endorsement` in the demo; mark `tax_exemption` deferred; rewrite the Done-when that says the prompt "lists only tax_exemption and endorsement as Mayor terms" to "lists only endorsement (tax_exemption deferred)".
- `Planning/specs/treasury_spec.md` "Faction Tax Exemption": add a deferred note (no tax effect under v3; shelved).
- `Planning/specs/game-ui_spec.md` mayor-actions list: drop Grant Tax Exemption from the demo action set and any Done-when that names it.
- Light one-line deferral notes only where `mayor_spec.md` / `llm-system_spec.md` / `reference/data-models.md` present tax_exemption as an active Mayor term (do not rewrite those specs).
**Test:** Manual reread — grep the four files for "tax exemption"/"tax_exemption" and confirm each remaining mention is framed as deferred/dormant, not active.
**Done When:** The specs describe tax exemption as deferred, consistent with the code.
**Stuck If:** N/A.
- [x] Complete

### Final Step: Verify spec Done when items
**Build:** No new code. Confirm all `**Done when:**` items in tax-exemption-shelve_spec.md are met.
**Test:** `cd backend && py -m pytest tests/ -q` (prompt-offer + dormant-parser items) and `cd frontend && npm run build` (UI build). Capture output. For the `[human-required]` items (no UI action; spec deferral notes present), drive the UI / show the grep evidence.
**Done When:** Every `[automated]` criterion passes via its committed test; the `[human-required]` items have captured evidence.
**Stuck If:** An automated criterion fails and the cause is not clear from the output.
- [x] Complete

---
⛔ Final slice complete. Run **inspector** for final sign-off.

INSPECTED 2026-06-08 — 5 PASS · 1 needs-human (see output/inspect/Inspect_tax-exemption-shelve_Final_2026-06-08.md)
