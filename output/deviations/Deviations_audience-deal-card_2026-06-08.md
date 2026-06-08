# Deviations — Audience Deal Card
Blueprint: Planning/blueprints/audience-deal-card_BP.md
Date: 2026-06-08

| Slice | Step | Deviation | Why |
|-------|------|-----------|-----|
| —     | —    | None.     | —   |

Implemented as written. `parseTurn` + step1/3/5Parsed computeds in AudienceModal.vue;
the "Proposed deal" card markup is inlined under each faction turn (explicitly sanctioned
by the blueprint) reusing the confirm-box classes, with three small added styles
(.deal-card/.deal-line/.deal-why). Build passes; parseTurn verified across
valid/none/malformed inputs.
