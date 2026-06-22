# Reputation decay band — investigated as a tuning lever, kept at 10

**Date:** 2026-06-21

## What

Extracted the reputation-decay band (previously a hardcoded ±10 in `apply_reputation_decay`) into a
balance dial `reputation_decay_band`, threaded `balance` into the decay call. **Default left at 10**
— the playtested value — after a tuning investigation showed widening it makes the game worse.

## Why (the investigation)

Two endgame playtests pointed at the same governor: support/faction-rep settling at ±10 because
decay pulls anything past the band back toward it, while *inside* the band nothing decays. That
caps the whole support→approval→election range to a ±5 knife-edge, so the hope was that widening
the band would yield more decisive election mandates.

A sweep across band values (passive Mayor, seed 7) disproved it:

| band | passive-Mayor outcome |
|------|------------------------|
| 0    | degenerate — everything collapses to ~0; approval 0 *passes* the ≥0 threshold → **auto-victory** |
| 10   | support spans ±10, declines, **voted out @ c60** (neglect loses — correct) |
| 12–25 | honeymoon (+12…+20) sticks in the no-decay zone → **auto-victory @ c48** |

The cliff between 10 and 12 is sharp. The reason is structural: the band's "wide range" comes
entirely from the **no-decay zone**, which is the very thing that lets a passive well-fed honeymoon
stick instead of regressing. Range and regression are **coupled** in this one mechanism — you
cannot widen mandates without removing "neglect loses." (band=0 fails differently: with decay
pulling everything to 0 and the election pass score at 0, a neutral approval *wins*.)

## Conclusion

The decay band is the wrong lever for decisive mandates. Kept at the proven **10** (neglect loses,
coherent rise-and-fall arc), now a tunable dial for future experiments. Decisive mandates, if
wanted, need a *different* change — most promising: **decay toward 0 at a rate** (so active play
outpaces it for a real mandate while neglect regresses) **paired with a positive election pass
score** (so a neutral approval no longer auto-wins). That is a reputation-dynamics redesign
deserving its own slice and real active-play playtesting (a player doing public works / meeting
factions each cycle), which the passive harness can't represent — explicitly deferred, not forced.

## Consequences

- The band is now in the single source of truth (consistency, tunable), behaviour unchanged at 10.
- A recorded dead-end so this lever isn't re-litigated; the real levers are named for a future pass.
