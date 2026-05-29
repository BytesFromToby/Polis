# Blueprint: Faction Descriptions
Spec: Planning/specs/faction-descriptions_spec.md
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

## Slice 1: Faction description data (model, serializer, loader, content)
**Scope:** Every faction carries a `blurb` and `description` end to end — model, JSON data (all 41), serializer round-trip, and the loader.

### Step 1: Add fields to the Faction model
**Build:** In `backend/engine/models.py`, add to the `Faction` dataclass two fields with defaults: `blurb: str = ""` and `description: str = ""`. Place them after `relationships` (before the deal-commitment fields) so they read as descriptive metadata.
**Test:** `cd backend && py -c "from engine.models import Faction, Leader; f=Faction(id='x',name='X',domain_primary='d',leader=Leader(name='L')); print(repr(f.blurb), repr(f.description))"`
**Done When:** Prints `'' ''` — both fields exist and default to empty string.
**Stuck If:** Field ordering breaks an existing positional `Faction(...)` constructor call (search for positional construction).
- [x] Complete

### Step 2: Carry the fields through serializer + loader
**Build:** In `backend/serializer.py`: add `"blurb": faction.blurb` and `"description": faction.description` to `serialize_faction`, and `blurb=d.get("blurb", "")`, `description=d.get("description", "")` to `deserialize_faction`. In `backend/loaders.py` (the `Faction(...)` build around line 84), add `blurb=fc.get("blurb", "")` and `description=fc.get("description", "")`.
**Test:** Covered by Step 4's committed tests.
**Done When:** Serializer emits both keys; deserializer and loader read them with `""` fallback.
**Stuck If:** `deserialize_faction` is shared by a snapshot path that would error on the new keys (it uses `.get`, so it should not).
- [x] Complete

### Step 3: Transcribe all 41 factions from theming.md
**Build:** For every faction object in `backend/data/factions.json`, add a `"blurb"` and a `"description"` key, transcribed from its entry in `Planning/reference/theming.md` ("Factions by domain"). Match by faction **name** (e.g. data `id: "eumelidai"` → name "The Eumelidai"). For each theming.md entry of the shape:
> **Name** — *gloss*
> Identity sentence.
> Character: …
> Leader: …
set `blurb` = the gloss text (the italic part after the em-dash on the name line, transcribed as written including its inner quotes), and `description` = the identity sentence (the line beneath the name line, before "Character:"). Do not invent text; copy from theming.md. All 41 factions must be covered.
**Test:** Covered by Step 4's committed tests (non-empty for all 41 + spot checks).
**Done When:** Every faction in `factions.json` has non-empty `blurb` and `description`.
**Stuck If:** A faction id in `factions.json` has no matching name in theming.md — stop and report which id.
- [x] Complete
**Deviation:** Transcribed the 41 blurb/description pairs via a one-off UTF-8 script (run then deleted) rather than hand-editing the JSON — same result (all 41 keys added from theming.md), safer for em-dash/quote escaping.

### Step 4: Committed tests — data, serializer, loader, seed
**Build:** Create `backend/tests/test_faction_descriptions.py` with tests that:
(a) `Faction` defaults `blurb`/`description` to `""`;
(b) load `backend/data/factions.json` → every one of the 41 records has non-empty `blurb` and `description`;
(c) spot checks: the `eumelidai` record's blurb contains "well-flocked" and description contains "senior clan"; the `silverbench` record's blurb contains "money-changers" and description contains "bankers at their tables";
(d) `serialize_faction` → `deserialize_faction` round-trips `blurb` and `description` unchanged;
(e) `load_state_from_json("backend/data")` (resolve the path like `tests/test_seed_official.py` does with `BACKEND_DIR`) yields a faction whose `blurb`/`description` are populated;
(f) `seed_official_cities` into an in-memory DB → the seeded official "Polis" `factions_json` carries `blurb`/`description` for `eumelidai` (proves the seed→serialize path).
**Test:** `cd backend && py -m pytest tests/test_faction_descriptions.py -q`
**Done When:** All cases pass.
**Stuck If:** A spot-check string does not match because theming.md wording differs — re-read theming.md and use its exact text; report if the faction is genuinely absent.
- [x] Complete

---
⛔ End of Slice 1. Run **inspector** on this slice before continuing.

---

## Slice 2: Display + prompt injection
**Scope:** The blurb shows in the left panel, the description shows on audience open, and the description is in the audience system prompt.

### Step 1: Inject the faction description into the audience prompt
**Build:** In `backend/engine/llm/prompt_builder.py`, add the faction's `description` to the system prompt. In `SYSTEM_TEMPLATE`, after the line `{faction_name} is a {domain} organisation.{city_desc}`, add a `{faction_desc}` slot. In `build()`, compute `faction_desc = f"\n{faction.description.strip()}" if getattr(faction, "description", "").strip() else ""` and pass it to `.format(...)`. Empty description → empty string (line omitted cleanly, no placeholder).
**Test:** Covered by Step 2's committed test.
**Done When:** A faction with a `description` has that text in the built prompt; an empty one adds nothing.
**Stuck If:** `SYSTEM_TEMPLATE.format` raises a KeyError — ensure `faction_desc` is passed.
- [x] Complete

