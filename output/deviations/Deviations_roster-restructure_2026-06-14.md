# Deviations — Roster Restructure
Blueprint: Planning/blueprints/roster-restructure_BP.md
Date: 2026-06-14

| Slice | Step | Deviation | Why |
|-------|------|-----------|-----|
| 1 | 1–2 | factions.json / domains.json rewritten via a one-off Python transform (load → cut/re-home/add → write) | Deterministic and less error-prone than hand-editing 28+7 JSON objects. Same result. |
| 1 | 5–7 | Two **extra** test-fixture fixes beyond the three named files: `test_audience_terms.py` (synthetic `"trade"` faction asserting "Agora" → `"guilds"` / "Workshop") and `test_domain_base_project_name.py` (`harbor`→"Docks" → `port`→"Docks") | These fixtures broke when `trade`/`harbor` left `BASE_PROJECT_NAMES`. Mechanical id swaps. Harmless synthetic dead-id labels in test_actions / test_city_load_cap_freeze / test_events_system left as-is (don't break; outside the no-dead-id Done-when which is engine/api/db only). |
| 1 | 7 (food coupling) | `test_needs_dynamics.py`: `ARISTOCRACY` tuple gained `elaiades`; the **legibility** test reframed from *pin estates to 1.0* → *remove the aristocracy and restore* | The Skiadai split raised the aristocracy floor (4 estates, each min level 1), so a pin is now cushioned by redundancy and no longer drops a band. The shortage was made severe enough to register; the test's property (visible ≤5, recover ≤15) is unchanged. Food **balance** untouched — aristocracy Σ level == 9, all redundancy bands hold. Same regime-shift category as the fish/flocks legibility repairs. |
| 1 | 8 | Added an in-place **refresh** of a stale official template (update, not delete — FK-safe; user cities untouched) | An existing dev DB carrying the old roster must migrate; fresh DBs (the tests) take the create path. |
| Final | 1 | Graceful-save test placed in a new `tests/test_roster_migration.py` | Cleaner home than appending to test_seed_official. |

**Flavor recorded for review:** the 5 new factions (The Elaiades, The Builders, The Dockhands,
The Merchant Houses, The City Guard) carry proposed names / blurbs / leader names from the decision
log — the user may revise; renaming is a trivial data edit.

Result: full suite **456 green**; headless run on 28 factions (fed=77, Well-fed — the 4th estate
nudged supply up); old-roster snapshot restores; food system provably undisturbed (Σ level
conserved). No engine logic changed beyond `BASE_PROJECT_NAMES` and the seed refresh.
