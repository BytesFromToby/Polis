# Decisions: Projects v6 — Base-Project Stack Model
Spec: Planning/specs/projects_spec.md
Date: 2026-06-07

- **One `BaseProjectStack` record per domain, not N per-instance `Project`s** — the player's
  rules (only the newest/top instance is ever built, repaired, or attacked; you can't break
  ground while the top is in-flux) guarantee every instance below the top is always pristine.
  So the instances below need no individual storage — only a `count`. Rejected keeping N
  separate instances (v5): it forced per-instance ids/health and allowed states the design
  forbids (e.g. attacking a buried estate).
- **One unified `progress` (0–100) for both build and health, gated by a `completed` bool** —
  chosen over separate `build_progress` (0–4) and `health` (0–100). Decisive reason from the
  user: with separate numbers you can "finish a build that has 1 health" — nonsense. One track
  makes 100% = full health by definition, and makes build-damage and structural-damage the
  *same* operation. The `completed` flag is retained because `progress == 50` alone can't
  distinguish "half-built" (cap 0, keep building) from "completed then damaged" (cap +1,
  repairable).
- **Build length as a stored per-project percentage `build_step` (default 25)** — replaces the
  hardcoded "4 work units". A build action moves `progress` by `build_step`%; `ceil(100 /
  build_step)` actions finish it. Future projects can take any number of actions (e.g.
  `build_step = 10` → 10 actions). Chosen over a stored unit-count int because the unified
  0–100 track is already a percentage; one knob also scales repair.
- **Building tops are now sabotageable (reverses v5)** — v5 made under-construction projects
  un-attackable ("no health to lose"). With the unified track, sabotaging a build site simply
  knocks back its `progress`. The user wants build sites attackable; "completed" only changes
  whether the hit reads as build-knockback or health-damage and whether it contributes to cap.
- **Destruction takes a hit at 0, not the hit that reaches 0** — `progress` clamps at 0 and the
  instance survives as a husk; `count` only drops when a sabotage lands while `progress` is
  already 0, revealing a pristine instance below. Gives every instance a one-hit grace buffer;
  chosen over destroy-on-reaching-0 (no buffer) and stall-forever (never destructible).
- **Front shields the pool** — only the top is a legal sabotage target, so the pristine pool
  beneath is untouchable while a top is in-flux. Falls out of "only the newest is attackable";
  the user accepted that a build-in-progress shields the existing stack until it resolves.
- **`domains` kept as a list, multi-domain cap deferred** — the user flagged future multi-domain
  projects, so the field is a list now, but no base stack lists more than one domain yet and
  multi-domain cap math is left to the spec that introduces the first such project.
- **Repair reuses `build_step`% (30 gold + 1 AP)** — one size knob for build and repair; default
  25% matches v5's +25 repair. Recorded as a chosen default (flagged for review in the spec).
- **Reference docs reconciled at build time, not now** — `data-models.md`, `formulas.md`,
  `architecture.md` are as-built truth; per the Change rules the builder updates them when the
  code lands, not the architect up front. `game-ui_spec.md` and `actions_spec.md` (behavior
  specs) were updated alongside this spec.

Pending: this is a sizable rework touching cap, build, sabotage, repair, maintenance, the API,
NPC targeting, and many tests — expect the blueprint to span several slices.
