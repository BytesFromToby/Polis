# Inspection Report — Audience Deal Card (Final Sign-off)

- Feature: Audience Deal Card
- Spec: `Planning/specs/audience-deal-card_spec.md`
- Blueprint: `Planning/blueprints/audience-deal-card_BP.md`
- Component under test: `frontend/src/components/AudienceModal.vue`
- Inspector: fresh-eyes static + build + node re-verification (did not build the feature)
- Date: 2026-06-08

## Summary
- 1 PASS (automated build)
- 5 needs-human (visual/UI items, verified by static inspection + node re-verification)
- Source/spec NOT modified.

---

## Done-when items

### 1. `cd frontend && npm run build` succeeds with no template/script errors  `[automated]` — PASS
Ran `cd frontend && npm run build`. Build tail:

```
dist/index.html                   0.45 kB │ gzip:  0.29 kB
dist/assets/index-1TN9Qbhb.css   20.18 kB │ gzip:  3.97 kB
dist/assets/index-CJBQzqFQ.js   177.31 kB │ gzip: 56.39 kB
✓ built in 163ms
```
No template/script errors. **PASS.**

### 2. No faction transcript bubble displays a raw `<deal>`/`</deal>` tag or JSON braces — bubbles show only prose  `[human-required]` — needs-human (code evidence supports PASS)
Each faction bubble binds to the parsed prose, not the raw turn string:
- Step 1: `<div class="turn-text">{{ step1Parsed.prose }}</div>` (line 24)
- Step 3: `<div class="turn-text">{{ step3Parsed.prose }}</div>` (line 67)
- Step 5: `<div class="turn-text">{{ step5Parsed.prose }}</div>` (line 110)

No raw `{{ step1 }}`/`{{ step3 }}`/`{{ step5 }}` bindings remain in the template. `parseTurn` (lines 314-325) sets `prose = text.slice(0, open).trim()` — everything before `<deal>` — so the tag and JSON braces cannot appear in the bubble. Node re-verification (VALID case) confirms prose = `"We are pleased to consider terms."` with the `<deal>…</deal>` block excluded.

### 3. When a turn carried a deal, a "Proposed deal" card renders under that bubble, visually consistent with the Confirm box  `[human-required]` — needs-human (code evidence supports PASS)
Each turn has a `v-if="stepNParsed.deal"` card:
- Step 1: line 26 `<div v-if="step1Parsed.deal" class="confirm-box deal-card">`
- Step 3: line 69 `<div v-if="step3Parsed.deal" class="confirm-box deal-card">`
- Step 5: line 112 `<div v-if="step5Parsed.deal" class="confirm-box deal-card">`

Cards reuse the existing Confirm-box classes (`.confirm-box`, `.confirm-label`, `.terms-grid`, `.terms-col`, `.terms-head`, `.term-row`) so styling matches; `.deal-card` only quiets the border/background (line 543). Title is `<div class="confirm-label">Proposed deal</div>`. Terms render via `termLabel(t)`, the same method the Confirm box uses (lines 150/157).

### 4. The card shows all five elements, each populated from the deal  `[human-required]` — needs-human (code evidence supports PASS)
Per card (Step 1 example, lines 26-47; identical for Step 3 lines 69-90 and Step 5 lines 112-133):
- **You give** — `mayor_terms` via `termLabel(t)` (line 32); muted `—` when empty (line 34).
- **They give** — `faction_terms` via `termLabel(t)` (line 39); muted `—` when empty (line 41).
- **Break penalty** — line 44: `Breaking this costs you {{ ...rep_cost_if_broken_by_mayor }} reputation.` guarded by `!= null`.
- **Memory note** — line 45: `Note: {{ ...memory_note }}` guarded by `v-if`.
- **Why** — line 46: `<div ... class="deal-why muted">Why: {{ ...reasoning }}</div>`, muted/italic style (CSS line 545).

All five present and field-bound.

### 5. A turn with no deal renders prose only, no card  `[human-required]` — needs-human (code evidence supports PASS)
The card is gated solely by `v-if="stepNParsed.deal"`. Node re-verification (NONE case): `parseTurn('We have nothing to offer yet…')` → `{ prose: <full text>, deal: null }`. `deal: null` is falsy, so the `v-if` is false and no card renders — bubble shows prose only.

### 6. A malformed `<deal>` block is stripped, produces no card, no error  `[human-required]` — needs-human (code evidence supports PASS)
`parseTurn` wraps `JSON.parse` in `try { … } catch { deal = null }` (line 323) — never throws. Node re-verification (MALFORMED case): `parseTurn('Here are our terms.\n<deal>{this is not json,,}</deal>')` → `{ prose: "Here are our terms.", deal: null }`. Did not throw; prose excludes the broken block; `deal: null` → no card.

---

## Node re-verification of `parseTurn` (extracted verbatim from AudienceModal.vue)
```
VALID:     prose "We are pleased to consider terms."  deal = full object (mayor_terms/faction_terms/rep_cost.../memory_note/reasoning)
NONE:      prose = full text                          deal = null
MALFORMED: prose "Here are our terms."                deal = null  (did not throw)
```
All three behave exactly as the spec/blueprint require.

## Confirm box & Debug panels unchanged
- Confirm-the-deal box (lines 144-168): still gated by `phase === 'await-confirm'`, uses `proposedMayorTerms`/`proposedFactionTerms`, label "The faction accepts. Confirm the deal?", Decline/Accept buttons — unmodified. The new cards reuse its CSS classes but do not restyle `.confirm-box` itself; `.deal-card` is an additive class.
- Debug controls — "Show JSON" and "Debug — all LLM calls" `<details>` panels (lines 211-228) and `requestJson()`/`debugLog` — unmodified.

## Verdict
Automated item PASS. Five human-required items: code + node evidence all support PASS; flagged needs-human as the live UI cannot be driven here. No source or spec modified.
