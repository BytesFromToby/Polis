# Deviations — Player Identity
Blueprint: Planning/blueprints/player-identity_BP.md
Date: 2026-05-29

| Slice | Step | Deviation | Why |
|-------|------|-----------|-----|
| 1 | 1 | Did not delete `polis.db`. Added `player_name`/`player_title` to the existing forward-only migration in `db/session.py` `_migrate()` (`_add_column_if_missing`) instead. | Deleting the dev DB is destructive — it holds saved games. The migration backfills the columns with defaults on the existing DB at startup, meets the same Done-When, loses no data, and matches the established `llm_profile_id` migration pattern. |

All other steps were executed as written. The `build()` method keeps its `city_setting`
parameter (now unused) for back-compat with existing callers rather than removing it — this
was anticipated by the blueprint (Slice 2 Step 1 Stuck-If) and is not a behavioural change.
