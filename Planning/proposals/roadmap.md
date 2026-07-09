# Roadmap — Future Features

**Date:** 2026-06-21 · **Updated:** 2026-07-09 — the spine shipped; re-centered on UI.
**Status:** PLANNING — a map of forward work, not a commitment. Each entry links to its
detailed proposal (or flags that one is still needed). Re-prioritize freely.

## How to read this

This is the index of where Polis is going and *why each item earns its place*. The original
organizing idea was **make it a game → make it deep → make it pretty** — depth and polish on a
sandbox that can't end is decoration, so stakes came first.

**That spine is now built** (see below). A run can be won, lost, and finished. So the axis has
turned: the load-bearing gap is no longer stakes, it's **feel** — the engine produces the most
dramatic content in the game (clashes, strikes, collapses, removals) and renders it as log lines.
So the near-term order is **make it visible → make it pretty → then make it deeper.**

Detailed designs live in sibling proposals; this doc decides *order and leverage*, not mechanics.

---

## ✅ Shipped — the spine (was "do these first")

Everything the 2026-06-21 spine called for is done, each a full Plumbline run with independent
inspector PASS. Kept here as the record of what the rest now builds on.

- **Balance extraction** — dials + easy/normal/hard profiles in `engine/balance.py`, threaded
  through the cycle (`balance_spec.md`).
- **Endgame / fail-states** — terminal Mayor removal, population collapse + latched warning,
  recurring election verdict, assassination/coup risk (`fail-states_spec.md`, `endgame.md`).
- **Elections + title ladder** — the recurring verdict and the climb/demote-with-floor score
  (`elections_spec.md`).
- **Faction influence** — Rally / Agitate sway Public opinion of the Mayor, both authorable as
  deal terms in an audience (`faction-influence.md`).
- **Resource chains — the full food layer** — barley + **fish** + **flocks**, three sources with
  redundancy (one out → Hungry, all out → Starving); 6 of 7 Public scales live
  (`food-supply_spec.md`, `public-needs_spec.md`). *Food is complete — the next resource work is a
  new chain type (Goods/wool), an optional bet, not a continuation.*
- **OverrideLLM** — deterministic choose-the-outcome provider for testing/GM.

---

## ▶ Now — make it visible, then pretty

