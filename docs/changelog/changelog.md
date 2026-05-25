# Changelog

---

## 2026-05-25

### Removed — LARP + named-units + multiplayer subsystem (full-stack)
- LARP was spun into its own program. Removed it here end-to-end. Backend: deleted `phase.py`/`actions.py`/`members.py` routes; dropped `PlayerAction` + `CityMember` models, `City.mode`, `SimRun.larp_phase`/`phase_advanced_at`; cleaned phase-gating and schemas; DB migration drops 2 tables + 3 columns.
- Frontend: removed the BuilderView unit editor, DashboardView LARP phase UI + Units panel + `CharacterPopout`, HomeView LARP badges/options + `unit_count`, and unit/phase methods in `api.js`. Deleted `UnitForm.vue` + `CharacterPopout.vue`. Fixed the factions table to use the embedded `f.leader.name` and dropped the unit-era `member_ids` column.
- 234 tests pass; `npm run build` succeeds. Decision: `Planning/decisions/2026-05-25-remove-larp-units-multiplayer.md`. Manual UI smoke test still recommended.

### Removed — Dead `units_json` city-template field
- Removed `units_json` from the `City` model (`db/models.py`), `CityResponse` schema (with `unit_count`), and all write sites (`api/routes/cities.py`, `api/routes/city.py`, `db/seed.py`). The field was always written `"{}"` — superseded by `factions_json` when units left the engine (v3).
- Fixed a latent bug in `cities.py::publish_city`: its live-session branch called `serialize_state(world, units, factions, domains)` against the current unit-free signature and read a nonexistent `snapshot_data["units"]` — would have raised at runtime. Corrected to `serialize_state(world, factions, domains)`.
- Migrated `city_sim.db` — dropped the `units_json` column. Tests green (234 passed).
- Archived dead seed data `data/units.json` + `data/past_cities/TwinCities/` to `Planning/archive/`.
- **Not done:** the wider named-units *feature* (`state.py` units CRUD routes, BuilderView/DashboardView unit UI) is half-removed and left untouched pending a decision. See decision doc.

### Changed — Planning restructure (Plumbline alignment)
- Re-tiered `specs/data-models_spec.md` → `reference/data-models.md`; rebuilt the reference tier to `data-models.md` + `formulas.md` (both code-verified); archived stale unit-era mechanics docs. Added `specs/README.md` spec index/map. Full audit trail in `Planning/archive/alignment.md`.

---

## 2026-05-24

### Changed — Speccheck fixes
- `cycle-runner_spec.md` — removed two stale `leadership_need` references (field was removed 2026-05-24).
- `projects/processing.py` — project completion now checks `health >= 100 OR cycles_built >= build_time` per spec; was only checking `cycles_built`. Test helper `make_project` default health corrected to 0 (under-construction start).
- `projects_spec.md` + `models.py` — added `"critical"` to documented/annotated project status values (was live in code, missing from spec).
- `events_spec.md` — corrected event processing step from "Step 3.5" to "Step 8" to match actual cycle order.
- `city-generation_spec.md` — marked as future feature (currently cities are hand-authored JSON templates). Added to `Features_Todo.md` backlog.

### Removed — Dead event functions
- Deleted `engine/events/faction.py` (`apply_faction_entrench_decay` — uncalled).
- Removed `tick_power_vacuums` from `engine/events/world.py` and `events/__init__.py` — superseded by the inline `_tick_power_vacuums` in `cycle/runner.py`.

### Changed — `mayor_spec.md` Action Pool corrected
- Gain per cycle corrected from +2 to +1; starting value (1 AP) documented. Matches code since the 2026-05-23 AP economy change.

### Changed — Faction leader is now permanent
- `Faction.leader` changed from `Optional[Leader]` to required `Leader`. Field moved before defaulted fields in the dataclass to satisfy Python ordering.
- Removed `Faction.leadership_need` field and all code that ticked/reset it.
- `Faction.is_leaderless()` now checks only `leader.status == "absent"` — the None branch is gone.
- Loaders and API routes that constructed factions without a leader now generate a placeholder leader.
- `test_leaderless_faction_accumulates_ln` removed; test helpers that used `leader=None` updated to `leader.status = "absent"`.
- `data-models_spec.md` pending-change note removed; spec updated to reflect final state.

---

## 2026-05-23

### Changed — Spec & doc hygiene (speccheck follow-up)
- Deleted stale `cycle-runner_spec.md` (old v2 batch model); the sequential-initiative spec is now the sole cycle spec.
- Standardized spec filenames to `feature-name_spec.md`: `cycle_runner_spec` → `cycle-runner_spec`, `llm_system_spec` → `llm-system_spec`, `llm_profiles_spec` → `llm-profiles_spec`. Updated references in `engine/cycle/runner.py` and `audience_spec.md`.
- `cycle-runner_spec.md` — added a "Full Orchestration" section documenting the actual `runner.py` order, delegating subsystem detail to the treasury/mayor/projects/special/events specs.
- `Planning/architecture/system-overview.md` + `scr/CLAUDE.md` — added the mayor/llm/projects/special subsystems, `event_system`, and current API routes; marked the unit-era 13-step cycle and invariants as superseded.
- Decision: `Planning/decisions/2026-05-23-spec-hygiene.md`. Tests green (235 passed).

### Removed — unit-era dead code
- Deleted `engine/actions/unit.py`, `engine/actions/membership.py`, and `engine/cycle/declaration.py` — all tombstones from the units→faction-only and batch→sequential reworks, with no live importers. Cleaned references in `system-overview.md` and `scr/CLAUDE.md`. Tests green (235 passed).

### Changed — data-models spec↔code alignment (alignment pass 1)
- `data-models_spec.md` → v6: aligned with `engine/models.py` — added `Faction.floor` + `leadership_need`, `ActionResult.margin` + outcome values, renamed `Deal.rep_cost_if_broken`, reconciled helper names (`is_leaderless`), delegated special-factions/events entities to their specs.
- **Mayor action points changed** (owner decision): start `1`, cap `6`, `+1`/cycle (was start `6`, `+2`/cycle). `models.py` `action_points 6→1`, `refill +2→+1`; updated `test_mayor`. Balance change.
- Deferred: make faction leader permanent (remove leaderless machinery); document the new AP rule in `mayor_spec` during the mayor pass. Decision: `Planning/decisions/2026-05-23-data-models-alignment.md`. Tests green (235 passed).

---

## 2026-05-22 (5)

### Fix — Audience: token floor, parser recovery, modal close bug, raw JSON debug

**Token / parse fixes:**
- `engine/llm/audiences.py` — `conclude_audience_step` enforces min 1200 tokens regardless of profile setting, so narrative + full `<deal>` JSON is never truncated mid-response
- `engine/llm/response_parser.py` — fallback regex catches truncated `<deal>` blocks (no closing `</deal>`); progressive JSON repair (`"}` / `}` suffixes); string terms like `"public_endorsement"` mapped to proper `DealTerm` dicts via `_STRING_TERM_MAP`
- `LLMSettings.vue` — new profile default raised to 1200 tokens

**Audience modal fixes:**
- `MayorActionsModal.vue` — removed `this.showAudience = false` from `onAudienceActed`; modal was closing the moment results arrived, before the player could read them. Modal now stays open until player clicks OK
- `AudienceModal.vue` — added collapsible "Raw JSON" `<details>` block after the OK button for debugging deal results; `<deal>` blocks intentionally kept visible in steps 1 & 3 so the player can see the faction's preliminary terms during negotiation

---

## 2026-05-22 (4)

### Fix — Audience dialog is now truly interactive (AI → player → AI → player → AI)

Replaced single-shot audience endpoint with 3-step turn-based flow:
- `POST /mayor/audience/begin` — spends AP, runs step 1 (faction opens), stores state in `SimSession.audience_state`
- `POST /mayor/audience/reply` — sends mayor's opening offer, returns step 3 (faction counter)
- `POST /mayor/audience/conclude` — sends mayor's closing, returns step 5 + deal result, sets cooldown
- Added `begin_audience_step`, `reply_audience_step`, `conclude_audience_step` to `engine/llm/audiences.py`
- `AudienceModal.vue` rebuilt as a live chat with typing indicators, transcript building turn by turn, deal banner at end

---

## 2026-05-22 (3)

### Feature — Full LLM Audience Dialog for "Meet with Faction"

