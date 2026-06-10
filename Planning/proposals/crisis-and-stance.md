# Proposal: Crises & the Stance Layer (LLM jurisdiction)

**Date:** 2026-06-10
**Status:** PROPOSAL — not built, not scheduled. Captured from a roadmap discussion before a
development pause. Promote via a Spec Impact section when scheduled (see `proposals/README.md`).

Two halves that only work together: **disasters/events as crisis generators**, and a bounded
expansion of the LLM's role so factions *respond in character* to those crises. Also records the
considered-and-rejected alternative (LLM agents making all faction decisions) so the reasoning
isn't relitigated later.

## Problem (two seams)

1. **Audiences are good, but nothing forces you into them.** The negotiation layer is the
   headline mechanic, yet the sim rarely generates moments where the Mayor *needs* a deal.
   Crises are the missing generator of negotiation material.
2. **The audience aftermath doesn't write into behavior.** A leader can swear loyalty in an
   audience and their faction then acts as if the conversation never happened, because
   trait-weighted action selection doesn't know about it. Deals are enforced mechanically, but
   the faction's *general posture* never shifts. This is the one place the deterministic layer
   genuinely can't reach: language-borne context.

## The jurisdiction test

Put an LLM call exactly where it knows something the trait math cannot: **language-borne
context** — the conversation that just happened, the half-honored deal, the grudge, the crisis
as experienced. Everywhere else, trait-weighted selection is faster, deterministic, testable,
and (for small local models especially) probably *better* at picking actions.

## The spectrum considered

| Model | What the LLM does | Verdict |
|---|---|---|
| **Free agent** | Emits faction actions directly, every faction, every cycle | **Rejected.** Kills the engineering identity ("the model proposes; the rules engine disposes" — determinism, 372 tests, stub mode, replays). Practical killer: sequential initiative (B reads the state A left) forbids parallelizing ~41 calls → minutes per cycle on a local model, every cycle. Small models are weak strategic optimizers; this trades everything defensible for a slower, noisier copy of the trait math. |
| **Agent-as-policy** | Engine shortlists legal actions; LLM picks one + a reason | Safe but unscoped — still ~41 calls/cycle. The reason strings are nice narrative flavor. Possible later, not the entry point. |
| **Agent-as-stance** | LLM runs only at *moments where language should change behavior*, and writes durable state the deterministic engine consumes | **Chosen direction.** ~2–5 calls per cycle at most, each at a moment the player can feel. |

## The stance layer

A stance call fires on a **trigger**, reads the faction's memory/personality/current state, and
writes **bounded durable state** — never actions directly:

- **Triggers:** end of an audience (does the leader's attitude shift? do they intend to honor or
  quietly break the deal?); a crisis/event hitting the faction's domain; a major world moment
  (faction Break, election result — see `elections-and-titles.md`); optionally a low-frequency
  "strategy review" every N cycles.
- **Writes (all already-existing or near-existing state):** trait intensity adjustments (the
  trait-evolution machinery exists), a stance/goal enum the weight builder consumes
  (faction-behavior_spec), deal-fidelity intent (feeds the existing break-deal path), a line of
  leader memory.
- **Engine consumes stance deterministically.** Same parse-validate-clamp discipline as the deal
  parser: model output is a constrained block, invalid writes dropped, malformed response = no
  stance change. Stub mode falls back to a deterministic stance derivation (e.g. from the same
  modifiers the trait system already uses), so offline-first and the test suite survive untouched.

### Crises as the other half

Events/disasters (events_spec) become the **crisis calendar**: a disaster hits the harbor →
Fishermen stance call fires with the crisis in context → desperate faction seeks (or is
receptive to) an audience → relief negotiation → election later judges the handling. Disasters
generate the negotiation material; the stance layer makes the response feel authored by the
faction rather than by a formula. With `resource-chains.md`, disasters also get something
material to break (a Food gauge cut is legible; "−3 health/cycle" is not).

## Why this serves the Steam goal

- **Latency hides in player-driven moments.** Audience + stance calls happen around
  conversations and crisis beats, not in the per-cycle hot path. A packaged small model for
  audiences-plus-stance is a tractable ship target; per-faction-per-cycle inference means
  multi-GB models, GPU requirements, and support tickets.
- **Training corpus alignment.** `backend/logs/audiences.jsonl` is negotiation data — it trains
  the audience/stance model. It does *not* train a decision policy; and logging the trait
  engine's own decisions to train one would just distill the existing math into a worse copy.
  The fine-tune bet (README "self-improving AI groundwork") and the stance layer point at the
  same model.

## Prerequisite housekeeping

`events_spec.md` (v1, 2026-05-17) and `special-factions_spec.md` (v1) predate the June reworks —
they still reference entrench, Block, decree, Turn a Blind Eye, Withhold Resources, and Broker a
Deal, all cut. Picking this up starts with reconciling those specs to the post-rework model
(rank + health, audience-as-sole-influence-channel). How much of events v1 is actually
implemented vs spec-only needs a surveyor pass first.

## Cycle touchpoints (rough)

- Stance calls: post-audience (API-side, where audience already lives) and post-event
  (Step 8 adjacency) — never inside the faction action loop.
- Stance enum read by the weight builder (faction-behavior) at declare time, like traits are.
- New JSONL capture for stance calls alongside `audiences.jsonl` (same future fine-tune).

## Open questions

- Stance representation: reuse trait intensities only, or add an explicit per-faction
  stance/goal field? (Explicit field is more legible in UI and prompts; traits-only adds no schema.)
- Strategy-review cadence: every N cycles for all factions is the slippery slope back to
  41 calls — maybe only for factions above a rank threshold, or only when something happened
  to them since the last review.
- Does the *player* see stances? (Probably yes eventually — a faction's posture is exactly the
  kind of signal that makes audiences feel consequential — but UI is out of scope here.)
- Deal-fidelity intent vs existing break mechanics: does the LLM *decide* breaks, or only bias
  the existing probability? Biasing is safer; deciding is more in-character. Start with biasing.
