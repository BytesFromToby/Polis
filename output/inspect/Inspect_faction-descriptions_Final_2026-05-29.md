# Inspect Report — Faction Descriptions · Final
Spec: Planning/specs/faction-descriptions_spec.md
Blueprint: Planning/blueprints/faction-descriptions_BP.md
Date: 2026-05-29
Run/demo command: `cd backend && py -m pytest tests/ -q` · UI: `py -m uvicorn api.server:app` + Playwright

Summary: 7 passed · 0 failed · 3 need human sign-off

## Results
| Criterion | Status | Evidence |
|-----------|--------|----------|
| `Faction` model has `blurb`/`description` defaulting to `""` | PASS | `test_faction_descriptions.py::test_model_defaults_empty` |
| All 41 factions in factions.json have non-empty blurb + description | PASS | `test_all_factions_have_blurb_and_description` (asserts len==41 + non-empty each) |
| Spot checks match theming.md (eumelidai/silverbench) | PASS | `test_spot_checks_match_theming` |
| serialize_faction → deserialize_faction round-trips both fields | PASS | `test_serializer_round_trips_descriptions` |
| load_state_from_json yields populated blurb/description | PASS | `test_loader_populates_descriptions` |
| Built audience prompt contains the faction description when set | PASS | `test_description_present_in_prompt_when_set` |
| Empty description omitted cleanly (no artifact) | PASS | `test_empty_description_omitted_cleanly` |
| Expanded faction block shows the blurb | needs-human | `spec_faction-descriptions_final_leftpanel_2026-05-29.png` — Playwright: 3 `.faction-blurb` rendered; first = '"the well-flocked," old wealth in land and herds' |
| A faction with empty blurb renders no broken element | needs-human | Guarded by `v-if="f.blurb"`; all 41 seeded factions have a blurb so no empty case occurs in the official city |
| AudienceModal displays the faction's description on open | needs-human | `spec_faction-descriptions_final_audience_2026-05-29.png` — `.audience-desc` = "The senior clan: vast estates, an ancient name, treats the city as theirs by right." |

Full suite: **266 passed** (`py -m pytest tests/ -q`).

Extra coverage: `test_seed_official_city_carries_descriptions` proves the seed→serialize path carries the fields; the live official "Polis" city in polis.db was refreshed (0 runs referenced it) so new games carry descriptions.

## Deviations noted
| Step | Deviation | Impact |
|------|-----------|--------|
| Slice 1 / Step 3 | Transcribed 41 pairs via a one-off UTF-8 script (run then deleted) | None — all 41 keys added verbatim from theming.md; safer escaping |
| Slice 2 / Steps 3+4 | One `npm run build` for both frontend steps | None |
| Final / Step 1 | Deleted + re-seeded the official Polis city | None — 0 sim_runs referenced it; user games use copies; regenerated with fields |

## Human sign-off
Review, tick when verified:
- [ ] Faction block shows the blurb — evidence: `output/inspect/spec_faction-descriptions_final_leftpanel_2026-05-29.png`
- [ ] Empty blurb renders nothing — `v-if` guarded (no empty case in seeded data)
- [ ] AudienceModal shows the description on open — evidence: `output/inspect/spec_faction-descriptions_final_audience_2026-05-29.png`
