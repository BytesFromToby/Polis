# Walkthrough Recommendations — Polis — 2026-06-17 (PM)

Deferred items from the second run (covers the scales + pottery UI). The **morning** file
(`Recommendations_2026-06-17.md`) still stands for its items unless noted below. Baseline → end:
556 → **557 backend green**; frontend builds. Quick-Path fixes applied are in `WalkthroughLog_*_pm.md`.

---

## Priority: MEDIUM

### Add a frontend test runner — the game-ui `[automated]` Done-whens are unbacked
- **Area:** `frontend/` (no `vitest`/test script today — only `dev`/`build`/`preview`)
- **What:** Three game-ui `[automated]` items have **zero** automated backing because there is no JS
  test runner: (1) the faction block never shows the raw multi-decimal `rating`; (2) `api.js` has no
  `commission`/`/projects/commission`; (3) `npm run build` exits 0. Add a minimal **vitest** setup (or
  a grep-based CI gate for 1 & 2) plus a CI step that runs `npm run build`.
- **Why:** these are the spec's only frontend automated criteria and nothing regression-guards them;
  a stray `f.rating.toFixed` or a re-added `commission` would slip through. The build gate also catches
  the kind of template error this UI redo could regress.
- **Effort:** medium · **Path:** Full (new tooling/CI) · **Spec affected:** game-ui_spec

### Reconcile special-factions "The Public's Role in Faction Politics" (still open)
- **Area:** `Planning/specs/special-factions_spec.md` (L113–124); `engine/npc/behavior.py`
- **What:** Disposition-driven faction effects (content → −5 Steal, angry → +10 Harm, restless →
  Broker-DC +2) are **not in code** and are superseded by the Confidence posture modifier. Mark
  superseded, or re-spec the decree-AP / Broker-DC bits as confidence-band consequences.
- **Why:** unimplemented spec prose invites someone to "fix" code to a dead design. Flagged in the
  AM run; **still open**.
- **Effort:** small · **Path:** Full (architect)

### Retune piety off its resting Zealous pin (still open)
- **Area:** `engine/needs/scales.py` (`PIETY_PER_LEVEL=4`, `PIETY_PARITY=1.0`)
- **What:** the standard city rests at **Zealous** (piety ~100), so the zealot tax is always on —
  same defect class as the consumption Sodden-pin the inspector FAILed. Measure the std temple
  `piety_supply/demand` and set PARITY so rest ≈ Observant; add a resting-band regression mirroring
  consumption's.
- **Effort:** small · **Path:** Quick (constant + a test) · **Spec affected:** public-needs (provisional)

### Add a resting-band health tool (still open)
- **Area:** new `tools/resting_bands.py`
- **What:** run the std city N cycles × a few seeds, print the resting band of all seven scales +
  the production-wire efficiency; flag any pin to an extreme. Would have caught both the consumption
  Sodden-pin and the open piety-Zealous debt.
- **Effort:** small · **Path:** Full (new tool)

---

## Priority: LOW

### Decide the fate of the unreachable defensive clamps
- **Area:** `engine/needs/scales.py` — `unrest_target` clamp `[0,100]`; `production_efficiency`
  clamp `[EFF_MIN, EFF_MAX]`
- **What:** both clamps are **unreachable by real inputs** (max unrest pressure = 80 < 100; max
  efficiency = 1.10 < 1.25). Their tests are therefore smoke-only. Either drop the clamps (they're
  dead) or keep them as defensive and accept the smoke tests — but don't pretend they're covered.
- **Effort:** small · **Path:** Quick · **Spec affected:** none

### Audience needs-line — prove the post-drift band link end-to-end
- **Area:** `tests/test_audience_terms.py` (or a new integration test)
- **What:** the needs-line is asserted at prompt-build time; the "shows the *current* (post-drift)
  bands after a cycle" link is inferred, not asserted through a real `run_cycle`. One end-to-end test.
- **Effort:** small · **Path:** Quick (add test)

### Carried from the AM run (still open)
- Document `Treasury.guard_paid_this_cycle` in `treasury_spec.md` (LOW).
- Harden `test_cycle.py` orchestration coverage — initiative re-roll, treasury-before-loop ordering,
  `build_actions_this_cycle` reset end-to-end (MEDIUM; the AM run did utilization + Skip-exclusion).
- `audit.py` dirties the tree with generated artifacts — `.gitignore` or a `--check` mode (LOW).
- Foreman plan-quality: stop baking specific numeric **tuning literals** the builder must trust —
  cite the spec / a measurement step instead (the consumption-PARITY FAIL is the cost). (LOW; skill-level.)
