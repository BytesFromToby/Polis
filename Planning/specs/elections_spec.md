# Elections Specification

**Version:** v2 (slices 3a–3b)
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

## Outcome (the title ladder)

The Mayor has a standing on an ordered title ladder (`engine/titles.py`: Prytanis → Archon →
Strategos → Hegemon → Basileus), indexed by `Mayor.title_rank` (starts 0).

- **Win →** climb one rung (`ElectionWon`); reaching the **top rung (Basileus) is victory** —
  `world.game_over = True`, `end_cause = "victory"`.
- **Lose →** depends on the profile:
  - `election_loss_is_terminal` (hard): the run ends — `end_cause = "voted_out"` (`ElectionLost`).
  - otherwise (normal/easy): **demote one rung** (`ElectionDemoted`), with a **floor** — demoting
    below the bottom rung ends the run (`voted_out`). So a player earns a loss cushion by climbing.

Both terminal outcomes reuse the fail-states machinery. The frontend shows a defeat banner for
`voted_out` / removal / collapse, and a distinct **victory** banner for `victory`.

### Slice boundary

- **Slice 3a (shipped 2026-06-21):** the verdict, cadence, campaign warning, approval readout.
- **Slice 3b (shipped 2026-06-21):** the **title ladder** — win climbs, top rung = victory; loss
  demotes-with-floor (normal/easy) or is terminal (hard, via `election_loss_is_terminal`). Current
  title surfaced in the `/state` election block + top bar.
- **Deferred (next):**
  - **Titles in the audience prompt.** The ladder standing is mechanical + displayed; threading the
    current title into the negotiation prompt (so leaders address a Basileus differently than a
    Prytanis) needs reconciling with the player-chosen `player_title` (player-identity_spec) and is
    a separate follow-up.
  - **"Support me in the election" as a deal term** — the hook tying the audience/deal system to the
    vote, tracked by the existing deal-fidelity/memory.
  - **A dedicated forecast panel** beyond the current top-bar readout; per-difficulty election
    tuning (`election_pass_score` / `election_interval`).

---

## Data & API

- `Mayor.title_rank: int = 0` — the only new persisted state (serialized); cadence is derived from
  `world.cycle` + the interval and the verdict reads live currencies.
- `engine/titles.py`: `TITLE_LADDER`, `TOP_RANK`, `title_for_rank`.
- `engine/special/election.py`: `election_approval`, `cycles_until_election`, `process_election`
  (called in `run_cycle` after the removal check), `election_summary` (UI block).
- `serialize_state` gains an optional `balance` arg and an `"election"` block
  (`{interval, next_in, approval, pass_score, title, rank, top_rank}`) when a Mayor is present;
  `/state` passes the run's profile. GameView shows the title + readout in the top bar, a `voted_out`
  end-cause label, and a distinct victory banner.

## Balance dials (engine/balance.py)

`election_interval` (12), `election_warn_window` (4), `election_pass_score` (0.0),
`election_public_weight` (0.5), `election_loss_is_terminal` (False; **hard: True**). Other dials are
the same across profiles for now; tunable per difficulty later.

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
- A win climbs the title ladder; reaching the top rung sets `end_cause="victory"` —
  `tests/test_election.py`  `[automated]`
- A loss demotes one rung on forgiving profiles (game over only below the bottom rung) and is
  terminal when `election_loss_is_terminal` (hard) — `tests/test_election.py`  `[automated]`
- `Mayor.title_rank` survives serialization — `tests/test_election.py`  `[automated]`
- `/state` exposes the election readout (incl. current title); the GameView top bar shows the title
  + "Election in N · approval ±X"; victory shows a distinct banner — `[human-required]`

## Tests

- `tests/test_election.py` — approval math + rank weighting, cadence, warning window, win/lose
  verdict, title-ladder climb/demote/victory/floor, difficulty terminal-vs-demotion, summary
  readout, serialization, `run_cycle` integration.