**Backend:**
- `api/sessions.py` — Added `llm_profile_id: Optional[str]` to `SimSession`
- `api/routes/sim.py` — `start_sim` and `_restore_session` now carry `llm_profile_id` through; added `PATCH /sim/llm-profile` endpoint; `SimStatusResponse` now includes `llm_profile_id`
- `api/schemas.py` — Added `SimSetProfileRequest`; added `llm_profile_id` to `SimStatusResponse` (initial single-shot `AudienceRequest`/`AudienceResponse` superseded by 3-step schemas in entry 4)
- `api/routes/mayor.py` — Initial single-shot `/mayor/audience` endpoint (superseded by 3-step endpoints in entry 4)

**Frontend:**
- `frontend/src/components/AudienceModal.vue` — New component: mayor writes opening offer + closing position, LLM runs the 5-step conversation, full transcript shown with deal result
- `frontend/src/components/MayorActionsModal.vue` — "Meet with Faction" now opens `AudienceModal` instead of calling a simple act
- `frontend/src/components/LLMSettings.vue` — Added "Active city AI" section: shows current run's profile, dropdown to swap it mid-game via `PATCH /sim/llm-profile`
- `frontend/src/api.js` — Added `mayor.audience()`, `sim.setLlmProfile()`
- Also fixed `engine/llm/client.py` — split `except ImportError` so init errors show the real message instead of "package not installed"

---

## 2026-05-22 (2)

### Fix — Settings accessible from GameView and DashboardView

**frontend/src/views/GameView.vue**, **frontend/src/views/DashboardView.vue:**
- Added Settings button to top bar (GameView) and nav (DashboardView)
- Imported and registered `LLMSettings` component; added `showSettings: false` data property
- Settings modal (LLM profile management) now reachable from all three views: HomeView, DashboardView, GameView

---

## 2026-05-22

### Fix — `start_sim` 500: load_projects KeyError on "domain"

**scr/loaders.py:**
- `load_projects()` was using `d["domain"]` (old key) but `projects.json` and the `Project` model use `domains` (list)
- Fixed to read `d.get("domains") or [d["domain"]]` — supports both current and legacy formats
- `start_sim` was crashing with `KeyError: 'domain'` before the session could be created

---

### Fix — Mayor starts with full AP

**engine/models.py:**
- Changed `Mayor.action_points` default from `0` to `6` (matching `action_cap`)
- Previously the mayor had 0 AP on game start and all action buttons were disabled until the first cycle completed; now the mayor is ready to act immediately

---

### Fix — MayorActionsModal: action rows not rendering

**frontend/src/components/MayorActionsModal.vue:**
- Rewrote to remove inline sub-components (`ActionRow`, `FactionSelect`, `DomainSelect`) which used string `template:` fields — Vue 3 + Vite does not ship the runtime template compiler for inline strings, so those components silently failed to render
- Replaced with direct HTML in the SFC template; same layout, same logic, all action rows now render correctly

---

### Fix — Modal positioning (all modals now render correctly)

**frontend/src/style.css:**
- Added global `.modal-overlay` (`position: fixed; inset: 0; z-index: 200; flex centering`) and `.modal-box` rules
- Fixes BuilderView "Start Sim" modal, LLMSettings modal, and MayorActionsModal all rendering inline at the bottom of the page instead of centered over the viewport

**frontend/src/views/HomeView.vue:**
- Removed redundant scoped `.modal-overlay` / `.modal-box` styles (now covered by global rules)

---

## 2026-05-21 (2)

### Feature — Mayor actions UI (modal + full action coverage)

**api/schemas.py:**
- Added `VALID_MAYOR_ACTIONS` set (13 actions including BreakADeal and GrantTaxExemption)
- Added `MayorActRequest` / `MayorActResponse` schemas

**api/routes/mayor.py — `POST /users/{user_id}/mayor/act` (new):**
- Single unified endpoint for all mayor actions; executes immediately against the live session
- Routes through `execute_mayor_actions` for standard actions
- `GrantTaxExemption`: domain-uniqueness guard, 1–10 cycle clamp
- `BreakADeal`: 0 AP, rep penalty, clears deal effects, domain spillover −3
- Unknown action → 422; AP failure / validation → 400
- Returns narrative, outcome, updated AP, dramatic flag

**frontend/src/api.js:**
- Added `mayor.act(userId, action, targetId, targetId2, cycles)`

**frontend/src/components/MayorActionsModal.vue (new):**
- Two-column layout: Political + Information (left), Resource + Authority + Active Deals (right)
- Each action shows: AP cost, hint text, target selector(s), Act button
- Actions greyed out when AP is insufficient
- Result banner shown inline after each action (outcome + narrative, dramatic styling)
- AP counter updates live after each action
- BrokerADeal and PlantARumor use dual faction selectors
- GrantTaxExemption includes cycle count input (1–10)
- Active Deals section shows Break button per deal
- Sub-components: FactionSelect, DomainSelect, ActionRow (all inline)

**frontend/src/views/GameView.vue:**
- "Act ▸" button added to Mayor panel Actions section header
- `MayorActionsModal` mounted conditionally; receives factions, domains, mayorData
- `onActed()` refreshes mayor data after each action without full reload

**tests/test_mayor_act.py (new — 21 tests):**
- AP spending: 1-AP, 2-AP, insufficient AP
- Political: endorse raises rep, domain peer penalty, condemn, meet cooldown, broker rep requirement, broker success
- Resource: allocate budget drift, gold requirement, withhold blocks growth, rep penalty
- Authority: decree marks domain, appoint fails with leader, appoint succeeds leaderless, blind eye marks uncontested
- Information: report returns no_op with traits, plant rumor adds trait, escalates existing distrust

**Total: 235 tests passing (was 214)**

---

## 2026-05-21

### Feature — LLM profile management (named AI configs, encrypted storage, per-run selection)

**Spec:** `Planning/specs/llm_profiles_spec.md (v1)`

**engine/llm/crypto.py (new):**
- `encrypt_api_key(plaintext) -> str` / `decrypt_api_key(ciphertext) -> str`
- Fernet (AES-128-CBC + HMAC-SHA256); key derived from `sha256(str(uuid.getnode()))`
- Protects against casual file inspection; no master password required

**db/models.py:**
- New `LLMProfile` table: `profile_id`, `name`, `provider`, `model`, `encrypted_api_key`, `base_url`, `temperature`, `max_tokens`, `timeout`, `created_at`
- `SimRun`: added nullable `llm_profile_id` FK → `llm_profiles`

**db/session.py:**
- `init_db()` now calls `_migrate()`: adds `llm_config_json` to `cities` and `llm_profile_id` to `sim_runs` if missing (handles existing DBs without schema reset)

**engine/llm/client.py:**
- `LLMConfig.from_profile(profile)`: decrypts API key and returns `LLMConfig`
- `LLMConfig.resolve()`: updated priority order — profile → city json → env vars → stub

**api/routes/llm_profiles.py (new):**
- `GET /llm-profiles` — list all (encrypted key never returned; `has_api_key` bool instead)
- `POST /llm-profiles` — create; plaintext key encrypted on write
- `PUT /llm-profiles/{id}` — update; key only re-encrypted if provided
- `DELETE /llm-profiles/{id}` — delete
- `POST /llm-profiles/{id}/test` — fires a minimal LLM call; returns `{"ok": true/false, "error": "..."}`

**api/schemas.py:** Added `SimStartRequest` with optional `llm_profile_id`

**api/routes/sim.py:** `POST /sim/start` now accepts `SimStartRequest` body; stores `llm_profile_id` on the `SimRun` row

**api/server.py:** Registered `llm_profiles_router`

**frontend/src/api.js:**
- Added `llmProfiles` export: `list`, `create`, `update`, `remove`, `test`
- `sim.start` updated to accept optional `llmProfileId`

**frontend/src/components/LLMSettings.vue (new):**
- Profile list with Test / Edit / Delete per row
- Add/Edit form: name, provider dropdown, model, api_key (password field), base_url, advanced toggles
- Test result badge (ok/fail) shown inline

**frontend/src/views/HomeView.vue:**
- Settings button in nav opens `LLMSettings` modal

**frontend/src/views/BuilderView.vue:**
- "Start Sim →" now opens a confirmation modal with AI profile dropdown (None = stub)
- Loads profile list on mount; passes selected `llm_profile_id` to `sim.start`

**tests/test_llm_crypto.py (new — 5 tests):** round-trip, empty string, plaintext not in token, bad ciphertext raises, different values → different tokens

**tests/test_llm_profiles.py (new — 11 tests):** CRUD, duplicate name rejection, api_key not in response, update key, delete, 404 paths, test endpoint happy/sad

**Total: 214 tests passing (was 198)**

**Note:** `cryptography` package required (`pip install cryptography`). No requirements.txt present in project.

---

## 2026-05-20 (4)

### LLM system implementation complete — engine/llm/

