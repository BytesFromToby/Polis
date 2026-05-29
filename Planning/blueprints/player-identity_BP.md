# Blueprint: Player Identity
Spec: Planning/specs/player-identity_spec.md
Date: 2026-05-29

---

## Builder instructions
- Execute steps in order. Do not skip, reorder, or read ahead into the next slice.
- Check off each step when complete: [ ] → [x]
- One step = one logical concern. If a step can't be tested on its own, it's too small — merge it. If it touches more than one concern, split it.
- Deviation: if you do something differently than the step says, note it inline and keep going.
- Stuck: stop immediately. Do not try alternative approaches. Report exactly where and why.

Test command (backend): `cd backend && py -m pytest tests/ -q`
Frontend build: `cd frontend && npm run build`

---

## Slice 1: Identity persistence (data layer + new-game write)
**Scope:** A started run carries `player_name` and `player_title`, defaulting to Kallisto / Prytanis, with blank inputs falling back to defaults.

### Step 1: Add identity columns to SimRun
**Build:** In `backend/db/models.py`, add to `SimRun` two columns beside the carried fields (`setting`/`description`/`details`): `player_name: Mapped[str] = mapped_column(String, default="Kallisto")` and `player_title: Mapped[str] = mapped_column(String, default="Prytanis")`. The dev SQLite DB is recreated from `create_all`; if a stale `polis.db` exists and lacks the columns, delete it so it regenerates.
**Test:** `cd backend && py -c "from db.models import SimRun; print(SimRun.player_name, SimRun.player_title)"` runs without error.
**Done When:** `SimRun` has `player_name` and `player_title` columns with defaults "Kallisto" / "Prytanis".
**Stuck If:** An existing migration framework (Alembic) is in use — stop and report; do not hand-edit migrations.
- [x] Complete
**Deviation:** Did not delete `polis.db` (destructive — holds saved games). Instead added the two columns to the project's existing forward-only migration (`db/session.py` `_migrate()` via `_add_column_if_missing`), which backfills defaults on the existing DB at startup. Same Done-When (DB has the columns), no data loss, matches the existing `llm_profile_id` migration pattern.

### Step 2: Accept identity on sim start
**Build:** In `backend/api/schemas.py`, add to `SimStartRequest`: `player_name: Optional[str] = None` and `player_title: Optional[str] = None`. In `backend/api/routes/sim.py` `start_sim`, after resolving `setup_run`, set `setup_run.player_name = (req.player_name.strip() if req and req.player_name and req.player_name.strip() else "Kallisto")` and `setup_run.player_title = (req.player_title.strip() if req and req.player_title and req.player_title.strip() else "Prytanis")` before `db.commit()`. Blank/whitespace → default.
**Test:** Covered by Step 3's committed test.
**Done When:** `start_sim` writes `player_name`/`player_title` onto the run, applying defaults for missing/blank values.
**Stuck If:** `SimStartRequest` is consumed somewhere that breaks with the new optional fields.
- [x] Complete

### Step 3: Committed test — identity capture & persistence
**Build:** Create `backend/tests/test_player_identity.py`. Using the existing test client/fixtures (mirror `tests/test_llm.py` / other API tests for auth + setup-run creation), add tests that:
(a) start a run with no player fields → the persisted `SimRun` has `player_name=="Kallisto"`, `player_title=="Prytanis"`;
(b) patch the city name and start with `player_name="Theron"`, `city_name="Megara"` → run has `player_name=="Theron"` and the city row has `city_name=="Megara"`;
(c) start with `player_name="   "` (blank) → falls back to "Kallisto";
(d) re-query the run row after commit (restore round-trip) → `player_name`/`player_title` and the city's `city_name` are unchanged.
**Test:** `cd backend && py -m pytest tests/test_player_identity.py -q`
**Done When:** All four cases pass.
**Stuck If:** No reusable fixture exists to create a setup run via the API — report what the existing API tests do instead.
- [x] Complete

---
⛔ End of Slice 1. Run **inspector** on this slice before continuing.

---

