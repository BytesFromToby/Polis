# Decisions: Audience Deal Card
Spec: Planning/specs/audience-deal-card_spec.md
Date: 2026-06-08

- Frontend-only. The deal's fields are already present in the raw turn text the client
  receives, so the card can be built client-side with no backend/schema change. Rejected
  exposing new fields from the API — unnecessary for the in-transcript case.
- Strip `<deal>` from ALL turns (1/3/5), not just where it's "supposed" to appear. LLMs emit
  the block unpredictably; a defensive strip guarantees the dialogue never shows raw JSON.
- Include the out-of-character `reasoning` as a muted "Why:" line (user choice: show all
  fields). It's meta, but the player opted to see it; keeping it visually muted limits the
  immersion cost.
- Malformed deal → strip and show prose only, no card, no crash. Robustness over completeness:
  a bad block must never break the audience modal.
- Confirm-the-deal box and Debug/Show-JSON panels left unchanged — the Confirm box is the
  visual template the card mirrors, not something to refactor here.
