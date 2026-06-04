# Decisions: Faction + Actions Redesign (demo)

Specs: `Planning/specs/actions_spec.md`, `faction-behavior_spec.md`, `cycle-runner_spec.md`
Reference: `Planning/reference/data-models.md`, `formulas.md`
Full design log: `Planning/proposals/demo-redesign.md`
Date: 2026-06-03

- **Rank kept a float, widened 1–5 → 1–10.** `level = int(rank)`; the integer crossing is the dramatic level-up beat, while the fraction tracks gradual growth. Rejected a pure-linear "straight number" — it loses the decel curve and dumps all power-braking onto the cap.
- **Grow increment `1/(n+1)`** — replaces `1/(2^n+1)`, which is unusable across 10 levels (level-9→10 would take ~500 grows). Provisional; tuned by feel.
- **`entrench` dropped.** Its only real job (gating level advancement) is replaced by the float crossing an integer; otherwise it just duplicated `health`. Faction is now `rank` + `health`.
- **Factions are permanent (never die).** Adding/removing factions is too costly under LLM integration. Cascade: removed faction collapse + power-vacuum machinery from the cycle. `health` became a "breaking-point" buffer instead of a death meter.
- **Break (health→0): 75% level −1 / 25% leader death + regen** (new leader `weakened` 1 cycle); health resets to 75. Rejected *always leader death* (churns leaders, breaks LLM character continuity) and *always level drop* (less drama). The split keeps decapitations rare.
- **Level-1 factions can't be targeted by Harm/Steal** — simpler than special-casing a level-1 Break, and a safe floor for weak factions (temporary, since uncontested Grow lifts them out).
- **Block cut** — the hidden delayed-fire trap was the main cross-cycle timing mess for little demo value.
- **Aid added** (+25 health to an ally; Friends/`allied with`; cross-domain) — fills the missing cooperation; cross-domain restores some cross-domain interaction the same-domain aggression rule removed.
- **Faction-weight table (0,2,4,8,16) dropped; utilization = Σ level** (a domain `cap` is a "level budget"). Kills the second exponential.
- **Harm/Steal kept same-domain** — deliberate simplification for the demo.
- **Deferred:** the "roll dial" (raw float vs `floor(rating)` in contests — coupled to Steal balance) and the full **cap + projects** rework.

**Pending: cap + projects rework** — separate later pass.
