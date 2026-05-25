# ADR: SM Domain as Attention

**Date:** 2026-03-29
**Status:** Accepted

---

## Context

The Social Media domain (SM) was designed to function differently from the other 14 city domains. In the real world, social media is not just another power sector — it is a meta-layer that amplifies, exposes, and destabilizes other power sectors. A faction dominating the Finance domain behaves differently depending on whether they are under public scrutiny or operating in obscurity.

The design question was: how do you model this meta-layer without turning SM into special-case spaghetti code throughout the entire engine?

Two approaches were considered:

1. **An `is_sm` flag on the Domain model** — a boolean stored in `domains.json` that marks one domain as the SM domain. Code throughout the engine checks this flag.
2. **Name-based identification with a dedicated attention float** — SM is identified by its name. The utilization field is repurposed as an Attention float. All SM-specific behavior is gated by `domain.is_sm()` checks, which are a single method that compares the name.

The flag approach is simpler at first but implies that SM's special behavior is baked into the Domain schema, making the distinction structural. The name-based approach keeps the Domain schema generic and confines the special behavior to the `is_sm()` method and the places that call it.

---

## Decision

The Social Media domain is identified by name, not by a stored flag.

### Identification

```python
class Domain:
    def is_sm(self) -> bool:
        return self.name == "Social Media"
```

The domain name "Social Media" is the canonical identifier. This name must match the name used in `domains.json`. If the SM domain is renamed, this method must be updated accordingly. There is no `is_sm` field in the Domain dataclass.

### SM Utilization = Attention

For the SM domain, the `utilization` field stores the Attention float rather than a weight sum.

- All other domains: `utilization = sum of unit weights in domain`
- SM domain: `utilization = WorldState.sm_attention`

Attention is stored separately in `WorldState.sm_attention` and mirrored into `Domain.utilization` for the SM domain at the start of each cycle. This means the SM domain's utilization cannot be compared directly to other domains' utilization ratios without checking `is_sm()` first.

### Attention States

| State | Attention Range | Effect |
|---|---|---|
| `baseline` | 0 – 200 | Normal cycle order, no systemic pressure |
| `elevated` | 201 – 600 | Named units have reduced Obscure effectiveness; SM units have increased visibility |
| `crisis` | 601+ | Normal cycle order suspended; all NPC action selection receives defensive bias |

State transitions are calculated at the start of each cycle's pre-setup phase (Step 0) and stored in `WorldState.sm_state`.

### Crisis State Behavior

When `sm_state == "crisis"`:
- The NPC engine applies a flat weight multiplier to Protect, Entrench, Defend, and Obscure actions for all units across all domains.
- No domain is exempt from crisis pressure — SM attention represents citywide exposure, not just exposure in the SM domain.
- The cycle order is not literally reordered, but blocked and attacked units gain an additional contest bonus in step 7.

### Named vs Anonymous Units

Units in the SM domain have two sub-archetypes:

- **Named units** (`"Named"` in traits or `anonymous == False`): visible actors. They receive full SM faction bonuses but are targetable by anyone who knows they are active in SM.
- **Anonymous units** (`"Anonymous"` in traits or `anonymous == True`): obscured actors. They are not valid targets for Attack or SpyTargeted until an Expose action has identified them. The `resolve_targeted_spy()` action is the mechanism for stripping anonymity.

Anonymity is not SM-exclusive. Anonymous units in any domain follow the same targeting rules. SM is where anonymity is most tactically significant because of the meta-layer exposure effects.

### SM Attention Changes

Attention rises from:
- Decisive outcomes involving Named units in any high-visibility action
- SM-domain Grow actions
- Cascade events triggered by domain chaos
- Faction-vs-faction conflicts in high-cap domains

Attention decays naturally each cycle at a configured rate. The decay is not fast enough to counteract a rapid succession of high-visibility actions — sustained conflict raises and sustains crisis state.

---

## Consequences

### Positive

- The Domain schema stays generic. No booleans polluting the core data model for a single special case.
- `is_sm()` is a single, findable method. Any developer searching for SM-special behavior can grep for `is_sm()` and find every affected code path.
- SM attention as a system pressure layer — rather than as a resource to be captured — produces more interesting strategic texture. Factions cannot simply "own" SM and be done; they must manage attention as an ongoing concern.
- Anonymous units and the Expose mechanic create a distinct style of covert play that operates across all domains, not just SM.

### Negative

- The SM domain's `utilization` field has different semantics from all other domains. Any code that iterates over all domains and computes `utilization / cap` must check `is_sm()` or the SM ratio will be meaningless.
- The name-based identification creates a soft coupling between the code and the domain name string. If "Social Media" is renamed in `domains.json` without updating `is_sm()`, the SM mechanics silently stop applying.
- Crisis state applies a blanket defensive bias to all NPC selections. This is a global effect that can feel blunt — during a crisis, every unit shifts toward defense regardless of their traits or goals. The tradeoff is simplicity over nuance.
