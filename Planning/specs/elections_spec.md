# Elections Specification

**Version:** v1 (slice 3a)
**Date:** 2026-06-21

A recurring election: every `election_interval` cycles the city renders a verdict on the Mayor's
tenure. The scheduled-judgment counterpart to the [removal spiral](fail-states_spec.md) (the
mid-term coup). Designed in [elections-and-titles.md](../proposals/elections-and-titles.md);
the endgame heartbeat from [endgame.md](../proposals/endgame.md) (trigger 2).

---

## The verdict (legible weighted sum)

Approval is a single number in −50..+50, blended from currencies that already exist:

```
approval = election_public_weight · Public.support                 (the popular vote, −50..+50)
         + (1 − election_public_weight) · Σ(rep(f) · rank(f)) / Σ rank(f)   (the influential vote)
```

- **Popular vote:** the Public's `support`.
- **Influential vote:** per-faction Mayor reputation, **weighted by faction rank** — propping up a
  high-rank ally is worth more than placating a minor one, which makes faction rank matter *to the
  Mayor*, not just to the faction.
- Deterministic on purpose (the approval readout shows the same number the vote will use).
- **Win** if `approval >= election_pass_score` (default 0 — net non-negative standing).

## Cadence & campaign window

- An election is held when `cycle % election_interval == 0` (stateless modular cadence). Default
  interval 12 — long enough to govern, short enough a session sees a verdict; a balance dial.
- In the `election_warn_window` cycles before (default 4) a **campaign warning** fires each cycle
  carrying the projected approval and whether the Mayor is "favoured" or "in danger" — so a loss is
  foreseen and fought, not random.

## Outcome (slice 3a)

- **Win →** a fresh mandate; the run continues (`ElectionWon`).
- **Lose →** the run ends: `world.game_over = True`, `end_cause = "voted_out"` (`ElectionLost`),
  reusing the terminal machinery from fail-states. The frontend shows the reign-ended banner.

### Slice boundary

- **Slice 3a (this spec, shipped 2026-06-21):** the verdict, cadence, campaign warning, the
  approval readout, and **loss = game over** for every difficulty (the roguelike option from the
  proposal). Surfaced in the cycle, the `/state` payload, and the GameView top bar.
- **Deferred (next):**
  - **Title ladder + demotion-with-floor.** The forgiving loss outcome the proposal leans toward
    needs a rank ladder to demote within; titles also thread into the audience prompt (player_title
    is already in the prompt — the ladder makes it dynamic) and the top rung is a *victory*. Until
    then, loss is terminal on all profiles. (`election_pass_score` / `election_interval` can also be
    set per difficulty when the ladder lands.)
  - **"Support me in the election" as a deal term** — the high-value hook tying the audience/deal
    system to the vote, tracked by the existing deal-fidelity/memory.
  - **A dedicated forecast panel** beyond the current top-bar readout.

---

## Data & API

- No new persisted state — cadence is derived from `world.cycle` + the interval, and the verdict
  reads live currencies.
- `engine/special/election.py`: `election_approval`, `cycles_until_election`, `process_election`
  (called in `run_cycle` after the removal check), `election_summary` (UI block).
- `serialize_state` gains an optional `balance` arg and an `"election"` block
  (`{interval, next_in, approval, pass_score}`) when a Mayor is present; `/state` passes the run's
  profile. GameView renders it in the top bar and adds the `voted_out` end-cause label.

## Balance dials (engine/balance.py)

`election_interval` (12), `election_warn_window` (4), `election_pass_score` (0.0),
`election_public_weight` (0.5). Same across profiles for now; tunable per difficulty later.

---

## Done when

- Approval blends Public support with the rank-weighted faction reputation per the formula —
  `tests/test_election.py`  `[automated]`
- An election is held exactly on `cycle % election_interval == 0`; the campaign warning fires only
  within the warn window — `tests/test_election.py`  `[automated]`
- Approval ≥ `election_pass_score` → `ElectionWon`, run continues; below → `ElectionLost`,
  `game_over` with `end_cause="voted_out"` — `tests/test_election.py`  `[automated]`
- Cadence scales with `election_interval` (difficulty) — `tests/test_election.py`  `[automated]`
- Stepping into an election cycle while deeply unpopular ends the run via `run_cycle` —
  `tests/test_election.py`  `[automated]`
- `/state` exposes the election readout and the GameView top bar shows "Election in N · approval ±X"
  — `[human-required]`

## Tests

- `tests/test_election.py` — approval math + rank weighting, cadence, warning window, win/lose
  verdict, difficulty cadence, summary readout, `run_cycle` integration.
