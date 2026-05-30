# Blueprint: Audience Term Clarity + Remove budget_allocation
Spec: Planning/specs/audience_spec.md (v4 — "Valid Deal Terms")
Date: 2026-05-29

---

## Builder instructions
- Execute steps in order. Do not skip, reorder, or read ahead into the next slice.
- Check off each step when complete: [ ] → [x]
- One step = one logical concern. If a step can't be tested on its own, it's too small — merge it. If it touches more than one concern, split it.
- Deviation: if you do something differently than the step says, note it inline and keep going.
- Stuck: stop immediately. Do not try alternative approaches. Report exactly where and why.

Test command: `cd backend && py -m pytest tests/ -q`

**Scope guard:** this feature clarifies prompt wording, removes the dead `budget_allocation`
term, and hardens the parser's *target* handling + *unknown-term-type* handling. Do NOT change
action mechanics, add terms, or change the invalid-`committed_action`-*action* path (an unknown
*action* still rejects as today — only an unknown *term type* becomes drop-and-continue).

---

## Slice 1: Clarify terms, remove budget_allocation, harden the parser
**Scope:** The prompt explains each deal term with correct per-action targeting, `budget_allocation` is gone, and the parser drops removed terms (keeping the rest) and strips bogus targets.

### Step 1: Parser — remove budget_allocation, drop-and-continue, target guard
**Build:** In `backend/engine/llm/response_parser.py`:
1. Remove `"budget_allocation"` from `VALID_TERM_TYPES`.
2. Remove the `"budget_allocation"` entry from `_STRING_TERM_MAP`.
3. In `_parse_terms`, change the unknown-term-type handling from returning an error to
   **drop-and-continue**: where it currently does `if term_type not in VALID_TERM_TYPES: return [], f"unknown term type: ..."`, instead `continue` (skip that term, keep parsing the rest).
4. After the `committed_action` action-validity check, clear the target for untargeted actions:
   `if term_type == "committed_action" and action != "BuildProject": target_id = ""`.
   (Leave the existing `invalid committed_action` *action* check as a hard reject — out of scope to change.)
**Test:** Covered by Step 4's committed tests.
**Done When:** `budget_allocation` is not in `VALID_TERM_TYPES`/`_STRING_TERM_MAP`; an unknown term type is skipped not rejected; a `committed_action` of Grow/Protect comes out with `target_id == ""`, BuildProject keeps its target.
**Stuck If:** Removing the error path breaks an existing parser test that asserted whole-deal rejection on an unknown type — check `tests/test_llm.py::TestResponseParser` and report before changing the test's intent.
- [x] Complete

### Step 2: Prompt — explain each term, fix targeting, drop budget_allocation
**Build:** In `backend/engine/llm/prompt_builder.py`:
1. `VALID_MAYOR_TERMS_TEMPLATE`: delete the `- Budget allocation to {domain} domain …` line. Keep
   the tax line and the endorsement line (both already say what they do).
2. `VALID_FACTION_TERMS_TEMPLATE`: replace the generic `(target optional)` line with an explicit,
   per-action list, e.g.:
   ```
   What you can commit to (one commitment, every turn for 1–10 cycles):
   - Grow — invest in your own strength (no target)
   - Protect — raise your defenses; you take less harm from ALL rivals (no target)
   - BuildProject — work to build a specific city project (name the project)
   - Refrain from Harm or Steal against one named faction
   ```
3. In `SYSTEM_TEMPLATE`'s `<deal>` schema (lines ~129–130): remove the `budget_allocation` option
   from the mayor-terms line (leave `tax_exemption` and `endorsement`). Replace the single generic
   faction-terms line with **one option per line**, showing `target_id` only where it's real:
   ```
   - {title} terms ("mayor_terms"): {{"type": "tax_exemption", "duration": <1-10>}} or {{"type": "endorsement"}}
   - Your terms ("faction_terms") — commit to exactly ONE:
     - {{"type": "committed_action", "action": "Grow", "duration": <1-10>}}
     - {{"type": "committed_action", "action": "Protect", "duration": <1-10>}}
     - {{"type": "committed_action", "action": "BuildProject", "target_id": "<a project id>", "duration": <1-10>}}
     - {{"type": "committed_abstain", "action": "Harm" | "Steal", "target_id": "<a faction id>", "duration": <1-10>}}
   ```
   Keep each option on its own line (the Step 4 test relies on per-line isolation). `{valid_actions}`
   may become unused in the templates — that's fine; leave the variable defined or remove it.