### Step 2: Committed test — description in prompt / omitted when empty
**Build:** In `backend/tests/test_llm.py` (TestPromptBuilder) or `test_faction_descriptions.py`, add: build a prompt for a faction with `description="The senior clan: vast estates."` → assert that text is in the prompt; build for a faction with `description=""` → assert no blank artifact (e.g. prompt has no double-blank line where the desc would go, and the faction-org line is followed by the expected next section). Use the existing `_build`/MagicMock-db pattern.
**Test:** `cd backend && py -m pytest tests/test_llm.py tests/test_faction_descriptions.py -q`
**Done When:** Both assertions pass.
**Stuck If:** The empty-case assertion is brittle — assert on presence/absence of the description text rather than exact whitespace.
- [x] Complete

### Step 3: Show the blurb in the left-panel faction block
**Build:** In `frontend/src/views/GameView.vue`, in the faction block (around line 42, near the leader name / before or after the trait list), render the faction's blurb: `<div class="faction-blurb" v-if="f.blurb">{{ f.blurb }}</div>`. Add a small muted style (mirror `.faction-leader` / `.last-action`). Empty blurb renders nothing (the `v-if`).
**Test:** `cd frontend && npm run build`
**Done When:** Build succeeds; the block renders `f.blurb` when present.
**Stuck If:** `f.blurb` is undefined in the bound data — confirm `serialize_faction` change landed and the state endpoint carries it.
- [x] Complete

### Step 4: Show the description on audience open
**Build:** In `frontend/src/components/AudienceModal.vue`, display the faction's description near the top of the audience (e.g. under the modal title, above Step 1). The prop `faction` is the full object, so use `faction.description`: `<div class="audience-desc" v-if="faction.description">{{ faction.description }}</div>`. Add a small muted style. Empty → nothing.
**Test:** `cd frontend && npm run build`
**Done When:** Build succeeds; the modal renders `faction.description` when present.
**Stuck If:** `faction.description` is undefined — confirm GameView binds `audienceFactionObj` (it does, from `snapshot.factions`).
- [x] Complete
**Deviation:** Ran `npm run build` once after Steps 3+4 (both frontend) rather than per-step — same verification.

---
⛔ End of Slice 2. Run **inspector** on this slice before continuing.

---

## Final Slice: Refresh the official city + full verification
**Scope:** New games carry the descriptions; full suite green; human-required UI evidence captured.

### Step 1: Refresh the seeded official "Polis" city
**Build:** The seeder skips an already-seeded city, so the existing official row in `backend/polis.db` predates the new fields. Delete **only** the `is_official=True` city named "Polis" from `backend/polis.db` so it re-seeds from the updated `factions.json` on next server start. This is safe and regenerable: user games run on *copies* of the template (city.load), not the official row; do not touch user-created or published-by-user cities or any `sim_runs`/snapshots. Use a short script: open `polis.db`, `DELETE FROM cities WHERE is_official=1 AND city_name='Polis'`, commit. Then trigger a re-seed (start the server briefly, or call `db.seed.seed_official_cities` against the live DB) and confirm the official Polis row exists again with `blurb`/`description` in its `factions_json`.
**Test:** `cd backend && py -c "import sqlite3,json; c=sqlite3.connect('polis.db'); r=c.execute(\"SELECT factions_json FROM cities WHERE is_official=1 AND city_name='Polis'\").fetchone(); f=json.loads(r[0]); k=next(iter(f)); print('blurb' in f[k], 'description' in f[k], bool(f[k].get('blurb')))"`
**Done When:** Prints `True True True` — the refreshed official city's factions carry populated descriptions.
**Stuck If:** Deleting the row hits a foreign-key/constraint error, or a non-official city would be affected — stop and report.
- [x] Complete

### Final Step: Verify spec Done when items
**Build:** No new code. Confirm all spec `**Done when:**` items are met.
**Test:** `cd backend && py -m pytest tests/ -q` (every `[automated]` item has a committed test). For `[human-required]` items — blurb in the left panel, description on audience open — run the app (`py -m uvicorn api.server:app`, frontend already built) and capture screenshots via Playwright for inspector; a person judges. Remember to stop any server you start (PowerShell `Stop-Process`, not pkill).
**Done When:** Every `[automated]` criterion passes via its committed test; every `[human-required]` criterion has captured evidence.
**Stuck If:** An automated criterion fails and the cause is not clear from the output.
- [x] Complete

---
⛔ Final slice complete. Run **inspector** for final sign-off.

✅ Inspector: PASS — 2026-05-29 — 7/7 automated criteria pass (full suite 266 passed); 3 human-required items (left-panel blurb, empty-blurb graceful, audience description) evidence captured. See output/inspect/Inspect_faction-descriptions_Final_2026-05-29.md
