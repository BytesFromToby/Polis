# Elections slice 3a — the recurring verdict

**Date:** 2026-06-21

## What

Added the election heartbeat. `engine/special/election.py` holds a vote every `election_interval`
cycles (default 12): `election_approval` is a legible weighted sum of Public support (popular vote)
and rank-weighted per-faction Mayor reputation (influential vote); `process_election` (called in
`run_cycle` after the removal check) renders the verdict — win → fresh mandate, lose → `game_over`
with `end_cause="voted_out"` — and emits a campaign warning carrying the projected approval in the
`election_warn_window` (4) cycles before. A readout (`election_summary`) is exposed via `/state` and
shown in the GameView top bar. Spec: `specs/elections_spec.md`.

## Why these choices

- **Legible weighted sum, not dice.** The proposal's recorded lean: the approval readout wants the
  same deterministic number the vote uses, so a loss reads as "I saw it coming," not RNG.
- **Rank-weighted faction vote.** Makes faction rank matter *to the Mayor* (propping an ally is
  electoral strategy), reusing currencies that already exist — no new bookkeeping.
- **Stateless modular cadence.** `cycle % interval == 0` needs no stored term counter and survives
  resume for free.
- **Loss = game over for now (interim).** The proposal leans toward demotion-with-floor, but
  demotion needs a title ladder to demote *within*. Rather than ship a half-ladder, slice 3a uses
  the roguelike loss (a legitimate option in the proposal) and reuses the fail-states terminal
  machinery; the title ladder + demotion is the next slice. Flagged in the spec.
- **Approval readout honoured as a prerequisite.** The proposal calls visible approval a
  prerequisite, not polish — so even this first slice surfaces it (top-bar + campaign warning),
  not just the verdict.

## Consequences

- Polis now has a recurring judgment with real stakes — the single biggest item in the endgame
  proposal — turning the cycles before each vote into a campaign.
- Remaining: title ladder + demotion-with-floor + victory at the top rung; "support me in the
  election" deal term; per-difficulty election tuning; a richer forecast panel.