## Slice 2: Single-canon briefing + voice/rename (prompt builder)
**Scope:** `PromptBuilder.build` emits the canonical Greek briefing naming the city/player/title, with no "Mayor" and no dampening voice line.

### Step 1: Replace SETTING_TONE with the canonical briefing
**Build:** In `backend/engine/llm/prompt_builder.py`: remove the `SETTING_TONE` dict. Add a module constant `GREEK_BRIEFING` holding the "LLM situation briefing" text from `Planning/reference/theming.md` with two fixes — typo "summond"→"summoned", and the player reference parameterised — using placeholders `{city}`, `{player_name}`, `{title}` (e.g. "a free city-state … called {city}", "You stand before {title} {player_name}"). Add `city_name: str = "Polis"`, `player_name: str = "Kallisto"`, `player_title: str = "Prytanis"` params to `PromptBuilder.build`. Set the template's preamble (`tone_line`) to `GREEK_BRIEFING.format(city=city_name, player_name=player_name, title=player_title)`.
**Test:** Covered by Step 3's committed test.
**Done When:** Building a prompt produces the briefing preamble with the city/player/title substituted; `SETTING_TONE` no longer exists.
**Stuck If:** `build()` callers pass positional args that now misalign — note them for Slice 3.
- [x] Complete

### Step 2: Rename Mayor→title and sharpen the voice line
**Build:** In `prompt_builder.py`, in `SYSTEM_TEMPLATE` and the `VALID_MAYOR_TERMS_TEMPLATE`/`VALID_FACTION_TERMS_TEMPLATE` strings, replace every player-facing "Mayor" with the title via a `{title}` slot (e.g. "Your relationship with the {title}", "What the {title} can offer you"). Pass `player_title` into those `.format()` calls. Replace the instruction `"Keep responses to 3–4 sentences — measured, not verbose."` with a brevity-preserving, edgier line, e.g. `"Keep responses to 3–4 sentences — sharp and vivid, speaking with the pride and edge of who you are; never flat or fawning."`
**Test:** Covered by Step 3's committed test.
**Done When:** The built prompt contains no "Mayor" and no "measured, not verbose"; player references use the title.
**Stuck If:** A "Mayor" reference is structural (not player-facing copy) and unclear whether to rename — report it.
- [x] Complete

### Step 3: Committed tests — prompt content; replace obsolete tone test
**Build:** In `backend/tests/test_llm.py`: replace `test_setting_tone_injected` with `test_canonical_briefing_injected`. Add/adjust prompt-builder tests asserting the built system prompt: (a) contains the passed city name, player name, and title; (b) contains the briefing signatures `"bows to no king"` and `"never a master"`; (c) `"SETTING_TONE"` is no longer importable from the module AND building with any/no setting still yields the briefing (no blank first line); (d) contains no occurrence of the word `"Mayor"`; (e) does not contain `"measured, not verbose"` but still instructs ~3–4 sentence brevity.
**Test:** `cd backend && py -m pytest tests/test_llm.py -q`
**Done When:** All assertions pass; the old tone test is gone.
**Stuck If:** A prompt-builder test helper passes a now-removed `city_setting` in a way that errors — update the helper.
- [x] Complete

---
⛔ End of Slice 2. Run **inspector** on this slice before continuing.

---

## Slice 3: Thread identity through the audience route
**Scope:** The live audience route feeds the run's player name/title and the city name into the prompt builder.

### Step 1: Pass identity through the audience flow functions
**Build:** In `backend/engine/llm/audiences.py`, add `city_name: str = "Polis"`, `player_name: str = "Kallisto"`, `player_title: str = "Prytanis"` params to `begin_audience_step` and `run_audience`, and forward them to `_PROMPT_BUILDER.build(...)`.
**Test:** `cd backend && py -m pytest tests/ -q` (no breakage).
**Done When:** Both functions accept and forward the three identity params.
**Stuck If:** A caller other than the route relies on the old signature — report it.
- [x] Complete

