# Roadmap — Future Features

**Date:** 2026-06-21
**Status:** PLANNING — a map of forward work, not a commitment. Each entry links to its
detailed proposal (or flags that one is still needed). Re-prioritize freely.

## How to read this

This is the index of where Polis is going and *why each item earns its place*. The organizing
idea: most of the backlog is **depth** (more simulation) and **polish** (better feel), but the
load-bearing gap is **stakes** — a run can't be won, lost, or finished. Depth and polish on a
sandbox that can't end is decoration. So the spine is: **make it a game → make it deep → make it
pretty.**

Detailed designs live in sibling proposals; this doc decides *order and leverage*, not mechanics.

---

## The spine (do these first — they unlock the rest)

### 0. Balance extraction (prerequisite, not a feature)
Pull the difficulty/feel dials into one source of truth (`engine/balance.py`) with named
**profiles** (easy / normal / hard) layered over a base set — the same pattern as LLM profiles.
Store the chosen difficulty on `SimRun` (mirrors `llm_profile_id`).

- **Why first:** every stakes threshold below (population floor, election cadence, assassination
  trigger) is a dial. Centralize before they get hardcoded across five modules; the constant set
  only grows as Events / Weather / Projects land.
- **Discriminator for what to extract:** "Would I ever change this to retune the game?" Yes →
  central dial (`DRIFT_STEP`, `POP_GROWTH`, `UNREST_EASE`, `POP_MIN`, support deltas, election N).
  No → leave it (`RATING_MAX`, the d20, term-type maps).
- **Do it as a pure refactor first:** `normal` = today's exact numbers, all tests green, behavior
  unchanged. Prove the plumbing without touching the game, *then* add easy/hard and tune.
- **"Self-balancing" = super-easy mode** becomes ~one override block, not a second codebase.
- For-sale upside: clean data profiles make **moddable / custom difficulty** nearly free later.
- *Spec needed:* `balance_spec.md` (dial inventory, profile structure, `SimRun.difficulty` wiring).

### 1. Endgame / fail states — **the missing major feature**
A run cannot end. There is already a half-built failure spiral (low Public support →
`RemovalRisk`; debt > 800 → removal coalition) but **it has no teeth** — it emits narrative and
the game continues. See [endgame.md](endgame.md) for the full design: one terminal
"Mayor loses office" resolution fed by multiple triggers (population collapse, election verdict,
assassination/coup). This is what turns a sandbox into a game and is the precondition for
difficulty, achievements, and progression all being meaningful.
- Builds on the unbuilt [elections-and-titles](elections-and-titles.md) (the election trigger in detail).

---

## Depth (the simulation) — after stakes exist

| Feature | Leverage | Notes |
|---------|----------|-------|
| **More dynamic audiences** | **High — this is the USP.** | The emergent LLM negotiation is what no other city-sim has. Highest-value form = **inter-faction politics**: factions react to *each other's* deals, alliances, rivalries. That's where political stories come from. |
| **Events** | High, half-built | Best framed as **crisis generators** that feed the failure spirals (see [crisis-and-stance](crisis-and-stance.md)), not random flavor. Needs the **latched-event subtype** (see endgame.md) — reusable by Weather too. |
| **Weather** (cycle = 1 month) | Medium — only if it *drives* | Worth it only as a driver of the resource chains (harvest variance → food crises) and a crisis input. As cosmetic seasons it's a trap. Fold into Events / [resource-chains](resource-chains.md); don't build standalone. |
| **Projects** (more) | Medium, low-risk | Mechanically understood, lower risk. Good "between big features" work. See [projects-rework](projects-rework.md). |
| **Resource chains** (full) | In flight | v1 shipped (barley); next slice = fish. Continue per [resource-chains](resource-chains.md). Gives the city a body for crises to wound. |

---

## Progression & motivation — depend on stakes

