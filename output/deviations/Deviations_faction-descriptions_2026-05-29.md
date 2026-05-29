# Deviations — Faction Descriptions
Blueprint: Planning/blueprints/faction-descriptions_BP.md
Date: 2026-05-29

| Slice | Step | Deviation | Why |
|-------|------|-----------|-----|
| 1 | 3 | Transcribed the 41 blurb/description pairs via a one-off UTF-8 Python script (run, then deleted) instead of hand-editing factions.json | Same result (all 41 keys added verbatim from theming.md); safer handling of em-dashes and inner quotes than manual JSON editing |
| 2 | 3+4 | Ran `npm run build` once after both frontend steps rather than once per step | Both steps are frontend; a single build verifies both |

All other steps executed as written. Final-slice Step 1 (delete + re-seed the official "Polis"
city) was performed after confirming 0 sim_runs referenced it — non-destructive to user data.