### 1. Placeholder scheduled events (small — the UI-testing enabler, do first)
The event deck is currently **all `random`** and gated on chaos / Public bands, so on a calm test
city events may never fire — which is why they feel invisible and why the UI can't be built
against them reliably. This step is *not* the real events-as-crisis work (that's in Next); it just
gives the UI dependable beats to render.

- **Add a scheduled trigger** to the scripted path in `engine/events/event_system.py`:
  `at_cycle: N` (fire once) and `every_n_cycles: N` (recurring). Confirm the scripted deck is
  actually wired into the cycle runner.
- **Author a tiny scheduled deck** — a few clearly-named placeholder events (e.g. a cycle-4
  "honeymoon over", an "admirer" every 10 cycles, one scripted disaster) so the procession band
  always has something to show. *Effects can be no-op for now* — visibility is the whole point;
  real effects land when events-as-crisis is built.

### 2. UI update — Living Pottery (the big near-term block)
Render the game's actors and events in the Geometric-pottery style itself — flat two-ink SVG
figures that scale, move, and wear. Full design in [ui-living-pottery.md](ui-living-pottery.md);
tokens/grammar already adopted in `reference/ui-art-direction.md`. Follow its build order, each
step independently shippable:

1. **Token reskin** — pottery palette into `frontend/src/style.css`.
2. **Part kit + generator playground** — all 28 factions from real JSON on a dev page; the cheap
   go/no-go gate on silhouette readability *before* any real UI wiring.
3. **FactionVessel** into the existing faction cards — first payoff, no layout change.
4. **Structured event emission** (the one backend touchpoint — additive event objects alongside
   the narrative strings) → **ProcessionBand** (hover-expand, pull-text, click-to-focus). *This is
   where the placeholder events from step 1 pay off — they're the beats the band renders.*
5. **Cracks / staples** — deal-break scars as permanent surface wear; ships whenever.

Promote via a Spec Impact pass (architect) when scheduled: `game-ui_spec.md` sections + the
structured-event contract in `events_spec.md` / `cycle-runner_spec.md`.

---

## ⏭ Next — depth, on a stakes-bearing, pretty base

| Feature | Leverage | Notes |
|---------|----------|-------|
| **Inter-faction politics / dynamic audiences** | **High — the USP.** | Factions react to *each other's* deals, alliances, rivalries — where political stories come from. The differentiator worth showing off in the new UI. |
| **Events as crisis generators** | High | The real version of step 1 above: events that *feed the failure spirals* (see [crisis-and-stance](crisis-and-stance.md)), plus the reputation-touching effect field the placeholders skipped. |
| **Stance layer** | Medium–High | Bounded post-audience / post-crisis LLM calls writing durable in-character state (`crisis-and-stance.md`); the chosen middle path between scripted and LLM-decides-everything. |
| **Projects (more)** | Medium, low-risk | Mechanically understood; good "between big features" work ([projects-rework](projects-rework.md)). |
| **Weather** | Medium — only if it *drives* | Worth it only as a driver of the resource chains (harvest variance → food crises) and a crisis input. Cosmetic seasons are a trap — fold into Events / resource-chains. |
| **Goods chain (wool)** | Optional | The next resource *type* now that food is complete; a new bet, not a continuation. |

**Progression / difficulty / achievements** ride along here: title-ladder progression is felt in
the audience prompt (built); difficulty falls out of the shipped balance profiles + fail-states;
achievements stay **deferred** until there are goals worth achieving against.

---

## 🔭 Later — the stretch (mostly post-UI)

Captured from the Fable brainstorm (`../Ideas From Fable.md`) — deliberately over the horizon,
not scoped. Highest-leverage bets flagged.

- **The deception experiment (Banana × Polis)** — instrument the stance layer's betray-intent;
  measure whether models defect more when defection pays. Fuses the two flagship projects into one
  research story; runs on hardware already owned. *(Highest wow-per-effort of the stretch set.)*
- **Polis as an MCP server** — expose the Mayor's seat over MCP; any agent can try to govern. Thin
  wrapper over the existing API; maximally 2026-shaped demo.
- **PolisBench** — a negotiation benchmark off the deterministic economy + parser (deal-close rate,
  term validity, breach rate over N cycles).
- **The Oracle** — fork the snapshot, run it forward headless, speak the real trajectory as Delphic
  verse. Only honest because the engine is deterministic.
- **The unreliable Chronicle** — end-of-run history written from the winning coalition's view; an
  inherently shareable artifact.
- **Alternate skins** — the engine is a politics engine wearing a toga (boardroom, mafia, station,
  HOA…). Ship one skin and Polis becomes "the engine," not "a game."
- Plus: soft-promise parsing, rumor graph, ostracism, stasis/civil-war mode, multi-party audience,
  the Persian envoy, voice audiences, dynasty/deep-time.

### Deferred (decided, not now)
- **Embedded local-LLM runtime** — a product-packaging problem; validate 8B audience quality via a
  documented Ollama preset first. Swap-in under the existing `LLMConfig`; nothing wasted.
  *(Decision 2026-06-21.)*
- **Local-LLM keep-alive option (QoL)** — settings toggle, off by default, 5–60 min only, never
  `-1`. Needs Ollama's native `/api/chat` keep-alive, not the global env var. *(Constraints
  2026-06-22.)*

---

## Suggested sequence

1. **Placeholder scheduled events** — `at_cycle` / `every_n_cycles` trigger + a small no-op deck,
   so events are reliably visible.
2. **UI — Living Pottery**, in its own 5-step order (reskin → playground → vessels → structured
   emission + procession → cracks). The structured-emission step is where the placeholder events
   become the procession's content.
3. **Inter-faction politics / dynamic audiences** — deepen the USP on the new visual base.
4. **Events as crisis generators** (real effects, reputation field) + **stance layer**.
5. **Projects**, **weather-as-crisis-driver**, optional **Goods chain**.
6. *Later:* the stretch set — deception experiment, MCP server, PolisBench, and the rest.

---

## Cross-references

- [ui-living-pottery.md](ui-living-pottery.md) — the UI build (the Now block's item 2)
- [../Ideas From Fable.md](../Ideas%20From%20Fable.md) — the full brainstorm the stretch set draws from
- [endgame.md](endgame.md), [elections-and-titles.md](elections-and-titles.md) — the shipped spine, in detail
- [crisis-and-stance.md](crisis-and-stance.md) — events-as-crisis + the stance layer (Next block)
- [public-model.md](public-model.md) — the Public subsystem + extreme-crisis events
- [resource-chains.md](resource-chains.md) — the resource map (food complete; Goods/wool next type)
- [projects-rework.md](projects-rework.md), [city-generation.md](city-generation.md),
  [faction-resource-map.md](faction-resource-map.md), [civic-public-works.md](civic-public-works.md),
  [demo-redesign.md](demo-redesign.md)
</content>