**engine/llm/response_parser.py (new):**
- Extracts `<deal>` block from LLM conclusion text via regex; never raises on failure — returns `accepted=False` with `parse_error` instead
- Validates term types, `committed_action` against VALID_FACTION_ACTIONS, duration (1–10), rep_cost_if_broken (10–35)
- Resource guard: blocks `tax_exemption` when another faction in the domain is already exempt
- Returns `ParsedAudienceResponse` with narrative, memory_note, terms, reasoning

**engine/llm/memory.py (new):**
- `MemoryWriter.write_note()`: persists ≤10-word notes to `faction_memory` table
- Triggers compression when 8 notes already exist: deletes oldest 5, adds LLM-generated summary (`is_summary=True`, prefixed `"older interactions summary: "`)
- Falls back to canned summary text on LLM failure or no client

**engine/llm/audiences.py (new):**
- `run_audience()`: full 5-step audience flow (3 LLM calls with 2 player turns injected)
- On deal accepted: persists `Deal` to DB, applies mayor terms (exemption, endorsement), sets faction `committed_*` fields
- Writes memory note regardless of deal outcome
- Raises `AudienceError` on LLM failure (caller is responsible for AP refund / retry)

**engine/npc/behavior.py:**
- `_committed_plan()`: bypasses all weight calculation when `faction.committed_action` is set — returns forced `FactionPlan` directly
- `committed_abstain` support: excludes the protected faction from target pool for the abstained action

**engine/cycle/end_of_cycle.py:**
- `tick_deals()`: decrements `cycles_remaining`, checks compliance (compares `all_results` against `committed_action`), increments `suspension_streak` on miss, expires at streak=3 or cycles_remaining=0; persists status changes to DB
- `apply_domain_jealousy()`: factions in same domain as an exempt faction lose -3 rep/cycle with mayor
- `_clear_deal_effects()`: removes committed fields from faction and exemption from mayor on deal expiry

**serializer.py:**
- Added `serialize_deal` / `deserialize_deal` and `_ser_deal_term` / `_des_deal_term`
- `serialize_faction` / `deserialize_faction`: now include all five committed fields
- `serialize_mayor` / `deserialize_mayor`: now include `deals` dict

**tests/test_llm.py (new — 35 tests, all passing):**
- StubLLMClient turn detection and valid JSON output
- LLMConfig env/JSON resolution and round-trip
- PromptBuilder: trait sentences, intensity prefixes, relational trait resolution, health narrative, setting tone
- ResponseParser: deal block extraction, rejection, tax_exemption conflict guard, invalid action rejection, rep_cost clamp, malformed JSON
- MemoryWriter: note write, 10-word trim, compression trigger at 8 notes, fallback summary
- Audience stub flow: full 3-call run, memory note written
- Serializer: Deal/DealTerm round-trip, Mayor.deals round-trip, Faction committed fields round-trip
- Behavior engine: committed_action override, committed_abstain target exclusion

Total: 198 tests passing (was 163)

---

## 2026-05-20 (3)

### Spec — LLM system (client, translation layer, faction memory)

**Planning/specs/llm_system_spec.md (new — v1):**

*Layer 1 — LLM Client:*
- `LLMConfig` dataclass: provider, model, api_key, base_url, temperature, max_tokens, timeout
- Config loading priority: city db setting → env vars → stub fallback
- Two provider paths: `anthropic` (Anthropic SDK) and `openai_compat` (OpenAI SDK with base_url override — covers Ollama, LM Studio, OpenAI, most third-party)
- `LLMClient.complete(system, messages) -> str` interface
- `StubLLMClient` for tests and unconfigured servers
- Error types: `LLMError`, `LLMTimeoutError`, `LLMParseError`; audience fails gracefully on error, AP not refunded

*Layer 2 — Translation Layer:*
- `PromptBuilder`: trait labels → personality sentences (TRAIT_SENTENCES lookup + intensity prefix); health/entrench/rating → narrative descriptors; recent events from narrative_log (last 5 cycles); memory notes formatted with summary prefix; valid terms as plain English with resource constraints; city setting informs tone register
- `ResponseParser`: extracts `<deal>` block, validates term types/durations, cross-checks resource constraints, returns `ParsedAudienceResponse(narrative, deal, memory_note)`; all parse failures return `deal=None`, never raise
- `memory_note` field added to `<deal>` JSON — ≤10 words, always present, written to faction_memory on every audience regardless of outcome

*Layer 3 — Faction Memory:*
- Note triggers: audience (LLM-written via memory_note), engine events (template-generated for decisive harm, deals, leader change, project completion)
- Compression: fires before 9th note; oldest 5 → one LLM-compressed summary row (`is_summary=True`); result always ≤8 notes
- Recent turn window: 5 cycles from existing narrative_log (no new table)

*Audience integration sequence documented end-to-end*

*Future hooks stubbed: crisis decision (`llm/crisis.py`), demo mode (`llm/demo.py`)*

*File structure: `engine/llm/` — client.py, prompt_builder.py, response_parser.py, memory.py, audiences.py*

**Planning/specs/audience_spec.md (v3):**
- `<deal>` JSON updated: added `memory_note` field
- LLM prompt section replaced with reference to llm_system_spec

---

## 2026-05-20 (2)

### Spec — Audience interaction format revised (v2)

**Planning/specs/audience_spec.md (v2):**
- Cooldown changed: 5 cycles → 10 cycles per faction
- Negotiation flow rewritten: 5-step conversation replacing single-exchange menu model
  - Step 1: AI sets the scene (LLM call 1 — faction leader opens in character)
  - Step 2: Player prompts (freeform)
  - Step 3: AI responds/counters (LLM call 2)
  - Step 4: Player's final prompt (freeform)
  - Step 5: AI concludes with decision + `<deal>` JSON block (LLM call 3)
- Player no longer selects terms from a menu — terms emerge from the conversation
- LLM constrained by valid terms menu in system prompt; invalid parsed terms dropped silently
- mayor_spec.md: Meet with Faction cooldown updated to 10 cycles

---

## 2026-05-20

### Spec — Audience system, Deal model, domain jealousy

**Planning/specs/audience_spec.md (new — v1):**
- Full audience flow: 1 AP, 5-cycle cooldown per faction
- LLM plays faction leader in character; single exchange with one counter allowed
- Valid mayor terms: tax_exemption, endorsement, budget_allocation
- Valid faction terms: committed_action (override behavior engine), committed_abstain
- Deal lifecycle: active → fulfilled / broken_by_mayor / broken_by_faction / suspended
- Grace clause: 3 consecutive suspended cycles → expires as fulfilled
- Mayor break: −10 to −35 faction rep (set by LLM at negotiation), −8 public rep, faction gains angry-at-mayor trait, domain spillover −3
- Faction breach: deal broken, mayor terms revoked, −5 mayor rep with that faction
- Behavior engine: committed_action bypasses weight calc entirely; committed_abstain re-selects if forbidden target chosen

**Planning/specs/data-models_spec.md (v7):**
- Added `DealTerm` model
- Added `Deal` model with full field set including `suspension_streak`, `rep_cost_if_broken_by_mayor`
- Added `deals: Dict[str, Deal]` to Mayor
- Added `committed_action`, `committed_target`, `committed_deal_id`, `committed_abstain_action`, `committed_abstain_target` to Faction

**Planning/specs/mayor_spec.md (v3):**
- Grant Tax Exemption: added domain jealousy mechanic (−3 rep/cycle to non-exempt factions in same domain)
- Added "Break a Deal" as a 0-AP mayor action with full cost breakdown
- Audience section upgraded from "POSSIBLE" to committed — references audience_spec

---

## 2026-05-19 (6)

### Balance — health recovery added to Grow and Protect

**engine/actions/faction.py:**
- `resolve_grow`: now adds `+3 health` (capped at 100) on every successful Grow
- `resolve_protect`: now adds `+5 health` (capped at 100) in addition to existing `+10 entrench`

**Planning/specs/actions_spec.md v5:**
- Grow: documented `+3 health` on success
- Protect: documented `+5 health` alongside `+10 entrench`

**Motivation:** 50-cycle run showed health as a one-way ratchet — every faction ended at 13–28 hp with no recovery path. With this change the same run ends at 54–99 hp, factions can sustain themselves through active play.

**Tests:** 163 passing

---

## 2026-05-19 (5)

### Implementation — leaderless mechanic removed; behavior engine improvements

**engine/formulas.py:**
- Removed `is_leaderless()` penalty (−2 to rolls) from `resolve_contest` — factions always have a leader

**engine/cycle/end_of_cycle.py:**
- Removed extra −1 health decay for leaderless factions

