# Blueprint: Projects Rework (v5 — base projects + cap fusion)
Spec: Planning/specs/projects_spec.md
Decision log: Planning/decisions/2026-06-05-projects-rework.md
Date: 2026-06-05

---

## Builder instructions
- Execute steps in order. Do not skip, reorder, or read ahead into the next slice.
- Check off each step when complete: [ ] → [x]
- One step = one logical concern. If a step can't be tested on its own, it's too small — merge it. If it touches more than one concern, split it.
- Deviation: if you do something differently than the step says, note it inline and keep going.
- Stuck: stop immediately. Do not try alternative approaches. Report exactly where and why.
- Test command: `cd backend && py -m pytest tests/ -q`. Headless: `py main.py --cycles 10`.

### Orientation (read before Slice 1)
- **Out of scope:** `tax_collection` projects. Do **not** remove `build_cost` / `build_time` / `faction_build_actions` from the `Project` dataclass — tax_collection still uses them. Base projects just don't.
- **Base project** = `category == "base"`; one repeatable type per domain; each completed one is its own instance with its own `health`.
- **Cap is derived**, not authored: `cap = base_cap + Σ contribution(active base projects)`. `base_cap` is frozen at cycle 0 from starting `Σ level`.
- Faction `level = int(rating)`; domain `utilization = Σ level` (already implemented in `runner.py`).
- Base-project names: harbor=Docks, trade=Agora, guilds=Workshop, military=Barracks, temples=Temenos, academy=Lyceum, aristocracy=Estate, professions=Gymnasion.

---

## Slice 1: Cap derivation
**Scope:** A domain's `cap` is computed from starting fill + active base-project health tiers, re-derived each cycle; no base projects yet means `cap == base_cap`.

### Step 1: Add `CAP_HEADROOM_MULT` + base-project contribution helper to formulas
**Build:** In `engine/formulas.py`: add `CAP_HEADROOM_MULT = 1.20`. Add `base_cap_from_fill(fill: float) -> int` returning `round(fill * CAP_HEADROOM_MULT)`. Add `project_cap_contribution(project) -> int` returning, for a `category=="base"` project: 2 if `status in ("active","damaged")` and `health >= 51`; 1 if active/damaged and `health` 21–50; else 0 (critical, under_construction, destroyed, or non-base → 0).
**Test:** covered by Step 5.
**Done When:** the two helpers exist and import; `project_cap_contribution` returns 2/1/0 by tier.
**Stuck If:** health-tier thresholds conflict with `Project.health_tier()` (reuse it if cleaner).
- [x] Complete

### Step 2: Add `base_cap` to Domain; set it at load
**Build:** In `engine/models.py` add `Domain.base_cap: int = 0`. In `loaders.py` where domains+factions are loaded, after both exist compute each domain's `base_cap = base_cap_from_fill(Σ level of its factions)` and set `domain.base_cap`; also set `domain.cap = base_cap` initially. Authored `cap` in `data/domains.json` is ignored for the budget (may stay in file, unused).
**Test:** covered by Step 5.
**Done When:** a freshly loaded game has `domain.base_cap == round(Σ level × 1.20)` for each domain.
**Stuck If:** loader computes domains before factions and can't see fill — reorder so factions load first.
- [x] Complete

### Step 3: Derive cap each cycle in the runner
**Build:** In `engine/cycle/runner.py`, in the per-cycle recalculation block (where `domain.utilization` is summed, ~L71–74), also set `domain.cap = domain.base_cap + Σ project_cap_contribution(p)` over projects whose single domain is this domain. Do this every cycle, alongside utilization.
**Test:** covered by Step 5.
**Done When:** after `run_cycle`, each domain's `cap` reflects base_cap + active base-project contributions.
**Stuck If:** projects aren't in scope at that point in the runner — pass them in or move the cap step to where projects are available.
- [x] Complete

### Step 4: Add `category="base"` + `build_progress` to the Project model
**Build:** In `engine/models.py` `Project`: add cycle-persistent `build_progress: int = 0` (0–4 work units during construction). Keep `category` default `"standard"` but document `"base"` as a valid value. Do not touch legacy fields. Update `serializer.py` to round-trip `build_progress` and `base_cap` (Domain).
**Test:** `py -c "from engine.models import Project, Domain; Project(id='p',name='Docks',domains=['harbor'],build_cost=0,build_time=4,category='base'); Domain(id='harbor',name='Harbor',cap=0,base_cap=0)"` constructs clean; serializer round-trip test (Step 5).
**Done When:** Project carries `build_progress`; Domain carries `base_cap`; both serialize/deserialize.
**Stuck If:** serializer has a fixed field list that rejects new keys — add them explicitly.
- [x] Complete

