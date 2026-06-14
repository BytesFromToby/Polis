# Blueprint: Audience Deal Card
Spec: Planning/specs/audience-deal-card_spec.md
Date: 2026-06-08

---

## Builder instructions
- Execute steps in order. Do not skip, reorder, or read ahead into the next slice.
- Check off each step when complete: [ ] → [x]
- One step = one logical concern. If a step can't be tested on its own, it's too small — merge it. If it touches more than one concern, split it.
- Deviation: if you do something differently than the step says, note it inline and keep going.
- Stuck: stop immediately. Do not try alternative approaches. Report exactly where and why.
- Test command (automated item): `cd frontend && npm run build`

---

## Slice 1: Strip raw deal + render a formatted card
**Scope:** Faction transcript bubbles show only clean prose; where a turn carried a parseable `<deal>`, a formatted "Proposed deal" card renders under it, styled like the Confirm-the-deal box, with all fields.

### Step 1: Parse helper + per-turn computeds
**Build:** In `frontend/src/components/AudienceModal.vue` (script):
- Add a method `parseTurn(text)` returning `{ prose, deal }`:
  - If `text` has no `<deal>`, return `{ prose: text, deal: null }`.
  - Else `prose` = text before `<deal>` (trimmed); attempt `JSON.parse` of the substring between `<deal>` and `</deal>`. On success → `deal` = the object; on any error → `deal: null` (malformed degrades gracefully). Never throw.
- Add computeds: `step1Parsed`, `step3Parsed`, `step5Parsed` each = `this.parseTurn(this.step1/step3/step5 || '')`.
**Test:** `cd frontend && npm run build`
**Done When:** Build succeeds; the computeds exist and `parseTurn` handles no-deal / valid-deal / malformed without throwing.
**Stuck If:** N/A.
- [x] Complete

### Step 2: Show prose + render the deal card in the transcript
**Build:** In the template, for each faction turn replace the raw text binding with the parsed prose and add a card under the bubble:
- Step 1 (~line 24): `<div class="turn-text">{{ step1Parsed.prose }}</div>` and, after the `.turn`, `<div v-if="step1Parsed.deal" ...>` the card.
- Step 3 (~line 45) and Step 5 (~line 66): same with `step3Parsed`/`step5Parsed`.
- The card markup (reuse the existing confirm-box classes so styling matches — do NOT restyle the confirm box): a `.confirm-box`-styled block titled "Proposed deal" containing:
  - a `.terms-grid` with two `.terms-col`s: "You give" → `v-for` `deal.mayor_terms` rendered via `termLabel(t)` in `.term-row` (show a muted "—" when empty); "They give" → `deal.faction_terms` via `termLabel(t)`.
  - a break-penalty line: e.g. `Breaking this costs you {{ deal.rep_cost_if_broken_by_mayor }} reputation` (only when that field is present).
  - a memory-note line: `deal.memory_note` (when present).
  - a muted "Why:" line: `deal.reasoning` (when present) using a muted text style.
- Keep it DRY where reasonable; inline repetition of the small card block across the three turns is acceptable since it reuses existing CSS. If you extract a local sub-component instead, note it as a Deviation.
- Add minimal CSS only if needed (e.g. a muted `.deal-why` line and a `.deal-card-title`); reuse existing `.confirm-box`/`.terms-*`/`.muted` styles otherwise.
**Test:** `cd frontend && npm run build`
**Done When:** Build succeeds; transcript bubbles bind to `*Parsed.prose` (no raw `{{ step1 }}` etc.), and a card block renders under each faction turn when its parsed `deal` is truthy.
**Stuck If:** `termLabel` isn't in scope for the card markup (it is a method on this component — call it directly).
- [x] Complete

### Final Step: Verify spec Done when items
**Build:** No new code. Confirm all `**Done when:**` items in audience-deal-card_spec.md are met.
**Test:** `cd frontend && npm run build` (the one `[automated]` item). For the 5 `[human-required]` items, drive the UI / capture evidence: (a) no bubble shows raw `<deal>`/JSON; (b) a deal-carrying turn shows a card consistent with the Confirm box; (c) the card shows You give, They give, break-penalty sentence, memory note, and the muted "Why:" line; (d) a no-deal turn renders prose only, no card; (e) a malformed `<deal>` block (hand-test by feeding text with broken JSON, or reason from `parseTurn`'s try/catch) yields prose only, no card, no error.
**Done When:** Build passes; the human-required items have captured evidence (screenshots / driven UI).
**Stuck If:** Build fails and the cause isn't clear from the output.
- [x] Complete

---
⛔ Final slice complete. Run **inspector** for final sign-off.

INSPECTED 2026-06-08 — 1 PASS · 5 needs-human (see output/inspect/Inspect_audience-deal-card_Final_2026-06-08.md)