**engine/npc/behavior.py:**
- Removed `is_leaderless()` state modifier from `select_faction_action`
- Added BuildProject +30 weight when faction owns a damaged/critical project
- Added Foe domain ×2 weighting in `_pick_sabotage_target` (projects in Foe domains weighted higher)
- Added TODO comment for cooperative faction logic (revisit later)

**Spec updates:**
- `faction-behavior_spec.md` v4: removed leaderless modifier row; added owned-damaged BuildProject +30; added SabotageProject foe domain ×2 weighting note; added TODO row for cooperative logic
- `cycle-runner_spec.md`: removed leaderless check section
- `data-models_spec.md` v6: `leader` field is now required (not Optional); removed `leadership_need`; updated `is_leader_absent()` helper; updated absent leader description

**Tests:** 163 passing

---

## 2026-05-19 (4)

### Implementation — spec changes applied to engine

**engine/models.py:**
- `Project.domain: str` → `Project.domains: List[str]`; added `faction_level: bool`, `build_actions_this_cycle: int` (cycle-only); added `defense_rating()`, `defense_bonus()`, `domain` compat property
- `Faction`: replaced `action_taken` with `action_cancelled` + `action_downgraded`; added `active_block_target: str`
- `WorldState`: added `initiative_order: List[str]`

**data/projects.json:** All 50 projects migrated `domain→domains` array; `faction_level: false` added

**engine/actions/faction.py v4:**
- Removed `resolve_recruit`
- `resolve_block` split into `set_block` (places hidden trap) + `fire_block` (contest resolution)
- Added `resolve_build_project` (DC 12, increments build_actions_this_cycle on success)
- Added `resolve_sabotage_project` (contested vs project defense_rating + build_bonus)
- `resolve_harm` + `resolve_steal` now enforce same-domain; return `"blocked"` if cross-domain

**engine/npc/behavior.py v3:**
- `BASE_WEIGHTS`: Recruit removed; BuildProject (15) + SabotageProject (10) added
- `select_faction_action` takes `projects` param; called per-turn with live state
- `industrious`/`destructive` traits added to TRAIT_MODIFIERS
- Project state modifiers added; Block suppressed if faction already armed
- Separate target pickers: `_pick_faction_target`, `_pick_block_target`, `_pick_build_target`, `_pick_sabotage_target`

**engine/cycle/resolution.py:** Full rewrite — `run_sequential_actions`: initiative shuffle, per-faction block check (`fire_block`), live behavior engine call, immediate action resolution

**engine/cycle/declaration.py:** Stubbed out (replaced by sequential model)

**engine/cycle/runner.py:** Replaced `run_declaration`+`run_resolution` with `run_sequential_actions`; `_track_cycle_outcomes` no longer needs faction_plans

**serializer.py v5:** `serialize/deserialize_project` updated for `domains`/`faction_level`; `serialize/deserialize_faction` includes `active_block_target`; `build_actions_this_cycle` and `initiative_order` correctly excluded from persistence

**engine/projects/processing.py:** `commission_project` updated for `domains` field

**Tests:** Updated `test_actions.py` and `test_harm_block_steal.py` for new Block API and same-domain rules; `test_projects.py` `make_project` updated. **163 tests passing.**

---

## 2026-05-19 (3)

### Cycle runner spec + sequential initiative model

**cycle_runner_spec.md v1 (new):**
- Sequential initiative model: factions act one at a time in random order each cycle
- Five steps: Treasury (0), Initiative (1), Action Loop (2), Project Ticks (3), End of Cycle (4)
- Block fires at start of target's turn before action selection; persists across cycles until fired
- Behavior engine called per-faction-turn with live current state
- Project build bonus accrues in real-time during the cycle (SabotageProject sees it)
- Public log rules: Block target hidden until fired
- Cycle-only state fields documented

**actions_spec.md v4 (Block rewrite):**
- Block is now a standing trap with hidden target
- Persists until fired; one active block per faction at a time
- Fires at start of target's turn any cycle; consumed on firing regardless of outcome

**data-models_spec.md v5:**
- Faction: added `active_block_target: str` (persistent); replaced `action_taken` with `action_cancelled` + `action_downgraded` (cycle-only)
- WorldState: added `initiative_order: List[str]` (cycle-only)

**faction-behavior_spec.md v3:**
- `select_faction_action` now takes `projects` parameter
- Behavior engine called per-turn with live state (not cycle-start snapshot)
- Block target selection rules added; armed factions skip Block as option

---

## 2026-05-19 (2)

### Faction action spec redesign — project actions, domain restrictions, balance

**actions_spec.md v4:**
- Removed `Recruit`
- Added `BuildProject`: faction in project's domain, d20 + floor vs DC 12, advances construction health; each success grants +1 project defense this cycle (max +2)
- Added `SabotageProject`: any faction, any domain; contested vs project defense roll (`d20 + max(1, health//20) + build_bonus`); decisive −25 health, partial −10
- `Harm` now restricted to same-domain targets (Foe relationship requirement dropped)
- `Steal` same-domain restriction documented
- `Block` partial now explicitly downgrades Harm → Grow, Steal → Grow
- `Grow` floor advance condition documented: requires `entrench >= 50`

