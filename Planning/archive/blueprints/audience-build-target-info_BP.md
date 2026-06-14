# Blueprint: Audience Build-Target Info
Spec: Planning/specs/audience-build-target-info_spec.md
Date: 2026-06-08

---

## Builder instructions
- Execute steps in order. Do not skip, reorder, or read ahead into the next slice.
- Check off each step when complete: [ ] → [x]
- One step = one logical concern. If a step can't be tested on its own, it's too small — merge it. If it touches more than one concern, split it.
- Deviation: if you do something differently than the step says, note it inline and keep going.
- Stuck: stop immediately. Do not try alternative approaches. Report exactly where and why.
- Backend test: `cd backend && py -m pytest tests/ -q`

---

## Slice 1: Per-project description (single source)
**Scope:** A `base_project_description(domain_id)` helper returns a one-line effect string for every base project, exported alongside `base_project_name`.

### Step 1: Add BASE_PROJECT_DESCRIPTIONS + base_project_description
**Build:** In `engine/projects/processing.py`, next to `BASE_PROJECT_NAMES` (~272) and `base_project_name` (~284), add `BASE_PROJECT_DESCRIPTIONS: Dict[str, str]` and `def base_project_description(domain_id: str) -> str`. All v6 base projects do the same thing (building raises the domain's cap), so the description can be one generic sentence per domain — either authored per domain in the dict or generated. Use a one-line, human-readable sentence, e.g. for the default: `f"Raises the {domain_id.replace('_',' ')} domain's capacity, giving its factions room to grow."`. The helper returns the dict entry if present, else the generic default. Export `base_project_description` from `engine/projects/__init__.py` alongside `base_project_name`.
**Test:** `cd backend && py -c "from engine.projects import base_project_description; print(base_project_description('harbor')); print(base_project_description('nope'))"`
**Done When:** Both print a non-empty one-line string (no newline); unknown domain returns the generic default.
**Stuck If:** N/A.
- [x] Complete

### Step 2: Description helper test
**Build:** Create `backend/tests/test_base_project_description.py`: for every domain in `BASE_PROJECT_NAMES`, `base_project_description(domain)` returns a non-empty string with no `\n`; and an unknown domain id returns a non-empty default.
**Test:** `cd backend && py -m pytest tests/test_base_project_description.py -q`
**Done When:** Passes.
**Stuck If:** N/A.
- [x] Complete

---
⛔ End of Slice 1. Run **inspector** on this slice before continuing.

---

## Final Slice: Prompt names the faction's own buildable + spec coherence
**Scope:** The audience prompt states the faction's own project name + description and targets BuildProject by domain id; specs updated; verified.

### Step 1: Parameterize the BuildProject term + fix the deal-schema target
**Build:** In `engine/llm/prompt_builder.py`:
- `VALID_FACTION_TERMS_TEMPLATE` (~78-82): change the BuildProject bullet from the static "work to build a specific city project; name the project" to name THIS faction's own project + effect, via placeholders, e.g.:
  `- BuildProject — work to build {project_name} ({project_desc}); target it by your domain id below`
- In `PromptBuilder.build` (~where `valid_faction` is assigned, before the `SYSTEM_TEMPLATE.format` at ~267): format the template with the faction's own project — `VALID_FACTION_TERMS_TEMPLATE.format(project_name=base_project_name(faction.domain_primary), project_desc=base_project_description(faction.domain_primary))`. Import both helpers from `engine.projects`.
- The `<deal>` schema BuildProject line in `SYSTEM_TEMPLATE` (~127): change `"target_id": "<a project id>"` to `"target_id": "{domain}"` (the `SYSTEM_TEMPLATE.format` call already substitutes `domain=faction.domain_primary`, the domain id — so this renders the faction's domain id, no new substitution needed).
- Do NOT edit `_committed_plan`, the resolver, or any engine targeting.
**Test:** `cd backend && py -m pytest tests/ -q`
**Done When:** Suite runs; any failures are only prompt-assertion tests to update in Step 2.
**Stuck If:** A non-prompt test fails (engine/parser) — the change leaked beyond the prompt; stop.
- [x] Complete

### Step 2: Prompt tests
**Build:** In `backend/tests/test_audience_terms.py`, add tests building the prompt via the existing `_build_prompt()` helper (its faction is `domain_primary="trade"` → base project "Agora"):
1. The built prompt contains the faction's own project name (`"Agora"`) and its description text (`base_project_description("trade")`).
2. The prompt's BuildProject `<deal>` target shows the faction's domain id (`"trade"`) and contains neither the literal `"<a project id>"` placeholder nor `dock_expansion`.
3. The prompt does NOT contain another domain's base-project name (e.g. `"Docks"` / `"Barracks"`) — only the faction's own buildable appears.
**Test:** `cd backend && py -m pytest tests/test_audience_terms.py -q`
**Done When:** All pass; full suite green (update any pre-existing assertion that expected the old "name the project" wording).
**Stuck If:** The own-project name can't be asserted because the template wasn't parameterized — recheck Step 1.
- [x] Complete

### Step 3: Spec coherence edits
**Build:** `audience_spec.md` Valid Deal Terms: the BuildProject faction term builds the faction's own-domain base project, targeted by the **domain id**; fix the `<deal>` example that uses `"target_id": "dock_expansion"` to a domain-id form (e.g. `"target_id": "harbor"`), and any Done-when naming a free-text project id. Add a light note in `llm-system_spec.md` if it describes the prompt's project/term section.
**Test:** Manual reread / grep: `grep -rn "dock_expansion" Planning/specs/audience_spec.md` returns nothing; the BuildProject term reads as own-domain + domain-id target.
**Done When:** `audience_spec.md` no longer contains `dock_expansion` and describes the domain-id target.
**Stuck If:** N/A.
- [x] Complete

### Final Step: Verify spec Done when items
**Build:** No new code. Confirm all `**Done when:**` items in audience-build-target-info_spec.md are met.
**Test:** `cd backend && py -m pytest tests/ -q` (the committed tests cover the 4 `[automated]` items). Capture output. For the `[human-required]` audience_spec coherence item, show the grep evidence.
**Done When:** Every `[automated]` criterion passes via its committed test; the spec coherence item has evidence.
**Stuck If:** An automated criterion fails and the cause is not clear from the output.
- [x] Complete

---
⛔ Final slice complete. Run **inspector** for final sign-off.

INSPECTED 2026-06-08 — 4 PASS · 1 needs-human (see output/inspect/Inspect_audience-build-target-info_Final_2026-06-08.md)
