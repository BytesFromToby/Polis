# Deviations — Public Needs (The Barley Run)
Blueprint: Planning/blueprints/public-needs_BP.md
Date: 2026-06-12

| Slice | Step | Deviation | Why |
|-------|------|-----------|-----|
| 1 | 3 | `deserialize_state` returns an 8-tuple (public appended); 4 unpack sites updated | Symmetry with serialize; mechanical change |
| 1 | 3 | Serialization tests live in `test_needs_bands.py`, not a separate file | Cohesion with the band tests |
| 2 | 2 | Used `Faction.level` (alias of `floor_rating`) | Readability; same property |
| 3 | 1 | Support deltas via `mayor.adjust_reputation("the_public", …)` when mayor present | `mayor.reputation` is the documented source of truth; `public.support` syncs from it |
| 4 | 2 | `select_faction_action` takes `public=None, chain_roles=None` (precomputed set) instead of loading chains | Engine stays IO-free; loaders own files |
| 4 | 2 | Weight tests capture the dict by monkeypatching `weighted_choice` | No refactor of the selector needed |
| 4 | 3 | Only LLM-side whitelist exists (`VALID_FACTION_ACTIONS`); engine committed path is generic | Updated in slice 6 where the blueprint addresses it |
| 5 | 1 | `chains` defaults to `[]` in `run_cycle`; callers pass loader output | Engine IO-free |
| 5 | 2 | Toiling reset at end of `run_cycle`, not `end_of_cycle.py` | `end_of_cycle` runs *before* the needs step; the blueprint step corrected itself |
| 5 | 3 | `start_sim` builds the public from `load_the_public()` defaults, not the city template | City rows carry no `the_public` block yet — city-generation's concern |
| 5 | — | Inspector fix: Toil-boost assertion was vacuous at `fed=0` (drift cap); restarted at `fed=50`, strict `>` | Inspector finding, slice-5 report |
| 6 | 1 | Same-cycle gate test patches `random.random` **and** `random.choices` | Deck selection needed determinism too |
| 6 | 1 | Known limit surfaced: event rolls iterate `world.chaos` — a zero-chaos starving city never rolls | Pre-existing event-system shape; gates correct, firing chaos-coupled. Follow-up |
| 6 | 2 | Deck effects conformed to faction-health only (riot → ovenmen −10; plague → asklepiads −3) | `_apply_single_event_effect` cannot touch The Public/support; chaos branch unreachable for real domain ids. Follow-up |
| 6 | 3 | Two signatures widened (`begin_audience_step`/`run_audience`, `PromptBuilder.build`) | Within the step's ≤2 bound |
| F | 1 | `ThePublic.drunk` stored as display cache set by `apply_needs`; serializer emits derived band keys | Step proposed it; "not stored" honored in spirit (no axis, no dynamics) |
| F | 2 | "The People" is a 4th Mayor-window section (grid 3→4), not a standalone panel | Reads naturally beside Treasury/Standing/World |
| F | 3 | Spec corrected ×2 (recorded in spec text): *Toil matters* forces **estate** Toil (processor Toil self-cancels raw-bound); control = committed Protect (estates Toil **voluntarily** when hungry — prosocial weight by design) | Discovered by the math/dynamics run; intent unchanged |
| F | 3 | Legibility + recoverability assertions share one trajectory run | Same scenario; two phases of one curve |
| F | 3 | No constant tuning needed — dynamics passed on shipped constants | — |
