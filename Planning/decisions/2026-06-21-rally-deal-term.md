# Rally as a deal term — "publicly endorse me"

**Date:** 2026-06-21

## What

Made `committed_action: "Rally"` a valid audience deal term: a faction can be bound by a deal to
publicly champion the Mayor (the Rally action) for N cycles, pumping public support each cycle.
Added `"Rally"` to `VALID_FACTION_ACTIONS` (response parser), described it in the audience prompt
(term line, JSON schema, valid-actions list), and threaded `title` into the faction-terms template.
Spec: `audience_spec.md` (Valid Deal Terms). Follows the faction-influence proposal's deal hook.

## Why these choices

- **Rode the existing `committed_action` machinery.** Rally is targetless like Grow/Protect/Toil, so
  it needed only to be whitelisted + described; `_committed_plan` forces it, `_execute` resolves it
  with the `mayor`/`balance` already threaded for the live influence action, and deal fidelity/memory
  tracks compliance. No new deal mechanics.
- **Shipped the positive term, deferred the abstain.** "Cease agitating" (`committed_abstain`
  · `Agitate`) needs the behavior engine to zero a targetless action's weight under abstain — the
  current abstain only excludes a *target* for Harm/Steal. That's a small but distinct change, so it
  is a noted follow-up; the positive "endorse me" term is the headline and is clean.
- **Offered to any faction.** Unlike Toil (chain-role only), Rally is universal — any faction can be
  asked to publicly back the Mayor, so it's unconditionally in the prompt.

## Consequences

- The headline LLM-negotiation USP now reaches the endgame: "back me publicly" is a tradeable
  promise whose delivery (or betrayal) is tracked, feeding the support that elections and the
  removal spiral read.
- Remaining faction-influence follow-up: the `committed_abstain` · `Agitate` term (targetless-abstain
  handling).
