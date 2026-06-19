# Walkthrough Recommendations — Polis — 2026-06-17

Everything below was **deferred** (Full-Path or a decision needed) — nothing here was applied.
Quick-Path fixes that WERE applied this run are in `WalkthroughLog_2026-06-17.md`. Baseline: 550
green → **553 green** after the Quick-Path test hardening.

---

## Priority: MEDIUM

### Reconcile special-factions "The Public's Role in Faction Politics" — unimplemented + superseded
- **Area:** `Planning/specs/special-factions_spec.md` (L113–124); `engine/npc/behavior.py`
- **What:** The spec section describing disposition-driven faction effects (`content` → distrusts-Mayor factions −5 Steal + Mayor decree −1 AP; `restless` → Broker-DC +2; `angry` → aggressive +10 Harm) has **no implementation** in `behavior.py`. The intent (public mood → faction aggression) is now covered, more cleanly, by the **Confidence posture modifier** (public-needs_spec, 2026-06-17, 5 bands over `support`).
- **Why:** A spec section that describes behavior the code never had is drift; leaving it invites someone to "fix" code to match a superseded design.
- **Effort:** small · **Path:** Full (architect) · **Spec affected:** special-factions_spec
- **Suggested resolution:** mark the section superseded by the Confidence posture modifier; if the *decree-AP* / *Broker-DC* sub-effects are still wanted, re-spec them explicitly as confidence-band consequences (they are NOT in the confidence work today).

### Harden cycle-runner orchestration coverage (the rest of the test_cycle.py gaps)
- **Area:** `backend/tests/test_cycle.py`; `engine/cycle/runner.py`
- **What:** This run hardened 2 of the flagged tautologies (utilization = exact Σ level; faction_actions excludes Skip — applied). Still unbacked: (a) **initiative is re-rolled every cycle / no persistent advantage** (stated twice in cycle-runner_spec) — no test references the order; needs an observability hook to assert, which is itself Full-Path; (b) **treasury step runs before the action loop and its results appear in CycleResult** — only the treasury-absent path is covered; (c) **`build_actions_this_cycle` reset end-to-end through `run_cycle`** — currently proven only by calling `tick_projects` directly.
- **Why:** These are core-loop invariants with no real backing test; (b) and (c) need a fuller fixture (Mayor + Treasury + projects/base_stacks), which is why they weren't added unattended.
- **Effort:** medium · **Path:** Quick for (b)/(c) tests; Full for (a)'s observability hook · **Spec affected:** cycle-runner_spec (detail in `output/walkthrough/InspectorAudit_2026-06-17.md`)

### Retune piety so the standard city doesn't rest at Zealous
- **Area:** `engine/needs/scales.py` (`PIETY_PER_LEVEL=4`, `PIETY_PARITY=1.0`)
- **What:** The standard roster's temple levels drive `piety` to **100 (Zealous)** at rest, so the zealot tax (−1 support/cycle) is effectively always on. Flagged during the consumption slice; never retuned. Same failure class as the consumption Sodden-pin (a resting band stuck at an extreme).
- **Why:** A "both-ends-bite" scale that lives permanently at one extreme isn't a balance axis — the player never sees the Observant/Devout middle at baseline.
- **Effort:** small (measure std temple `piety_supply/demand`, set PARITY so rest ≈ Observant) · **Path:** Quick (constant retune + a resting-band regression test, mirroring consumption's) · **Spec affected:** public-needs_spec (provisional constants)

### Add a resting-band health tool
- **Area:** new `tools/resting_bands.py`
- **What:** A script that runs the standard city N cycles across a few seeds and prints the resting band of **all seven scales** (fed/happy/health/piety/unrest/consumption/confidence) + the production-wire efficiency. Flag any scale that pins to an extreme.
- **Why:** The consumption Sodden-pin (inspector FAIL) and the piety-Zealous debt are the **same defect class** and NO existing tool/test guards it holistically. This is the cheapest insurance against the next mis-tune.
- **Effort:** small · **Path:** Full (new tool file) · **Spec affected:** none

---

## Priority: LOW

### Document `Treasury.guard_paid_this_cycle` in treasury_spec
- **Area:** `Planning/specs/treasury_spec.md`; `engine/models.py`, `engine/mayor/treasury.py`
- **What:** The cycle flag (set at step 0, true iff full guard payroll cleared; read by the unrest City-Guard lever) is undocumented in treasury_spec.
- **Why:** Small as-built gap; the unrest lever's "payroll met" precondition has no home in the treasury spec.
- **Effort:** small · **Path:** Full (architect, one line) · **Spec affected:** treasury_spec

### `tools/audit.py` dirties the working tree with generated artifacts
- **Area:** `tools/audit.py` outputs (`AUDIT.md`, `audit.xlsx`, `*.csv`)
- **What:** Running the audit rewrites generated files into the tree every time. Consider `.gitignore`-ing them (or a `--check` mode that compares without writing) so the health script doesn't produce spurious diffs.
- **Why:** Keeps `git status` honest; generated artifacts in the tree muddy reviews.
- **Effort:** small · **Path:** Full (decision: ignore vs commit-as-snapshot) · **Spec affected:** none

### Plan-quality (foreman) — two recurring, low-grade patterns in the deviation history
- **Area:** `Planning/blueprints/` (foreman output)
- **What:** (1) Foreman occasionally **bakes a specific numeric example/expectation that turns out wrong** — projects "expect 6 0" (spec-correct 6 2), piety "two sources → Starving" (spec-correct: all sources), consumption `CONSUMPTION_PARITY=0.10` (measured wrong). The builder re-derives from the spec each time, so no harm lands — but foreman should **cite the spec / a measurement step for tuned numbers** rather than asserting a literal the builder must trust. (2) Foreman names the behavior entry point **`decide_action`** in ~4 blueprints; the real symbol is **`select_faction_action`** — a trivial recurring naming miss.
- **Why:** Healthy overall (most builds 1–6 meaningful deviations, only 3/26 mention any "stuck" — no chronic under-specification). These two are the only *patterns*. The numeric one is worth a habit change because a wrong tuning literal is what produced the consumption FAIL.
- **Effort:** small (foreman skill guidance) · **Path:** Full (skill change — out of project scope; noted for the framework) · **Spec affected:** none

---

## Not in scope here (feature roadmap, not maintenance)
The big unbuilt items — the rest of `resource-chains` (building-supplies, imports, estate
differentiation), `crisis-and-stance`, `elections-and-titles` (incl. the hard removal endgame),
`city-generation`, the projects rework, the UI redo, and wiring the remaining factions' jobs — are
**roadmap features**, tracked in `Planning/proposals/`. They belong to architect/foreman, not this
maintenance pass.