### Step 2: Route reads identity from the run/city
**Build:** In `backend/api/routes/mayor.py`, add a helper (or extend `_get_city_description`) to fetch the run's `player_name`/`player_title` and the city's `city_name`. In `audience_begin`, pass `city_name`, `player_name`, `player_title` into `begin_audience_step` alongside the existing `city_description`.
**Test:** Covered by Step 3's committed test.
**Done When:** `audience_begin` passes the run's identity + city name into the prompt builder.
**Stuck If:** The run row isn't reachable from the session in this path — report.
- [x] Complete

### Step 3: Committed tests — route threading & deal contract intact
**Build:** In `backend/tests/test_player_identity.py` (or `test_audience_finalize.py`), add tests that: (a) drive `audience_begin` for a run with a known `player_name`/`player_title` and city name, then assert the returned `debug` payload's `system` prompt contains all three; (b) run a full stub audience (begin→reply→conclude) and assert the conclusion still yields a parseable result (no `parse_error`, a `<deal>`-derived outcome).
**Test:** `cd backend && py -m pytest tests/ -q`
**Done When:** Both tests pass.
**Stuck If:** The begin response doesn't expose the system prompt — confirm `debug_begin` carries `system` (it does per audiences.py `_debug`).
- [x] Complete

---
⛔ End of Slice 3. Run **inspector** on this slice before continuing.

---

## Final Slice: New-Game form + full verification
**Scope:** The title screen captures name + city; full suite green; human-required evidence captured.

### Step 1: Extend the frontend API for sim start
**Build:** In `frontend/src/api.js`, change `sim.start` to `start: (userId, llmProfileId, identity = {}) => post(\`/users/${userId}/sim/start\`, { llm_profile_id: llmProfileId || null, player_name: identity.player_name || null, player_title: identity.player_title || null })`.
**Test:** `cd frontend && npm run build` succeeds.
**Done When:** `sim.start` forwards player identity.
**Stuck If:** Other callers of `sim.start` break — they pass only the first two args, which stays compatible; report if not.
- [x] Complete

### Step 2: New-Game inline form on the title screen
**Build:** In `frontend/src/views/TitleView.vue`, replace the one-click `newGame` with an inline form (shown when "New Game" is chosen): a **player name** text field bound to a `playerName` data prop defaulting `"Kallisto"`, a **city name** field bound to `cityName` defaulting `"Polis"`, and a **Start** button. On Start: `await city.load(userId, cityId)`, then `await city.patch(userId, { city_name: (this.cityName || 'Polis') })`, then `await sim.start(userId, null, { player_name: (this.playerName || 'Kallisto'), player_title: 'Prytanis' })`, then route to `/game`. Keep the existing Load Game panel and error handling.
**Test:** `cd frontend && npm run build` succeeds.
**Done When:** The form renders with prefilled defaults and Start runs the load→patch→start sequence.
**Stuck If:** `city.load` requires a third arg — current signature is `(userId, cityId)`; report any mismatch.
- [x] Complete

### Step 3: Rebuild frontend
**Build:** Run the frontend build so the backend serves the updated UI.
**Test:** `cd frontend && npm run build`
**Done When:** Build completes, `frontend/dist/` updated.
**Stuck If:** Build errors — report the first error.
- [x] Complete

### Final Step: Verify spec Done when items
**Build:** No new code. Confirm all spec `**Done when:**` items are met.
**Test:** `cd backend && py -m pytest tests/ -q` (every `[automated]` item has a committed test from Slices 1–3). For `[human-required]` items — the New-Game form display, the briefing-restored "attitude" in a live/stub audience — capture evidence (screenshot/transcript) for inspector; a person judges.
**Done When:** Every `[automated]` criterion passes via its committed test; every `[human-required]` criterion has captured evidence.
**Stuck If:** An automated criterion fails and the cause is not clear from the output.
- [x] Complete

---
⛔ Final slice complete. Run **inspector** for final sign-off.

✅ Inspector: PASS — 2026-05-29 — 12/12 automated criteria pass (full suite 258 passed); 1 human-required item (New-Game form display) evidence captured. See output/inspect/Inspect_player-identity_Final_2026-05-29.md