### Step 5: Commit cap-derivation tests
**Build:** New `tests/test_projects_cap.py`. Assert: (a) `base_cap_from_fill` and a loaded game give `base_cap == round(Σlevel×1.20)`, and authored `domains.json` cap does not affect it; (b) a domain with no base projects has `cap == base_cap` after `run_cycle`; (c) one intact base project → +2, damaged → +1, critical/under_construction/destroyed → +0; (d) re-derivation: flipping an active base project intact→damaged drops that domain's cap by 1 next `run_cycle`; (e) changing `CAP_HEADROOM_MULT` changes base_cap. Also a serializer round-trip test for `build_progress`/`base_cap`.
**Test:** `py -m pytest tests/test_projects_cap.py -q`
**Done When:** all five cap criteria + round-trip pass.
**Stuck If:** the loader can't be invoked in a unit test — construct domains/factions directly and call the cap-derivation helper instead.
- [x] Complete

---
⛔ End of Slice 1. Run **inspector** on this slice before continuing.

---

## Slice 2: Build model (4 work units)
**Scope:** Base projects build via 4 work units — faction `BuildProject` (own-domain, DC 12, +1) or Mayor buy (50 gold + 1 AP, +1) — completing to `active` at 4.

### Step 1: Rewrite `resolve_build_project` to work units + domain gate
**Build:** In `engine/actions/faction.py` `resolve_build_project`: for a `category=="base"` project, (1) if `faction.domain_primary not in project.domains` → return `blocked` (no change); (2) roll `d20 + faction.level` vs DC 12; success → `project.build_progress += 1`; fail → no change; (3) if `build_progress >= 4` → `status="active"`, `health=100`, mark dramatic (completion). Do **not** deduct `build_cost`. Leave non-base projects on the existing path.
**Test:** Step 4.
**Done When:** own-domain success adds 1 unit; fail adds 0; cross-domain → blocked; 4th unit flips to active health 100.
**Stuck If:** the roll helper differs from `d20 + level` — match the spec/formulas roll.
- [x] Complete

### Step 2: Add `mayor_buy_build_unit` (50 gold + 1 AP, guaranteed)
**Build:** In `engine/projects/processing.py` add `mayor_buy_build_unit(project, treasury, mayor) -> ActionResult`: require `mayor.spend(1)` (1 AP) and `treasury.gold >= 50`; on failure of either, refund any spent AP and return `outcome="fail"` with nothing deducted; on success deduct 50 gold (`treasury.expenditure_this_cycle += 50`), `build_progress += 1`, completion check (→ active, health 100 at 4). Guaranteed unit (no roll).
**Test:** Step 4.
**Done When:** with ≥50 gold and ≥1 AP, one call adds 1 unit and deducts 50g+1AP; insufficient → 0 units, 0 deducted.
**Stuck If:** Mayor AP refund semantics unclear — mirror `repair_project`'s refund pattern.
- [x] Complete

### Step 3: Commit build-model tests
**Build:** Extend `tests/test_projects.py` (new class `TestBuildModel`): faction own-domain build success (force roll ≥12) → +1; forced fail → +0; cross-domain → `blocked` +0; `mayor_buy_build_unit` with 50g+1AP → +1 unit, gold −50, AP −1; with 40g → +0, no deduction; with 0 AP → +0, no deduction; 3 AP + 150g → 3 units in one turn (loop); reaching 4 units → `active`, `health==100` in the same call; assert no `build_cost` deducted anywhere in base build.
**Test:** `py -m pytest tests/test_projects.py -q`
**Done When:** all seven build criteria pass.
**Stuck If:** the build roll can't be forced deterministically — seed `random` or monkeypatch `random.randint`.
- [x] Complete

---
⛔ End of Slice 2. Run **inspector** on this slice before continuing.

---

## Slice 3: Initiation
**Scope:** Base projects come into being on breaking ground — Mayor anywhere, NPC factions under near-cap pressure — at most one under construction per domain.

