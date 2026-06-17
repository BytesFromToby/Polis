# Deviations — Confidence (the 7th scale)

Blueprint: Planning/blueprints/confidence_BP.md
Date: 2026-06-17

| Slice | Step | Deviation | Why |
|-------|------|-----------|-----|
| 1 | — | **No new persisted field** (as designed): confidence is a band view over `support`. Only a derived `confidence_band` display key was added to `serialize_the_public`; deserialize is unchanged. | Confidence = the existing support axis; nothing to round-trip. |
| Final | 2 | The Removal Coalition and Effigy target the **`merchant-houses`** faction (port domain) as the ringleader, via existing `rating`/`chaos`/public-`support` effect fields — no trait-add. | Event effects are field-based; the *standing* emboldening is the faction-behavior confidence modifier (Slice 1). A concrete high-rating faction was needed as the coalition's face. |

**No trait-add machinery** was introduced — the spec was kept to existing effect fields, as the
blueprint's "Stuck if" directed.

**Tests:** `test_confidence.py` (7 — bands, posture embolden/damp/neutral/no-public, serialize) +
`test_confidence_events.py` (6 — gates + 3 flagships). Result: **550 green** (544 → 550); headless
`main.py --cycles 10` clean.

**Milestone:** all **seven** Public scales from `public-model.md` are now built
(fed/happy/health/piety/unrest/consumption/confidence). The model is structurally complete.
