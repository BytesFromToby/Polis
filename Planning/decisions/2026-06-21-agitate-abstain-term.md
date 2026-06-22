# Agitate abstain as a deal term — "cease turning the people against me"

**Date:** 2026-06-21

## What

Made `committed_abstain: "Agitate"` a valid audience deal term: a faction can be bound to stop
taking the Agitate action for N cycles. Completes the faction-influence deal-hook pair (Rally to
endorse, Agitate-abstain to stand down). Behavior engine now distinguishes targetless vs targeted
abstain; prompt offers it; spec documents it.

## Why these choices

- **Targetless abstain = zero the action's weight; targeted abstain = exclude the named target.**
  The existing `committed_abstain` was target-oriented (don't Harm/Steal faction Y). Agitate has no
  target, so the rule is: `if committed_abstain_action and not committed_abstain_target →
  weights[action] = 0`. This generalises cleanly without disturbing the targeted Harm/Steal path
  (which still excludes only the named faction in target selection).
- **No parser change needed.** `committed_abstain` was never validated against the action set and
  already preserves an empty target, so an Agitate abstain parses as-is; only the prompt and the
  behavior rule were added.

## Consequences

- The deal hook is complete: a Mayor can buy a faction's public endorsement (Rally) *or* its
  silence (stop Agitate), both tracked by deal fidelity/memory and both feeding the support that
  elections and the removal spiral read. The faction-influence proposal is fully shipped.
- The targetless-abstain rule is general — any future targetless action becomes abstainable for free.
