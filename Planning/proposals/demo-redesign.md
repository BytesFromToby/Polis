# Demo Redesign — Working Decision Log

**Status:** SCRATCH / in progress — not a spec. Decisions captured live as we work them through.
**Started:** 2026-06-03
**Goal:** get Polis into a strong **demo** state. The system was built for a deeper sim end-goal; we are free to redesign whatever serves the demo.

Scope this pass: **faction interactions · faction cap · projects rework.** (Cap + projects largely parked for a later session; faction model settled first.)

---

## Decided

### Faction model
- **Interactions stay same-domain.** Harm/Steal remain restricted to the attacker's domain — simplifies for now.
- **Rank = float `1.0–10.0`, min 1.0.** (Was float 1.0–5.0.)
  - `level = int(rank)` — drives the dramatic "rose to a new level" beat, UI display, and ability gates (e.g. project initiation at level ≥ 3).
  - The float fraction **is** the growth progress — no separate progress stat needed.
  - *Intended payoff:* feed the raw float into resolution → power scales gradually; fire the integer crossing as the narrative beat → keep the drama. (Roll dial still open — see below.)
- **Growth increment → `1 / (n + 1)`** where `n = level`. (Was `1 / (2^n + 1)`; the `2^n` is unusable across 10 levels — level 9→10 would take ~500 grows.)
  - Decel preserved (low levels rise fast, apex is a grind): grows-to-next = `n+1`, ~54 grows total to reach 10.
  - **Provisional** — tune by feel. Cap resistance and other pressures share the braking load, so the curve only needs to be roughly right.
- **`entrench` — DROPPED.** Its only real job was gating advancement (`entrench ≥ 50`); the float crossing an integer replaces that. Removing it also de-duplicates with `health`.
- **`health` — KEPT** (1–100, survival/condition). Harm's effect on it to be retuned once rank scaling settles.
- **Result: a faction is `rank` (float, shown as level) + `health`.** Plus identity, traits/leader, relationships, deal-commitment plumbing.

### Faction conflict — Harm, Protect, the Break
- **Factions are permanent — they never die.** LLM integration makes adding/removing factions too costly, so the roster is fixed.
  - *Cascade:* removes faction **collapse + power-vacuum** machinery (a death is what spawned vacuums) → simplifies the end-of-cycle.
- **`health` is a "breaking-point" buffer, not a death meter.** Harm grinds it down; Protect restores it; hitting 0 triggers a **Break** — the faction is knocked back but lives on.
- **Break (health → 0):** roll the consequence —
  - **75% → level −1** ("fall from power"). Rank lands at `(level−1).0` — bottom of the lower tier; in-progress fraction lost.
  - **25% → leader dies + auto-regenerates** (new name, fresh traits, wiped personality_notes; new leader enters `weakened` for 1 cycle). Kept rare so we don't churn through leaders or break LLM character continuity.
  - **Health resets to 75** after a Break.
- **Level-1 factions can't be targeted by Harm or Steal** — a safe floor (simple, and keeps aggression pointed at level 2+ rivals). Temporary: Grow is uncontested, so a level-1 faction climbs back out on its own. The behavior engine skips level-1 factions when choosing aggression targets.
  - *Fallback:* if some non-aggression source (e.g. an event) ever zeroes a level-1 faction's health, the Break is a **reprieve** — health reset only; the 25% leader-death still applies.
- **Conflict loop:** grow power · grind down rivals' health · Protect to recover/brace · Break them for a level drop or a leadership decapitation. No eliminations.
- **Action set: Grow · Protect · Harm · Steal · Help** (+ Build/Sabotage, parked). **Block is CUT** — removes the hidden delayed-fire trap, which was the main cross-cycle timing mess.
  - **Grow** → uncontested; +`1/(n+1)` to rank; crossing an integer = the level-up beat.
  - **Protect** → **immediate +50 health** (flat % of max, capped at 100). No round-long brace (dropped for simplicity).
  - **Harm** → contested; damages target **faction** health: **−30 decisive / −15 partial** (starting numbers). The path to a Break. Can't target level-1.
  - **Steal** → contested; transfers rank = **half the attacker's grow increment = `0.5/(attacker_level+1)`**. Same-domain; not level-1; target floors at 1.0.
  - **Aid** (the Help action) → uncontested; **+25 health to an ally** (flat % of max). Targets **Friends / `allied with`**; **cross-domain allowed** (adds back some cross-domain interaction). *May need tuning.*
- **Steal balance — two brakes, one per direction (a nice result):**
  - *High → low:* attacker-based magnitude is tiny (e.g. 0.05), so a growing low faction **outpaces** it. ✓ (the intended property)
  - *Low → high:* magnitude is large (0.25) **but** the low attacker rarely **wins** the contest vs a high defender, so it rarely lands. ✓
  - **Coupling:** brake #2 depends on level mattering in the roll → linked to the deferred **roll dial.** If level is scaled down hard, low-vs-high steal lands more and the reverse issue returns. *Fallback if it griefs: cap a steal at the target's fraction-above-floor.*
- **Break balance note:** Protect (+50) out-heals one Harm (−30), and **Aid (+25 from an ally) stacks on top** — a defended alliance is very hard to Break. So Breaks need **focus-fire** or an isolated, can't-afford-to-Protect target. Intended (Breaks = climactic, alliances sticky) — watch in play.

### Domain / cap (pieces decided; full rework parked)
- **Faction-weight table `0,2,4,8,16` — DROPPED.** Domain **utilization = Σ faction level** in the domain. A cap is a **"level budget"** (cap 20 = four level-5s or two level-10s). Kills the second exponential.
  - *Nuance for later:* levels are `int`, so utilization steps at each level-up; summing the float rank would give smoother cap pressure. Parked with the cap.
- **Cap resistance — keep, reconcile later.** Currently wired at two thresholds that disagree with the reference table:
  - behavior nudge at `utilization ≥ cap × 0.9` (Grow −20, Steal +15)
  - hard block at `utilization ≥ cap` (Grow can't succeed)
  - reference `formulas.md` describes 4 states (open <60 / passive 60–85 / contested 85–95 / blocked ≥95) — more granular than the 0.9/1.0 actually used.
  - This 4-state ramp is the natural home for "harder to grow as the domain fills."

### Cycle
- **1 action / faction / cycle** — already the case; no change.

---

## Open

- **Roll dial** — raw float vs scaled into the d20. *Deferred — but now coupled to Steal balance: if level stops swaying the roll, low-vs-high steal griefs.*
- **Tuning numbers** — Protect +50 · Aid +25 · Harm −30/−15 · grow `1/(n+1)` · Steal `0.5/(n+1)` — starting points, settle by feel.
- **Cycle-run cleanup** — mostly handled: no-death removed collapse + power-vacuum; Block cut removed the delayed-fire wrinkle. Remaining: skim the other end-of-cycle steps.
- **Cap / projects rework** — parked thread.

---

## Downstream edits this will force (track so nothing is missed)
- `reference/data-models.md` — remove `entrench`; widen rank to 10; remove weight-table references; drop `WorldState.power_vacuums` (no death); note leader auto-regen + health reset-to-75 on Break.
- `reference/formulas.md` — rating ceiling 5→10; new grow increment; drop faction-weight table; reconcile cap-resistance thresholds.
- `actions_spec.md` — Harm/Protect effects redefined (no entrench); rescale magnitudes for 1–10.
- `faction-behavior_spec.md` — state modifiers referencing entrench/weight; near-cap logic.
- `cycle-runner_spec.md` — remove collapse + power-vacuum steps (no death); add the Break resolution; end-of-cycle steps that touched entrench.