| Feature | Verdict |
|---------|---------|
| **Mayor progression** | Needs a span to progress *across* — i.e. the election/term structure. Largely the **title ladder** in [elections-and-titles](elections-and-titles.md): titles thread into the audience prompt so advancement is *felt in conversation*, not cosmetic. Build with elections. |
| **Difficulty levels** | Falls out of **balance profiles (item 0)** + **fail states (item 1)**. "Harder numbers" on a sandbox that can't be lost is just tedious — difficulty is meaningless until a run can fail. |
| **Achievements** | **Defer.** Meaningless without goals to achieve against. Revisit after endgame + titles exist. |

---

## Presentation (the feel) — last, on a stable base

| Feature | Notes |
|---------|-------|
| **Approval / forecast readout** | **Not polish — a prerequisite for elections.** Without a visible needle, losing a vote feels random instead of "I saw it coming." Build with elections. |
| **Animations** | Polish; real payoff for a sellable feel. |
| **City map** | **Rabbit-hole risk.** Only build if it renders *live state* (factions, projects, crises), not a static backdrop. |
| **Temp sounds** | Lowest priority; easy to add late. |

---

## Deferred (not now)

- **Fully-integrated local LLM (embedded runtime).** The plumbing already supports local models
  via `openai_compat` (Ollama). A turnkey embedded runtime is a *product-packaging* problem
  (cross-platform binaries, GPU detection, multi-GB model distribution) that only pays off when
  packaging **for sale** — and only after the cheaper question is answered: *does an 8B local
  model produce good-enough audiences?* Validate quality first via a documented Ollama preset
  (Llama 3.1 8B), embed later. Nothing is wasted — the embedded runtime is a swap-in under the
  existing `LLMConfig` abstraction. *Decision recorded 2026-06-21: skip the preset build for now;
  current BYO-LLM path works.*
- **Local-LLM keep-alive option (settings, QoL).** Let the player keep the Ollama model resident
  to avoid the multi-second cold reload on intermittent audience calls (see memory: `keep_alive`).
  Constraints (per request 2026-06-22): a **settings option, off by default**, settable **5–60
  minutes** only — **never `-1`/indefinite** (the worry is the model lingering in VRAM/RAM after the
  game is quit; a bounded TTL auto-frees). Implementation note: Polis calls Ollama via the
  OpenAI-compat `/v1` endpoint, which doesn't take `keep_alive` per request — so this likely needs
  Polis to send `keep_alive` on Ollama's native `/api/chat`, or pass it as an extra body param, not
  just the env var (the env var is global + persists beyond the app, which is exactly what we're
  avoiding). Don't implement yet.

---

## Suggested sequence

1. **Balance extraction** (refactor; enables every threshold below)
2. **Endgame spine** — terminal end-state + make existing removal triggers actually end the run
3. **Population fail + latched warning event** (smallest stakes slice; builds reusable warning pattern)
4. **Elections + approval readout + title ladder** (the big endgame; Mayor progression rides along)
5. **Events as crisis generators**, then **inter-faction politics / dynamic audiences** (deepen the USP)
6. **Projects**, then **UI polish** (depth and feel on a stakes-bearing base)
7. *Later:* assassination/coup (extends the removal coalition), weather (as a crisis driver),
   achievements, embedded LLM

---

## Cross-references

- [endgame.md](endgame.md) — fail-state framework (the spine's item 1)
- [elections-and-titles.md](elections-and-titles.md) — the election trigger + title ladder, in detail
- [crisis-and-stance.md](crisis-and-stance.md) — disasters as crisis generators + bounded LLM stance
- [public-model.md](public-model.md) — the Public subsystem + extreme-crisis events
- [resource-chains.md](resource-chains.md) — the full resource map (v1 shipped; fish next)
- [projects-rework.md](projects-rework.md), [city-generation.md](city-generation.md),
  [faction-resource-map.md](faction-resource-map.md), [civic-public-works.md](civic-public-works.md),
  [demo-redesign.md](demo-redesign.md)