### Step 1: Base-project catalog + `initiate_base_project` helper
**Build:** Define the domain→name map (harbor=Docks … professions=Gymnasion) — in `data/projects.json` (replace its contents with the 8 base templates: `id`, `name`, `domains:[domain]`, `category:"base"`) and/or a `BASE_PROJECT_NAMES` constant the helper reads. Add `initiate_base_project(domain_id, projects, initiated_by) -> Optional[Project]` in `engine/projects/processing.py`: if a `category=="base"` project with `status=="under_construction"` already exists in that domain → return `None` (refuse); else create a new instance (unique id, domain's base name, `category="base"`, `status="under_construction"`, `build_progress=0`), register it in `projects`, return it.
**Test:** Step 4.
**Done When:** initiating with none-in-progress creates one under_construction instance with `build_progress==0` and the domain's name; a second initiation in the same domain returns None.
**Stuck If:** project id collisions — generate a unique id (e.g. `f"{domain}_base_{n}"`).
- [x] Complete
**Deviation:** catalog of names kept as a code constant `BASE_PROJECT_NAMES` (engine source of truth for initiation); `data/projects.json` is replaced with the 8 templates in the Final slice. The blueprint allowed "and/or a constant".

### Step 2: Faction near-cap initiation in behavior + resolution
**Build:** In `engine/npc/behavior.py`: when a faction would pick `BuildProject` and has no buildable base project in its own domain, allow initiation only if `domain.utilization >= 0.85 * domain.cap` AND no base project is `under_construction` in that domain; signal it by setting `plan.target_id` to a sentinel `f"new_base:{domain}"`. In `engine/cycle/resolution.py` `_execute`: when action is `BuildProject` and `target_id` starts with `new_base:`, call `initiate_base_project(domain, projects, faction.id)`, then `resolve_build_project` on the created instance (apply the build roll). Never initiate when one is already under construction.
**Test:** Step 4.
**Done When:** a faction in a ≥85%-cap domain with none under construction can select BuildProject-to-initiate; it does not when one is already under construction.
**Stuck If:** behavior can't see `domain.cap`/`utilization` at selection time — they're on the Domain object passed in; read them there.
- [x] Complete
**Deviation:** also refined `_get_buildable_projects` to exclude *active* base projects (a completed base project isn't buildable) so factions don't target a done Docks and waste the turn.

### Step 3: Mayor initiation path
**Build:** Ensure the Mayor can initiate in any domain: `mayor_buy_build_unit` (or a thin wrapper) accepts a domain with no under_construction base project by calling `initiate_base_project(domain, projects, "mayor")` first, then adding its guaranteed unit. Mayor initiation has no faction requirement and is not gated by cap.
**Test:** Step 4.
**Done When:** the Mayor can initiate + build a base project in a domain that has no factions of its own.
**Stuck If:** the mayor action dispatch (API/route) doesn't expose a target domain — wire the new path where mayor project actions are executed; note the location inline.
- [x] Complete
**Deviation:** provided the engine entry `mayor_build_base(domain, projects, treasury, mayor)` (find-or-initiate then buy a unit). Hooking it to a player-facing MayorAction in the API/route dispatch is deferred — the headless demo drives initiation via the near-cap faction path, and the player-facing Mayor build button is API-layer work outside this slice's tests.

### Step 4: Commit initiation tests
**Build:** New `tests/test_project_initiation.py`: initiation creates one under_construction instance (progress 0, correct name); second initiation in same domain → None; behavior — faction at `utilization == 0.85*cap` with none under construction can return a `BuildProject` plan that initiates (sentinel target), and returns a non-initiating plan when one is already under construction; Mayor initiation in a faction-less domain creates + builds an instance.
**Test:** `py -m pytest tests/test_project_initiation.py -q`
**Done When:** all four initiation criteria pass.
**Stuck If:** behavior selection is non-deterministic — seed `random`; assert over the eligibility condition rather than a single draw where needed.
- [x] Complete

---
⛔ End of Slice 3. Run **inspector** on this slice before continuing.

---

## Slice 4: Sabotage, destruction & maintenance (verify + wire to cap)
**Scope:** Base projects are sabotageable by any faction; a destroyed one stops feeding cap; maintenance is unchanged.

### Step 1: Confirm Sabotage works on base projects + destroyed→cap
**Build:** Verify `resolve_sabotage_project` (in `engine/actions/faction.py`) applies to `category=="base"` projects with no domain gate: decisive −25, partial −10, fail 0, `health 0 → status="destroyed"`. No code change expected unless a base-specific guard blocks it; if `build_progress`/under_construction interferes, ensure an active base project is a valid sabotage target. A destroyed base project must already contribute 0 to cap via Slice 1's `project_cap_contribution`.
**Test:** Step 3.
**Done When:** decisive/partial/fail damage tiers hold on a base project; destroyed base project contributes 0 cap; sabotage is not domain-gated.
**Stuck If:** sabotage path special-cases non-base projects — generalize to include base.
- [x] Complete
**Deviation:** verification only — `resolve_sabotage_project` is already category-agnostic; no code change. Cap drop on destruction is handled by Slice 1's `project_cap_contribution` (destroyed → 0).

### Step 2: Confirm maintenance covers base projects
**Build:** Verify the Treasury maintenance step charges `2 × active_project_count` including active base projects, and is silently skipped when unaffordable (no per-project damage). No change expected; adjust only if base projects are excluded from the active count.
**Test:** Step 3.
**Done When:** maintenance = `2 × active count` with base projects counted; skipped cleanly when broke.
**Stuck If:** the active-count query filters by category — include `base`.
- [x] Complete
**Deviation:** verification only — the runner counts active projects without category filtering, so base projects are already included; no code change.

### Step 3: Commit sabotage + maintenance tests
**Build:** In `tests/test_projects.py`: base-project sabotage decisive −25 / partial −10 / fail 0 (force outcomes); destroyed base project (`health 0`) → `status=="destroyed"` and `project_cap_contribution == 0`; a faction outside the project's domain can sabotage it (not blocked); maintenance = `2 × active count` with a base project active; maintenance skipped (no damage) when `treasury.gold` can't cover it.
**Test:** `py -m pytest tests/test_projects.py -q`
**Done When:** all sabotage + maintenance criteria pass.
**Stuck If:** forcing sabotage outcomes is hard — monkeypatch the contest/roll as in the faction action tests.
- [x] Complete

---
⛔ End of Slice 4. Run **inspector** on this slice before continuing.

---

## Final Slice: Data replacement, cleanup & full verification
**Scope:** Old project data gone, reference docs aligned, whole suite green, headless run shows projects built and caps growing.

### Step 1: Replace `data/projects.json` + reconcile loaders
**Build:** Replace `data/projects.json` with only the 8 base-project templates (no bespoke/`faction_level` entries). Ensure `loaders.py` loads zero base-project **instances** at game start (cities begin with none) while the catalog/templates are available for initiation. Any `tax_collection` data, if present, is left intact.
**Test:** `py main.py --cycles 1` loads and runs with no project KeyError/AttributeError.
**Done When:** a game loads with zero starting base projects and the 8-template catalog available.
**Stuck If:** loader expects bespoke fields from the old 45 entries — drop those reads.
- [x] Complete
**Deviation:** `data/projects.json` emptied to `[]` (zero starting instances) rather than holding the 8 templates — the catalog is the `BASE_PROJECT_NAMES` code constant, and loading templates as instances would start the game with 8 under-construction projects, violating zero-start. No loader change needed.

### Step 2: Align reference docs
**Build:** Update `Planning/reference/data-models.md` (Project: add `category="base"`, `build_progress`, note legacy fields retained for tax; Domain: add `base_cap`) and `Planning/reference/formulas.md` (add `CAP_HEADROOM_MULT`, `base_cap_from_fill`, `project_cap_contribution`, and the derived-cap formula). Update root `CLAUDE.md` / `architecture.md` only if a subsystem seam moved.
**Test:** grep shows the new names present; no stale `build_cost`-as-base-mechanic claims remain.
**Done When:** reference docs match the built model.
**Stuck If:** a reference claim contradicts the code — code + spec win; fix the doc.
- [x] Complete

### Step 3: Headless smoke
**Build:** No new code. Run `py main.py --cycles 10`.
**Test:** observe output + `logs/narrative.log`.
**Done When:** run completes with no errors; base projects get initiated/built in near-cap domains and at least one domain's `cap` rises above its `base_cap`; no faction removed.
**Stuck If:** no project is ever initiated over 10 cycles — check the near-cap threshold wiring (Slice 3 Step 2).
- [x] Complete
**Deviation:** smoke surfaced two bugs, both fixed: (1) `run_cycle` used `projects or {}`, creating a throwaway empty dict so runtime-initiated projects were discarded — normalized to use the caller's dict; (2) under-construction base projects (health 0) were instantly destroyed by Sabotage — added a guard so a base project under construction isn't a sabotage target (in `resolve_sabotage_project` and behavior targeting). Result over 15 cycles: 16 base projects initiated, 12 active, all 8 domains' cap grew above base_cap.

### Final Step: Verify spec Done when items
**Build:** No new code. Confirm all `**Done when:**` items in `projects_spec.md` are met by committed tests.
**Test:** `cd backend && py -m pytest tests/ -q` (full suite) + the headless smoke. Capture output.
**Done When:** every `[automated]` criterion passes via its committed test; suite green.
**Stuck If:** an automated criterion fails and the cause isn't clear from output.
- [x] Complete
**Result:** full suite **318 passed**; `py main.py --cycles 10` clean. All 21 `[automated]` items backed by committed tests in test_projects_cap.py, test_projects.py (TestBuildModel/TestSabotageBase/TestMaintenanceBase), test_project_initiation.py. No `[human-required]` items.

---
⛔ Final slice complete. Run **inspector** for final sign-off.

✅ Inspector: PASS — 2026-06-05 16:45 — all 21 [automated] Done-when items verified via committed tests; cap derivation independently re-checked on real data; projects↔cap loop confirmed end-to-end (15-cycle run). Suite 318-green, headless clean. See output/inspect/Inspect_projects-rework_Final_2026-06-05.md. One spec-prose mismatch noted (under-construction sabotage in the Damage Input line) for an architect reconciliation — not a defect, blocks nothing.