**Test:** Covered by Step 4's committed tests.
**Done When:** The built prompt offers only tax_exemption + endorsement on the mayor side, explains Grow/Protect/BuildProject + abstain, and shows `target_id` only on the BuildProject and committed_abstain schema lines.
**Stuck If:** `SYSTEM_TEMPLATE.format(...)` raises (brace escaping / a removed `{valid_actions}` key still referenced) — fix the format args; report if unclear.
- [x] Complete
**Deviation:** `{valid_actions}` and `{domain}` placeholders became unused in the two templates; left the `.format()` kwargs in build() (harmless, ignored) rather than removing them.

### Step 3: Remove budget_allocation from the model comment + secondary docs
**Build:** Delete every remaining `budget_allocation` reference outside the audience_spec changelog:
- `backend/engine/models.py` (~L329) — the `DealTerm.type` comment.
- `Planning/reference/data-models.md` (~L192) — the `DealTerm.type` enum row.
- `Planning/specs/llm-system_spec.md` — the prose "Budget allocation to {domain}…" line (~L188) and
  `budget_allocation` in `VALID_MAYOR_TERM_TYPES` (~L284).
- `Planning/specs/mayor_spec.md` (~L96) — drop "budget allocations cancelled" from the revoke line.
Leave the historical mention in `audience_spec.md` (the v4 changelog) and the decision log — those
document the removal on purpose.
**Test:** `cd backend && grep -rn "budget_allocation\|budget allocation" engine/ api/ ../Planning/reference ../Planning/specs/llm-system_spec.md ../Planning/specs/mayor_spec.md` returns nothing.
**Done When:** The grep above is empty (budget_allocation survives only in audience_spec's changelog + the decision log).
**Stuck If:** A reference appears in a file not listed here — stop and report it rather than editing blindly.
- [x] Complete
**Deviation:** Left `mayor_spec.md:71` ("Allocate Budget to Domain") and engine `AllocateBudget` untouched — that's the separate, wired Mayor *action*, not the audience deal-term. Only the deal-term `budget_allocation` was removed.

### Step 4: Committed tests
**Build:** Create `backend/tests/test_audience_terms.py` (reuse the `_faction`/`_mayor`/MagicMock-db
patterns from `tests/test_llm.py`). Cover each Done-when:
- **(a)** `"budget_allocation"` is not in `response_parser.VALID_TERM_TYPES`, not in `_STRING_TERM_MAP`, and not in a freshly built system prompt.
- **(b)** the built prompt explains each term: contains "Grow", "Protect" with "all"/"ALL", "BuildProject" with "project", plus "tax" and "endorsement" (case-insensitive as needed).
- **(c)** in the built prompt, the schema line containing `"action": "Protect"` does NOT contain `target_id`, the line with `"action": "Grow"` does NOT, the line with `"action": "BuildProject"` DOES, and the `committed_abstain` line DOES. (Isolate per line.)
- **(d)** `ResponseParser().parse` of an accepted `<deal>` with `faction_terms=[{committed_action, Protect, target_id:"some_faction"}]` and `mayor_terms=[{endorsement}]` → `accepted` and `faction_terms[0].target_id == ""`; the same with `BuildProject, target_id:"dock"` → `target_id == "dock"`.
- **(e)** parse of an accepted `<deal>` with `mayor_terms=[{tax_exemption,duration:4},{budget_allocation,duration:3}]` and a valid faction term → `accepted` True, mayor_terms length 1, only `tax_exemption` present (budget dropped).
- **(f)** parse with `mayor_terms=[{budget_allocation,duration:3}]` + a valid faction term → not accepted (mayor side empty → one-sided), `parse_error` mentions one side committed nothing.
**Test:** `cd backend && py -m pytest tests/test_audience_terms.py -q`
**Done When:** All six pass.
**Stuck If:** (c)'s per-line isolation is brittle — assert on the specific option substring up to its line break; report if the prompt format makes this impossible.
- [x] Complete

---
⛔ End of Slice 1. Run **inspector** on this slice before continuing.

---

## Final Slice: Verification
**Scope:** Full suite green; budget_allocation confirmed gone as a live term.

### Final Step: Verify spec Done when items
**Build:** No new code. Confirm all spec `**Done when:**` items are met.
**Test:** `cd backend && py -m pytest tests/ -q` (every automated item has a committed test from Slice 1). Then confirm the removal grep from Step 3 is still empty.
**Done When:** Every automated criterion passes via its committed test; the only surviving `budget_allocation` mentions are the audience_spec changelog and the decision log (documenting the removal).
**Stuck If:** An automated criterion fails and the cause is not clear from the output.
- [x] Complete

---
⛔ Final slice complete. Run **inspector** for final sign-off.

✅ Inspector: PASS — 2026-05-29 — 6/6 automated criteria pass (full suite 274 passed); removal grep empty. See output/inspect/Inspect_audience-term-clarity_Final_2026-05-29.md
