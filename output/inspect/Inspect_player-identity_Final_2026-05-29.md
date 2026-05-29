# Inspect Report — Player Identity · Final
Spec: Planning/specs/player-identity_spec.md
Blueprint: Planning/blueprints/player-identity_BP.md
Date: 2026-05-29
Run/demo command: `cd backend && py -m pytest tests/ -q` · UI: `py -m uvicorn api.server:app` + Playwright

Summary: 12 passed · 0 failed · 1 need human sign-off

## Results
| Criterion | Status | Evidence |
|-----------|--------|----------|
| New-Game form shows player-name "Kallisto" + city-name "Polis" + Start | needs-human | `output/inspect/spec_player-identity_final_2026-05-29.png` — Playwright: input values `['Kallisto','Polis']`, Start button visible, 0 error banners |
| Starting with defaults → run player_name="Kallisto", player_title="Prytanis", city "Polis" | PASS | `test_player_identity.py::test_start_defaults_identity` |
| Editing both fields persists entered player name + city name | PASS | `test_player_identity.py::test_start_custom_name_and_city` (Theron / Megara) |
| Blank player/city falls back to that field's default | PASS | `test_player_identity.py::test_start_blank_name_falls_back` (whitespace → Kallisto) |
| SimRun has player_name/player_title columns; default Kallisto/Prytanis | PASS | `test_start_defaults_identity` + columns confirmed on `SimRun.__table__` (defaults Kallisto/Prytanis) |
| Snapshot/restore round-trip preserves name/title/city | PASS | `test_player_identity.py::test_identity_persists_in_fresh_session` (fresh session re-read) |
| Built prompt contains city, player name, title | PASS | `test_llm.py::test_canonical_briefing_injected` (Athenai/Perikles/Strategos) |
| Prompt opens with briefing signatures "bows to no king" + "never a master" | PASS | `test_llm.py::test_canonical_briefing_injected` (also asserts no blank leading line) |
| SETTING_TONE removed; briefing regardless of setting | PASS | `test_llm.py::test_setting_value_does_not_change_briefing` (asserts `not hasattr(pb,'SETTING_TONE')`) |
| Audience route passes run identity + city into builder for begin | PASS | `test_player_identity.py::test_begin_audience_threads_identity_into_prompt` + `test_get_audience_identity_reads_run` |
| Built prompt contains no "Mayor"; references use the title | PASS | `test_llm.py::test_no_mayor_wording_uses_title` |
| No "measured, not verbose"; brevity instruction retained | PASS | `test_llm.py::test_voice_line_sharpened` |
| Stub audience still yields a parseable `<deal>` after rename/voice | PASS | `test_player_identity.py::test_stub_audience_still_parses_after_rename` (parse_error=="") |

Full suite: **258 passed** (`py -m pytest tests/ -q`).

## Deviations noted
| Step | Deviation | Impact |
|------|-----------|--------|
| Slice 1, Step 1 | Added columns via `db/session.py` `_migrate()` instead of deleting `polis.db` | None — same Done-When (columns present, defaults applied); avoids destroying saved games; matches existing migration pattern |
| Slice 2, Step 1 | `build()` keeps unused `city_setting` param for back-compat | None — anticipated by the blueprint; no behaviour change |

## Human sign-off
Review, tick when verified:
- [ ] New-Game form shows player-name "Kallisto" + city-name "Polis" + Start — evidence: `output/inspect/spec_player-identity_final_2026-05-29.png`