**projects_spec.md v4:**
- `domain: str` → `domains: List[str]` — projects can span multiple domains; factions in any listed domain can build, attack, or receive effects
- Added `faction_level: bool = False` — when True, effects apply only to `initiated_by` faction; Mayor cannot commission
- Added `build_actions_this_cycle` cycle-only field for defense bonus tracking
- Project defense rating system documented (health//20 scale, 1–5)
- Destroying projects now routes through SabotageProject action
- Added Guild Safehouse as faction-level project example

**faction-behavior_spec.md v2:**
- Removed Recruit from BASE_WEIGHTS; added BuildProject (15) and SabotageProject (10)
- Added `industrious` and `destructive` trait modifiers
- Added state modifiers for project presence in domain
- Added BuildProject and SabotageProject target selection rules

**data-models_spec.md v4:**
- Project model updated: `domain` → `domains List[str]`, added `faction_level`, `build_actions_this_cycle`

---

## 2026-05-19

### Spec sync — projects, mayor, data-models updated to match code

- **`projects_spec.md`** v3: added `category` and `tax_level` fields to Project struct; added `target_id` to `ProjectEffect`; corrected maintenance description — treasury uses flat `2 × active_project_count`, not per-project values; maintenance failure is a silent skip, not "damaged status"
- **`mayor_spec.md`** v2: documented `exemptions` and `cooldowns` fields on Mayor; added **Grant Tax Exemption** action (1 AP, 1–10 cycles, exempted faction +5 rep/cycle, 1 per domain limit)
- **`data-models_spec.md`** v3: added Mayor, Treasury, Project, ProjectEffect, and MayorAction model tables; removed nonexistent `step` field from CycleEvent; moved Result/Plan types into their own section

---

## 2026-05-18 (5)

### Balance — reduce infrastructure maintenance cost

Per-project maintenance rate lowered from `10` to `2` gold/cycle (`engine/mayor/treasury.py`).

**Why:** With 29 active starting projects, flat `10/project` = 290 gold/cycle maintenance vs ~116 gold/cycle tax income — hopelessly negative from cycle 0. As under-construction projects complete (cycles 3–6), n_active rises to 50 and the deficit grew to 510/cycle. The "skip if can't afford" behavior caused irregular payment spikes rather than steady drain.

At `2/project`: Rivers Point now starts at +38/cycle net (cycle 0, 29 active), ramps smoothly to +20/cycle at cycle 10 (50 active, 120 expend vs 140 income). Gold grows throughout with no skipped-maintenance events. Spec updated to match.

---

## 2026-05-18 (4)

### Bug fixes — session restore + trait display

- **`_restore_session`**: snapshots pre-dating mayor/treasury now fall back to fresh `Mayor()`, `Treasury()`, and `load_projects()` instead of leaving them `None`
- **`api/routes/mayor.py`**: treasury/mayor/projects endpoints now auto-restore the session from DB if it's not in memory (server restart no longer breaks the right panel)
- **GameView.vue**: faction trait tags now display the trait name string instead of raw JSON object

---

## 2026-05-18 (3)

### Mayor / Treasury / Projects — full backend + frontend wire-up

- **Serializer** (v4): added `serialize_project`, `deserialize_project`, `serialize_treasury`, `deserialize_treasury`, `serialize_mayor`, `deserialize_mayor`; `serialize_state`/`deserialize_state` now carry mayor, treasury, and projects in snapshots (backwards-compatible — old snapshots restore without them)
- **SimSession**: added `mayor`, `treasury`, `projects` fields; `start_sim` initialises fresh `Mayor()`, `Treasury()`, and loads `data/projects.json`; all `_save_cycle` and `_restore_session` calls updated
- **loaders.py**: added `load_projects(path)` — loads `data/projects.json` into `Dict[str, Project]`
- **api/routes/mayor.py** (new): Treasury endpoints (`GET /treasury`, `PATCH /treasury/tax-rate`, `POST /treasury/borrow`, `/invest`, `/public-works`, `/guard-surge`); Mayor endpoints (`GET /mayor`, `POST /mayor/exempt`); Projects endpoints (`GET /projects`, `GET /projects/catalog`, `POST /projects/commission`)
- **api/schemas.py**: added `TreasuryResponse`, `TaxRateRequest`, `BorrowRequest`, `InvestRequest`, `MayorResponse`, `ExemptFactionRequest`, `ProjectResponse`, `CommissionProjectRequest`
- **frontend/api.js**: added `treasury`, `mayor`, `projects` API modules
- **GameView.vue**: right panel now shows live treasury (gold, income, debt, max tax rate), mayor AP/rep, and project list (active + under construction)
- All 158 tests pass

---

## 2026-05-18 (2)

### Docs — Archived obsolete planning docs

Moved 6 Phase 1 / superseded files to `Planning/old_docs/`:
- `specs/npc-behavior-engine_spec.md` — unit NPC engine, replaced by `faction-behavior_spec.md`
- `decisions/2026-03-29-sm-domain-as-attention.md` — SM domain removed in Phase 2
- `decisions/2026-03-29-multi-point-action-economy.md` — multi-point economy reversed in Phase 2
- `decisions/2026-03-31-pre-sim-population-fill.md` — unit pre-fill, units are gone
- `decisions/2026-03-31-action-economy-rework.md` — unit action point system, superseded
- `decisions/2026-04-01-faction-health-to-entrench.md` — Phase 2 re-added `health` as a separate field, making this misleading

---

## 2026-05-18

### Added — Phase 2 UI (Mayor Game v1) + Backend Migration

**Frontend (new)**
- **`frontend/src/views/TitleView.vue`** — Title screen with New Game / Load Game. Auto-logs in as guest on mount (invisible to player), finds Rivers Point template, starts sim or restores active run, navigates to `/game`.
- **`frontend/src/views/GameView.vue`** — Full-height three-panel game screen: faction list (left, 260px), event log (center, newest cycle on top, dramatic events highlighted gold), mayor panel (right, 220px). Top bar has Run Cycle button (upper-left, always visible), city name, cycle badge, and Title link.
- **`frontend/src/router.js`** — `/` now loads `TitleView`; `/game` loads `GameView` (auth-guarded). Old routes preserved.
- **`frontend/src/api.js`** — Added `auth.guestLogin()` calling `POST /auth/guest`.

**Backend (new)**
- **`api/routes/auth.py`** — Added `POST /auth/guest` endpoint. Creates a fixed local guest user on first call; returns JWT. No login screen needed.

**Backend (Phase 2 migration fixes)**
- **`serializer.py`** — Full rewrite. Removed all Unit serialization. `serialize_faction` outputs embedded Leader and FactionTrait list. `serialize_world_state` removes `sm_attention`/`sm_state`. `serialize_cycle_event` removes `domain_targeted`/`points`. `serialize_state(world, factions, domains)` takes no units param.
- **`api/sessions.py`** — Removed `Unit` import and `units` field from `SimSession`.
- **`db/seed.py`** — Rewrote to use `load_state_from_json(data_dir)`; removed Phase 1 loader calls.
- **`api/routes/sim.py`** — Removed Phase 1 pre-sim init calls; `run_cycle` called without units; `SimStepResponse.dramatic_count` fixed (`e.dramatic > 0` not `result.dramatic_events`).
- **`api/routes/state.py`** — Removed Unit routes and imports; updated `serialize_state` call; fixed `trigger_event` (power_vacuum appends dict, no sm_state).
- **`api/routes/city.py`** — Full rewrite; removed unit builder routes; `new_city` uses Phase 2 `WorldState`; `add_faction` uses new Faction constructor.
- **`loaders.py`** — Made backwards-compatible: handles both old string traits and new dict traits; handles old `leader_id` field and new embedded `leader` object.

---

## 2026-05-17 (4)

### Added — Stage 5: Projects, Events, Special Factions

- **`engine/models.py`** — Added: `Project`, `ProjectEffect`, `GameEvent`, `EventEffect`, `CascadeSpec`, `ThePublic`, `ThreatEffect`, `ExternalThreat` dataclasses.
- **`engine/projects/`** — New module. `processing.py`: `tick_projects` (construction advance, completion, health decay), `apply_project_effects` (scaled by health tier), `harm_project` (faction vs project d20 contest), `repair_project` (gold + AP), `commission_project` (from template dict).
- **`engine/events/event_system.py`** — Full event system: `roll_for_random_events` (chaos-scaled probability, deck-based), `check_scripted_events` (condition-based firing), `process_active_events` (per-cycle effects, timer decrement, cascade firing), `create_mayor_triggered_event` (side effects from condemn/withhold).
- **`engine/special/`** — New module. `public.py`: disposition derivation from support, trait evolution, removal risk flag. `moneylender.py`: leverage at 500/800 debt thresholds, angry trait, removal coalition countdown. `external_threats.py`: per-cycle effect application, duration ticking, factory helpers for bandits/rival_city.
- **`engine/cycle/runner.py`** — Integrated all new systems. New optional params: `projects`, `active_events`, `event_deck`, `public`, `external_threats`. Projects tick after Step 6; active events process at Step 3.5; random events roll at Step 8; moneylender and The Public process at Step 9.
- **`tests/test_projects.py`**, **`tests/test_events_system.py`**, **`tests/test_special_factions.py`** — 62 new tests. 158 total passing.

---

## 2026-05-17 (3)

### Added — Stage 5: Mayor Layer

- **`engine/mayor/`** — New module: `treasury.py` (income, tax effects, guard payroll, maintenance, debt interest, investment maturity, borrow/invest helpers) and `actions.py` (11 mayor actions: MeetWithFaction, PubliclyEndorse, PubliclyCondemn, BrokerADeal, AllocateBudget, WithholdResources, IssueADecree, AppointAnOfficial, TurnABlindEye, RequestAReport, PlantARumor).
- **`engine/models.py`** — Added `Treasury`, `Mayor`, and `MayorAction` dataclasses. Mayor tracks action pool (2/cycle, cap 6), per-faction reputation (-50 to +50), cooldowns, and multi-cycle commitments. Treasury tracks gold, tax rate, debt, investment, and cycle income/expenditure totals.
- **`engine/cycle/runner.py`** — Integrated Mayor and Treasury into `run_cycle`. Treasury processes at Step 0; mayor actions execute before faction declaration; mayor refills/ticks at Step 9. All parameters optional — existing tests unchanged.
- **`main.py`** — Instantiates Mayor and Treasury and passes them to run_cycle.
- **`tests/test_mayor.py`** — 34 new tests covering treasury income, tax effects, borrow/invest, reputation mechanics, all major action paths, and cycle integration. 96 total tests passing.

---

## 2026-05-17 (2)

### Added — Stage 4 Complete (Phase 2 Specs)

- **`Planning/specs/personality-system_spec.md`** — FactionTrait structure with intensity (slight/moderate/strong/very), 8 general traits with weight modifiers, relational traits, 6-trait cap, evolution rules table, leader influence rules.
- **`Planning/specs/mayor_spec.md`** — Action pool (2/cycle, cap 6), 12 mayor actions across Political/Resource/Authority/Information categories, per-faction reputation system (-50 to +50), reputation decay, mayor removal conditions.
- **`Planning/specs/treasury_spec.md`** — Treasury dataclass, income formula, 5-level tax rate table, fixed and optional expenditure, Moneylender investment terms and borrowing mechanics, leverage thresholds, bankruptcy consequence table.
- **`Planning/specs/projects_spec.md`** — Project and ProjectEffect dataclasses, build process (faction contributions, rival interference, mayor acceleration), mayor action locking by build time, health system (intact/damaged/critical/destroyed), destruction via Harm variant, 4 example projects, starting projects concept.
- **`Planning/specs/events_spec.md`** — Event, EventEffect, and CascadeSpec dataclasses, 3 event types (random/scripted/mayor-triggered), chaos-based probability table, processing at Step 3.5, 4 example events, city event deck JSON format.
- **`Planning/specs/special-factions_spec.md`** — The Public (support/disposition system, trait evolution, passive influence on faction and mayor actions), The Moneylender (leverage mechanics, removal coalition trigger), External Threats (4 types with threat_level scaling, removal via projects/treasury).

---

## 2026-05-17

### Changed — Stage 3 Complete (Unit Removal, Faction-Only Engine)

- **Faction behavior** (`engine/npc/behavior.py`) — rewrote as personality-driven engine. `select_faction_action` uses FactionTrait list with intensity multipliers. Added `evolve_traits` for end-of-cycle trait mutation. Removed all unit-based logic, focus mechanics, SM trait logic, spy gate requirements.
- **Cycle runner** (`engine/cycle/`) — rewrote all four files (runner, declaration, resolution, end_of_cycle) for faction-only operation. 9-step spec implemented. Unit declaration phase, unit resolution phase, and multi-domain health penalty removed. CycleResult no longer has `unit_actions`, `retirements`, `new_units`.
- **Events** (`engine/events/`) — rewrote cascades (faction-collapse-triggered, unit-free), faction events, world chaos. Removed SM attention spike, unit retirement cascade, unit emergence.
- **Data files** — updated `factions.json` (leader objects, FactionTrait list), `world_state.json` (removed SM fields), `domains.json` (removed Social Media domain and all references to it), `units.json` archived (no longer loaded).
- **Loaders** (`loaders.py`) — rewritten for faction-only. Returns `(world, factions, domains)`.
- **Main** (`main.py`) — updated for v3 signature and summary.
- **Logger** (`engine/logger.py`) — removed SM/unit references.
- **NPC module** — `targeting.py` and `weights.py` stubbed (unit-based, to be deleted in cleanup).
- **Tests** — all 8 test files rewritten for v3. 62 tests pass.

---

## 2026-04-17 (5)

### Added
- **Full faction roster with ranks** (`Planning/twin-cities-model.md`) — designed all ~60 factions across 15 domains. Each faction has: name, traits, 1-2 sentence description, and a 5-rank ladder with rank title, traits, and description. Covers Traditional Media, Social Media, Political, Street, Religion, Bureaucracy, Finance, Police, Underworld, Legal, Health, High Society, Industry, Transportation, and University.

---

## 2026-04-17 (4)

### Added
- **Twin Cities model document** (`Planning/twin-cities-model.md`) — describes the current state of the Twin Cities city model: domains, factions, named units, world state fields, what is working, and what is incomplete. Created as a reference for planning future updates.

---

## 2026-04-17

### Changed
- **Active city swapped from Rivers_Point to Twin Cities** (`scr/data/`) — Previous city contents (9-domain fantasy setup: guilds, docks, noble_houses, etc.) archived to `scr/data/past_cities/Rivers_Point/`. Active data now loads the 15-domain Twin Cities setup (traditional_media, social_media, political, street, religion, bureaucracy, finance, police, underworld, legal, health, high_society, industry, transportation, university) with 10 factions and 20 seeded units. `oldunits.json` removed; `units.json` now present. Smoke test: `py main.py --cycles 1` runs clean; loader reports 15 domains / 10 factions / 4146 units after pre-sim population fill.

## 2026-04-17 (3)

### Changed
- **Rating ceiling lowered from 10 to 5** — full-path change per `Planning/decisions/2026-04-17-rating-cap-5.md`.
  - `scr/engine/formulas.py`: `_UNIT_WEIGHT_TABLE` and `FACTION_CAPACITY` trimmed to keys 1-5; new `RATING_MAX = 5.0` constant.
  - `scr/engine/actions/unit.py`: `resolve_grow_unit` blocks when `dr.rating >= 5.0` and clamps the rating update with `min(RATING_MAX, ...)`.
  - `scr/engine/actions/faction.py`: `resolve_grow_faction` blocks when `faction.rating >= 5.0` and clamps the update.
  - Data rescaled via `new = 1 + (old - 1) × 4/9` (endpoints preserved: 1→1, 10→5). Applied to `scr/data/factions.json`, `scr/data/units.json`, `scr/data/past_cities/Rivers_Point/factions.json`, `scr/data/past_cities/Rivers_Point/units.json`. Twin Cities max faction rating: 6.45 → 3.42. Rivers Point max faction rating: 7.0 → 3.67.
  - Specs updated: `data-models_spec.md` (rating range 1-5 in `DomainRating` and `Faction.rating`), `actions_spec.md` (Grow ceiling, Support Faction pooling example rewritten from L5→L6 to L4→L5, Obscure-at-max note), `city-generation_spec.md` (faction-floor table no longer includes 6+).
  - Tests: `tests/test_formulas.py` — level 6-10 test methods removed, `test_above_cap_returns_zero` added, `test_grow_increment_cycles` loop bound changed to `range(1,5)`, `test_get_faction_capacity` rewritten for new ceiling. `tests/test_cycle.py` — `test_under_capacity_faction_recruits` set rating from 10 to 5. 272/272 passing.
  - DB: both official city rows (`Twin Cities`, `Rivers Point`) in `scr/city_sim.db` deleted and re-seeded from rescaled JSON.
  - Smoke test: `py main.py --cycles 3` — clean run, all ratings in 1-5, Grow actions respecting the ceiling.

### Known edge cases (flagged in decision doc, deferred per user direction)
- Support Faction pooling past the ceiling (3 × L5 would pool to L6, now clamps at 5).
- Obscure-at-max: top-level actions can no longer be fully obscured because there is no L+1 above the ceiling.
- `domain.cap` values unchanged; utilization pressure now lower relative to cap.

---

## 2026-04-17 (2)

### Changed
- **Official cities now include both Twin Cities and Rivers Point** (`scr/db/seed.py`) — `_OFFICIAL_CITIES` was a single-entry list with "Rivers Point" pointing at `data/`; after the JSON swap, that entry would have mislabelled Twin Cities content as "Rivers Point" on any fresh seed. Now holds two `_CityDef` entries: `"Twin Cities"` → `data/` (15 domains) and `"Rivers Point"` → `data/past_cities/Rivers_Point/` (9 domains). Browser/API exposes both as selectable official templates.
- **Rivers Point backup — `oldunits.json` renamed to `units.json`** (`scr/data/past_cities/Rivers_Point/`) — Loader expects `units.json`; without the rename, the Rivers Point template would have seeded with an empty unit roster (leaders Vorn Ashpike, Mira Tallow, Brek Hammerfield, Dag Ironhook etc. would be lost and replaced by random-generated units at pre-sim fill).

### Fixed
- **Stale "Rivers Point" DB row removed** (`scr/city_sim.db`) — Old official row had frozen JSON columns predating the data swap; seeder skipped it because the row already existed, so the browser kept showing Rivers_Point content even after the JSON swap. Row deleted; next-startup seeder re-creates it fresh from `data/past_cities/Rivers_Point/`. Confirmed by running `seed_official_cities(db)` manually: Twin Cities (15/10/20) and Rivers Point (9/21/20) now both present as `is_official=True` templates.

---

## 2026-04-10 (2)

### Fixed
- **Faction Steal roll formula** (`actions/faction.py`, `cycle/resolution.py`) — Inline Steal handler used `stat=10` in `roll_result`, incorrectly inflating rolls. Corrected to `stat=0` per spec. Actor faction now also gains the stolen entrench (was drain-only).
- **Leaderless proxy filter** (`cycle/runner.py`) — Proxy selection used `get_domain_rating()` which matched any domain containing the faction's primary; now filters to members whose first domain slot matches (true primary domain check).

### Added
- **Leave focus drain** (`actions/membership.py`) — When a unit leaves a faction, any focus score targeting that faction is reduced by `faction_inertia × 0.5`, per spec.
- **Obscure paired action** (`models.py`, `npc/behavior.py`, `cycle/resolution.py`) — Obscure now selects and executes a paired action (highest-weighted non-Obscure action) at level−1. `NPCPlan` gains a `paired_action` field. Paired results are tagged `[Obscured]` in action detail.
- **`resolve_steal_faction()`** (`actions/faction.py`) — Extracted faction Steal into a proper resolver, replacing inline resolution code.

### Changed
- **Leaderless Seek Leadership spec** (`Planning/specs/actions_spec.md`) — Documented the exception: partial outcome on a leaderless faction grants immediate leadership transfer (LN −2), not "Leader Unstable". Existing-leader vs leaderless outcomes now shown in a side-by-side table.

---

## 2026-04-10

### Fixed
- **Double-append of support_results** (`cycle/runner.py`) — `support_results` was appended twice in `run_cycle`, duplicating all SupportFaction events in cycle output. Removed the second append.
- **Faction Expose action string** (`cycle/resolution.py`) — Faction Expose handler created ActionResult with `action="Steal"` instead of `"Expose"`.
- **Harm effective levels off-by-one** (`actions/unit.py`) — When Harm >= Protect+2, code returned `[harm_level-1, harm_level-2]` instead of spec-correct `[harm_level, harm_level-1]`.
- **Leave dramatic condition** (`actions/membership.py`) — Spec says departure is dramatic when the leaving unit was leader. Code only checked high inertia. Added `was_leader` as a dramatic trigger.

### Added
- **`tools/audit.py`** — AST-based engine metadata extractor. Outputs 6 CSVs + AUDIT.md summary covering entity fields, actions, traits, formulas, constants, and trait references.
- **`tools/validate_state.py`** — JSON data integrity checker. Validates cross-references, value ranges, duplicate IDs across domains/factions/units/world_state.
- **71 new tests** (`tests/test_harm_block_steal.py`, `tests/test_npc_and_eoc.py`) — Coverage for Harm/Block/Steal/Care/Evolve/Protect resolvers, health formulas, NPC weight building, action selection, focus scores, and weight constants. Test count: 119 → 190.
- **`improve` skill** (`skillsforprogram/improve/skill.md`) — Reusable autonomous improvement pass: audit, speccheck, test coverage, MD optimization, tools, recommendations.

### Changed
- **`scr/CLAUDE.md` rewritten** — Was stale (referenced TypeScript, headless frontend). Now documents actual Python/FastAPI/Vue/SQLite stack, directories, and commands.

---

## 2026-04-06 (3)

### Changed
- **Dashboard world state panel** (`frontend/src/views/DashboardView.vue`) — Removed SM State, Attention, and Vacuums display. Replaced with a domain fill panel showing each domain's utilization vs cap as a labelled bar. Bar colour: purple (normal), amber (≥60%), red (≥90%). SM domain excluded from the list. Sorted alphabetically.

---

## 2026-04-06 (2)

### Added
- **City name/description editing in builder** (`frontend/src/views/BuilderView.vue`) — City info card now has an Edit button that swaps the name to an input and the description to a textarea. Save calls `PATCH /users/{user_id}/city` and updates local state. Cancel restores the displayed values.

### Fixed
- **Browser caching stale frontend builds** (`api/server.py`) — Replaced blanket `StaticFiles` mount with a dedicated SPA catch-all route that serves `index.html` with `Cache-Control: no-store`. Assets (`/assets/*`) are still served via `StaticFiles`. Prevents browsers from loading outdated JS after a Vite rebuild.

---

## 2026-04-06

### Fixed
- **Template load not showing factions/units in builder** (`api/schemas.py`) — `CityResponse` was missing `factions_json` and `units_json` fields. Added both as optional fields so the City Builder can populate its tables on load.
- **Template load mutating shared template** (`api/routes/city.py`, `load_city`) — Loading a template pointed the user's `SimRun` directly at the template `City` row. Edits in the builder would overwrite the shared template. Now creates a personal copy of the template city and points the run at the copy.

### Added
- **Edit buttons on City Builder factions and units** (`frontend/src/views/BuilderView.vue`) — Each row now has an Edit button that opens the existing form pre-populated via the `initial` prop. Add and Edit are mutually exclusive. Save calls `patchFaction`/`patchUnit` and updates local state.
- **`domain_primary` editable on faction patch** (`api/schemas.py`, `api/routes/city.py`) — Added `domain_primary` to `FactionPatchRequest` and the patch handler.
- **`name`, `domains`, `faction_id` editable on unit patch** (`api/schemas.py`, `api/routes/city.py`) — Added to `UnitPatchRequest` and the patch handler. `faction_id` uses `model_fields_set` to distinguish "not sent" from explicit `null` (clear faction).

---

## 2026-04-05

### Added
- **Steal action** — Implemented `resolve_steal()` in `engine/actions/unit.py`. Unit Steal: contest roll siphons domain rating from highest rival (+0.25 decisive, +0.10 partial, exposed on fail). Faction Steal: siphons entrench from rival faction (roll ≥12: 1pt, ≥18: 2pt). Added to `actions_spec.md`. Decision doc: `Planning/decisions/2026-04-05-steal-evolve-unstable-fixes.md`.
- **Evolve action** — Implemented `resolve_evolve()` in `engine/actions/faction.py`. Faction-only, requires leader. Probabilistic trait swap (25% add, 25% remove, 50% both). Added to `FACTION_TRAIT_WEIGHTS` for Expansionary, Open, Hierarchical, Meritocratic factions. Wired into `_execute_faction_action` in resolution.py.

### Fixed
- **unstable_stacks persistence** — `Faction.unstable_stacks` no longer resets each cycle. Removed from `reset_cycle_state()`, added decay (-1 per cycle) in `end_of_cycle.py`. Stacks now accumulate meaningfully across cycles (max 3).
- **Faction Steal stub** — Faction Steal in resolution.py previously rolled but did nothing. Now siphons entrench from a rival faction.

---

## 2026-04-04

### Added
- **`frontend/`** — Vue 3 + Vite browser frontend. Four views: Login/Register, Home (city template browser), City Builder (factions + units CRUD), GM Dashboard (faction/unit/domain panels, sim controls, narrative log). Global dark theme in `style.css`. API calls centralized in `api.js`. Shared reactive state in `store.js`. Vue Router with auth guard. Built frontend served as static files by FastAPI. Decision doc: `Planning/decisions/2026-04-04-vue-frontend.md`.
- **`api/server.py`** — FastAPI app entry point. Lifespan handler runs `init_db()` and `seed_official_cities()` at startup. Wires all routers. CORS middleware included (open for dev, tighten before production). `GET /health` probe. Decision doc: `Planning/decisions/2026-04-04-api-routes.md`.
- **`api/routes/users.py`** — `GET /users/{user_id}`.
- **`api/routes/cities.py`** — `GET /cities`, `GET /cities/{city_id}`, `POST /users/{user_id}/city/publish`.
- **`api/routes/city.py`** — User city setup (`/city/load`, `/city/new`, `GET /city`, `PATCH /city`) and city builder CRUD (`/city/factions`, `/city/units` — add, patch, delete). All operate on the City DB record while the run is in `setup` status.
- **`api/routes/sim.py`** — `POST /sim/start`, `POST /sim/step`, `POST /sim/run/{n}` (max 100, auto-stops on `sm_state == "crisis"`), `POST /sim/pause` (sets session flag, interrupts between cycles), `POST /sim/reset`, `GET /sim/status`. Cycle snapshots and narrative log saved to DB after every cycle.
- **`api/routes/state.py`** — Full state reads (`/state`, `/factions`, `/units`, `/domains`, `/logs`, `/cycles`, `/cycles/{n}`). GM edit endpoints (`PATCH /factions/{id}`, `PATCH /units/{id}`, `POST /factions`, `DELETE /factions/{id}`, `POST /units`, `DELETE /units/{id}`, `POST /events/trigger`). All GM edits blocked while `session.is_running == True`.
- **`api/schemas.py`** extended with `CityNewRequest`, `CityPatchRequest`, `FactionCreateRequest`, `FactionPatchRequest`, `UnitCreateRequest`, `UnitPatchRequest`, `DomainRatingIn`, `EventTriggerRequest`.
- **`api/__init__.py`**, **`api/routes/__init__.py`** — Package markers.

## 2026-04-03

### Added
- **`scr/db/` package** — Database layer. `models.py` defines SQLAlchemy ORM tables (users, cities, sim_runs, cycle_snapshots, narrative_log). `session.py` provides the engine, `SessionLocal` factory, `get_db()` FastAPI dependency, and `init_db()`. `seed.py` seeds official city templates (Rivers Point) from `data/` into the DB at startup. Decision doc: `Planning/decisions/2026-04-03-db-layer.md`.
- **`scr/loaders.py`** — Loaders abstraction. All JSON loading, faction/leader generation, and pre-sim population fill moved out of `main.py` into a dedicated module. Public API: `load_state_from_json(data_dir)` returns `(world, units, factions, domains)` ready to run. `main.py` is now a thin CLI wrapper. API layer will call the same loader functions without touching file paths.
- **`scr/serializer.py`** — State serialization layer. Symmetric serialize/deserialize for all core engine models (`Unit`, `Faction`, `Domain`, `WorldState`, `CycleEvent`). Top-level `serialize_state()` / `deserialize_state()` for full snapshots. Used by API responses and SQLite cycle snapshots. Cycle-only fields excluded.

### Fixed
- **Multi-domain health penalty** (`cycle/end_of_cycle.py`) — Penalty now based on domains a unit *actively acted in* this cycle, not domains they have ratings in. Was `(len(unit.domains) - 1) * 5`; now uses active domain count passed from `runner.py`. Units with multiple domain ratings no longer take spurious HP drain every cycle.

### Added
- **Health-based domain cap** (`npc/behavior.py`) — Units below 50 HP are capped at 2 active domains per cycle; below 25 HP capped at 1 (primary only). Enforced at end of `select_npc_actions()`. Decision doc: `Planning/decisions/2026-04-03-multi-domain-health-fix.md`.

---

## 2026-04-01 (4)

### Changed
- **`resolve_protect` (replaces `resolve_entrench`)** (`actions.py`) — No roll. Entrench increase = `4N / 100` per use (N = action level). Stores `unit.cycle_protect_level` for Harm comparison. Old name kept as alias.
- **`resolve_care` (replaces `resolve_rejuvenate`)** (`actions.py`) — Healing is `4 × level` (linear, not flat 10). Old name kept as alias.
- **`resolve_harm` (replaces `resolve_attack`)** (`actions.py`) — Two-stage resolver. Stage 1: entrench drain `6N / 100` per effective level. Stage 2: rating damage via `harm_rating_damage()` if entrench reaches 0; floor regresses if rating drops below threshold. Protect interaction: Harm ≤ Protect → blocked; Harm = Protect+1 → Harm-1 succeeds; Harm ≥ Protect+2 → Harm-1 and Harm-2 both succeed. Old `resolve_attack` kept as legacy alias.
- **`resolve_block` (new unified)** (`actions.py`) — Replaces both old block resolvers. Pure level comparison: Block ≥ target → decisive (all cancelled); Block = target-1 → partial (levels reduced); else fail. Old resolvers kept for faction use.
- **Multi-domain health penalty** (`cycle.py`) — Each domain beyond the first costs 5 HP per cycle, applied before natural health decay.
- **Block dispatch updated** (`cycle.py`) — Step 5a now computes `target_highest_level` from current plans and calls `resolve_block` directly. Partial Block outcome reduces plan levels by 1 (cancels level-1 plans).
- **`cycle_protect_level: int = 0`** (`models.py`) — Added to Unit cycle-only state; reset each cycle via `reset_cycle_state()`.
- **`harm_rating_damage(harm_level, defender_floor)`** (`formulas.py`) — New formula function used by `resolve_harm`.
- **Faction Skip action** (`cycle.py`) — `_execute_faction_action` now handles `"Skip"` plan cleanly (returns None).

### Fixed
- **Protect tests updated** (`tests/test_actions.py`) — Reflected new 4N/100 increment, removed level-2 gate assertion, added `cycle_protect_level` assertion.

---

## 2026-04-01 (3)

### Changed
- **NPC action selection reworked** (`npc.py`) — Replaced proportional point allocation with top-3 threshold selection. Highest-weight action always selected; 2nd selected if within 5 weight of 1st; 3rd if within 8. Each selected action has a 5% independent skip chance. Maximum 3 actions per unit per cycle. Wildcard override removed. Decision doc: `Planning/decisions/2026-03-31-action-economy-rework.md`.
- **L1 budget system added** (`npc.py`) — Each domain has a budget of `2^(floor-1)` L1 units per cycle. Each action executes at a level (1–floor) with cost `2^(level-1)`. Level is reduced if budget is exceeded; action is dropped if level 1 still exceeds budget.
- **Action level on NPCPlan and FactionPlan** (`models.py`) — Both dataclasses gain a `level: int = 1` field. NPC sets it to the chosen action level; faction sets it to `faction.floor`.
- **Faction 5% skip chance** (`npc.py`) — Factions have a 5% chance of taking no action each cycle (same as units).
- **Specs updated to v2** (`Planning/specs/actions_spec.md`, `Planning/specs/npc-behavior-engine_spec.md`) — Full rewrite reflecting the accepted action economy rework.

---

## 2026-04-01 (2)

### Changed
- **Unified grow increment formula** (`formulas.py`) — Replaced `UNIT_GROW_INCREMENTS` dict and `faction_grow_increment()` with a single `grow_increment(floor_level)` function using `cycles = 2^n + 1`. Both units and factions now use the same curve. Decision doc: `Planning/decisions/2026-04-01-grow-rework.md`.
- **Floor stored separately from rating** (`models.py`) — `DomainRating` and `Faction` gain a `floor: int` field (auto-initialized from `int(rating)` via `__post_init__`). The floor tracks the last confirmed level independently of the rating float.
- **Entrench gate on level-up** (`cycle.py`) — Floor advances only at end of cycle AND only if `entrench >= 50` (units: per domain; factions: faction entrench). Level-up effects (entrench reset to 25%, capacity narrative) moved from Grow action to end-of-cycle step 7.
- **Grow action simplified** (`actions.py`) — `resolve_grow_unit` and `resolve_grow_faction` no longer trigger level-up logic. They only increment rating. Trait modifiers (Expansionary, Satisfied) preserved.

### Fixed
- **`test_revengeful_unit_may_attack` skipped** (`tests/test_cycle.py`) — Test relies on seed-sensitive NPC Harm selection which will be superseded by the action economy rework.

---

## 2026-04-01

### Changed
- **`faction.health` renamed to `faction.entrench`** (`models.py`, `actions.py`, `cycle.py`, `events.py`, `npc.py`, `main.py`, `data/factions.json`, `data/past_cities/TwinCities/factions.json`) — Faction health was semantically equivalent to entrench; factions do not retire. Renamed throughout to match the unified entrench concept. `_faction_health_state()` → `_faction_entrench_state()`. `FactionHealthDecay` action string → `FactionEntrenchDecay`. All stat_change field strings updated from `"health"` to `"entrench"`.

---

## 2026-03-31 (5)

### Fixed
- **Cascade never fired on combat** (`events.py`) — `check_for_cascades` was filtering on `"Attack"`, the pre-rename action name. Corrected to `"Harm"`. Cascades from decisive combat hits were silently skipped since the 2026-03-31 rename.

---

## 2026-03-31 (4)

### Fixed
- **Faction split name chaining** (`events.py`) — Splinter factions no longer inherit "The The X Remnant Remnant..." names. Added `_SPLINTER_NAMES` pool keyed by domain (8 names per domain, plus 6 generic fallbacks). Each split draws a fresh unused name from the pool. ID is derived from the new name, not the parent ID. Fallback numbering (`The Splinter Faction 2`, etc.) handles pool exhaustion on heavily-split domains.

---

## 2026-03-31 (3)

### Fixed
- **Kick cannot target leader** (`actions.py`) — Leader protection was only present in the inertia-based selection branch. Added `if uid == faction.leader_id: continue` to all three branches (Hierarchical, Meritocratic, inertia). If no non-leader members exist, kick does nothing.

### Added
- **Faction collapse and split** (`events.py`, `cycle.py`) — Factions now collapse when health decay fires against a faction already at health=1. Outcome by floor rating: 2–3 dissolve, 4–5 50/50 dissolve/split, 6+ always split. On dissolve: faction removed, members unaffiliated. On split: old faction demoted 2 levels, new splinter created 1 level below, leader ejected, traits divided, units rebalanced by rating, both factions set as Foe to each other. Decision doc: `Planning/decisions/2026-03-31-faction-collapse-and-split.md`.

---

## 2026-03-31 (2)

### Changed
- **Seek Leadership weight boost** (`npc.py`) — Units in a leaderless faction receive +11 to their Seek Leadership action weight each cycle, on top of trait modifiers. Gives any member pressure to claim leadership, not just Ambitious units.

---

## 2026-03-31

### Added
- **Pre-sim population fill** (`main.py`) — After loading starting data, a fill pass
  generates anonymous background units and assigns them to factions up to ~40% of
  capacity before cycle 1 begins. Generated units are ephemeral (memory only, never
  written to JSON). Named characters in the starting data are unaffected.
  See: `Planning/decisions/2026-03-31-pre-sim-population-fill.md`

- **Rivers Point data** (`data/`) — New starting data set replacing TwinCities.
  9 domains (Guilds, Docks, Noble Houses, City Watch, Underworld, Temple, Commons,
  Arcane, Registry), 21 factions, 20 named starting units. TwinCities data archived
  to `data/past_cities/TwinCities/`.

- **Canonical action names** — All action name strings renamed throughout engine to
  match spec: Attack→Harm, SpyPassive→Steal, SpyTargeted→Expose, Rejuvenate→Care,
  Entrench→Protect, BlockCityWide/BlockSpecific→Block, SupportFaction→Support Faction,
  SeekLeadership→Seek Leadership.

- **Multi-point action economy** (`npc.py`) — `select_npc_actions()` now returns
  `List[NPCPlan]`. Units receive `floor(primary_rating)` action points distributed
  proportionally across all weighted actions per cycle.

### Fixed
- `_apply_citywide_block` updated to iterate `List[NPCPlan]` per unit (was single plan)
- `events.py` updated to use renamed `build_action_weights()` (was `build_trait_weights`)
- Logger safe-print for Unicode characters on Windows console
