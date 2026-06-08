# Spec: Audience Deal Card

Faction LLMs sometimes emit the `<deal>` JSON block early (step 1 or 3), and the audience
transcript renders each turn's text verbatim — so raw JSON leaks into the dialogue bubble. This
replaces any in-transcript `<deal>` block with clean in-character prose plus a compact, formatted
**"Proposed deal" card** styled like the existing "Confirm the deal" box. Frontend-only
presentation; the negotiation logic, backend, and the Confirm box / Debug panels are unchanged.

## Scope
- Does: strip `<deal>…</deal>` from every displayed faction turn so bubbles show only prose;
  render a formatted deal card (all fields) under any turn that carried a parseable deal.
- Does NOT: change the backend, the deal schema, the response parser, the negotiation flow, the
  existing Confirm-the-deal box, or the Show JSON / Debug panels; introduce any backend/network
  change (the deal fields are already in the turn text the client receives).

## Feature: Deal card in the transcript
In `frontend/src/components/AudienceModal.vue`, each faction turn (`step1`/`step3`/`step5`) is
shown via `{{ ... }}`. A helper splits a turn's text on `<deal>`/`</deal>`: the prose (everything
before `<deal>`) is shown in the bubble; the JSON between the tags is parsed. When it parses, a
"Proposed deal" card renders under that bubble, styled with the existing `.confirm-box` /
`.terms-grid` / `.term-row` classes and `termLabel(t)`.

Card contents (all fields from the deal block):
- **You give** — `mayor_terms` via `termLabel`.
- **They give** — `faction_terms` via `termLabel`.
- **Break penalty** — `rep_cost_if_broken_by_mayor`, phrased e.g. "Breaking this costs you 20 reputation".
- **Memory note** — `memory_note`.
- **Why** — `reasoning`, shown as a muted "Why: …" line (out-of-character, but the player sees it).

- Input: a faction turn's raw text that may contain a `<deal>{…}</deal>` block.
- Output: clean prose in the bubble, plus a formatted deal card when a valid deal was present.

**Done when:**
- `cd frontend && npm run build` succeeds with no template/script errors  `[automated]`
- No faction transcript bubble displays a raw `<deal>`/`</deal>` tag or JSON braces — bubbles show only in-character prose  `[human-required]`
- When a faction turn carried a deal, a "Proposed deal" card renders under that bubble, visually consistent with the Confirm-the-deal box (same You give / They give grid styling)  `[human-required]`
- The card shows all five elements — You give, They give, the break-penalty sentence, the memory note, and a muted "Why:" reasoning line — each populated from the deal  `[human-required]`
- A faction turn with **no** deal block renders exactly as before (prose only, no card)  `[human-required]`
- A malformed/unparseable `<deal>` block is stripped from the prose and produces no card and no console/render error (the modal still works)  `[human-required]`
