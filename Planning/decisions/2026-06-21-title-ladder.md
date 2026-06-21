# Elections slice 3b — the title ladder (demotion-with-floor + victory)

**Date:** 2026-06-21

## What

Made the election two-sided. `engine/titles.py` defines an ordered ladder
(Prytanis → Archon → Strategos → Hegemon → Basileus); `Mayor.title_rank` indexes it. In
`process_election`: a **win climbs** a rung and reaching the **top rung is victory**
(`end_cause="victory"`); a **loss demotes** a rung on forgiving profiles with a **floor**
(demoting below the bottom ends the run), or is terminal where `election_loss_is_terminal` (hard).
The current title is surfaced in the `/state` election block and the GameView top bar; victory gets
a distinct banner. Spec: `specs/elections_spec.md` (slices 3a–3b).

## Why these choices

- **Demotion-with-floor as the proposal's default.** Slice 3a shipped loss = game over because
  demotion needs a ladder to demote within; this slice adds the ladder, so normal/easy now demote
  (you earn a loss cushion by climbing) and only hard stays roguelike. Realises the proposal's
  recorded lean.
- **Victory = reaching the top rung.** Gives the run a positive pole to match the defeats, reusing
  the same `game_over`/`end_cause` machinery (`"victory"`) — the frontend just branches the banner.
- **Title rank on the Mayor, in the engine.** Elections run in `run_cycle`, so the rank lives in
  serialized engine state, not the DB — survives resume for free.
- **Deferred the audience-prompt threading.** The proposal's headline ("leaders address a Basileus
  differently") means putting the current title into the negotiation prompt — but that collides with
  the player-chosen `player_title` (player-identity_spec). Reconciling the two is its own decision,
  so this slice keeps the ladder mechanical + displayed and defers the prompt flavour. Avoids
  silently overwriting a player's chosen title.

## Consequences

- Elections are now two-directional with a win condition — the endgame has both poles.
- Difficulty meaningfully shapes the loss: hard = roguelike, normal/easy = climb-and-cushion.
- Remaining: titles in the audience prompt; "support me in the election" deal term; per-difficulty
  election tuning; assassination/coup (endgame slice 4).
