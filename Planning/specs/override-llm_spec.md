# Override-LLM Specification

**Version:** v1
**Date:** 2026-06-22

A deterministic **"choose the outcome"** LLM provider for testing and GM use. Instead of calling a
model, the audience's responses — above all the **deal verdict** — are supplied by the operator (a
test harness, the agent driving the API, or a human via a dev-mode UI control). Plugs into the
provider abstraction in [llm-system_spec](llm-system_spec.md); the audience flow and parser are
unchanged.

> Real-LLM audiences against local Ollama (qwen3:8b) are confirmed working (2026-06-22). Override is
> the **deterministic complement** to that — not a replacement. Use the real model for fidelity;
> use override for reproducible tests, scripted demos/screenshots, and hand-authored (GM) outcomes.

---

## Why

- **Deterministic audience testing** — exercise the full audience flow (and deal-term effects)
  with no model, no network, no flakiness. Enables automated UI/integration tests and agent-driven
  testing.
- **Scenario crafting** — force a *specific* deal (e.g. a `Rally` commitment, a rejection, an
  abstain) to verify its effects or capture a screenshot.
- **GM / roleplay** — a human authors the faction's stance and the outcome by hand.

## Design

### A new provider: `"override"`

Add `"override"` to `LLMConfig.provider` alongside `anthropic` / `openai_compat` / `stub`. An
`OverrideLLMClient` implements the same interface —

```python
def complete(self, system: str, messages: list[dict]) -> str
```

— but returns operator-supplied content instead of calling a model. Because it returns the **same
string shape** a model would (narrative text, plus a `<deal>` block on the conclude step), the
audience flow (`audiences.py`) and `ResponseParser` need **no changes** — the override merely
synthesises what a model would have produced. It never touches the network.

### The outcome the operator chooses (the core)

The minimum meaningful choice is the **deal verdict**, supplied as structured data:

- `accepted`: `true | false`
- `faction_terms`: list of term dicts (e.g. `committed_action`/`Rally`, `committed_abstain`/`Agitate`,
  `Grow`, …) — the same schema the parser already accepts (`audience_spec.md`)
- `mayor_terms`: list (e.g. `endorsement`)
- `narrative` (optional): text for the opening / counter / conclusion turns; defaults to neutral
  placeholders if omitted

From these the override client builds a well-formed conclude string —
`"{narrative}\n<deal>{json}</deal>"` — which `ResponseParser` consumes exactly as a real model's
output. Steps 1 and 3 return supplied or placeholder narrative.

### How the outcome is supplied (two channels)

1. **Programmatic** (tests / the agent over the API): the chosen outcome is set on the config or
   the session's audience state before the run. This is the layer that lets automated tests and an
   agent deterministically drive any audience result.
2. **Interactive** (human GM, dev-mode UI): a control in the audience modal lets the operator pick
   the verdict + terms before concluding. **Dev/test-gated** — never shown to normal players.

### Gating / safety

- Override counts as a **valid active AI** (`aiSet` true), so audiences are enabled with it.
- It is a **developer/test provider**: selectable only when a dev/test mode is on (a settings flag,
  an env var, or test-only wiring) — it is **not** offered in the normal player AI-profile list.
- Fully offline and deterministic; no network call is ever made.

### Slices

- **Slice 1 — provider + programmatic supply. SHIPPED 2026-06-22.** The `override` provider/client
  (`OverrideLLMClient`) and the transient `LLMConfig.override` carrier. Deterministic, no network;
  synthesises the conclude `<deal>` from the supplied outcome. (Engine/test layer; no normal-player
  surface.) An **accepted** outcome must supply **both** `mayor_terms` and `faction_terms` — the
  parser's fair-exchange rule rejects a one-sided deal, same as for a real model.
- **Slice 2 — dev-mode UI control + live API. SHIPPED 2026-06-22.** Gated by the `POLIS_DEV_MODE`
  env var (surfaced as `SimStatusResponse.dev_mode`). `/audience/begin` takes `override: bool` —
  when dev mode is on it holds the audience with an override `LLMConfig`, bypassing the profile
  active-AI gate; `/audience/conclude` takes `override_outcome: dict`, injected into the override
  config so the conclusion synthesises that exact `<deal>`. `AudienceModal` shows an "Override
  outcome (dev)" toggle and an accept/reject + term/duration/endorsement chooser; GameView lets the
  audience open in dev mode even on a stub run. Verified end-to-end in the browser (Deal Sealed with
  the chosen Rally↔endorsement terms).

---

## Data / API

- `LLMConfig` gains provider `"override"` and a carrier for the scripted outcome (e.g.
  `override_script`, or the outcome stashed on the session's `audience_state`).
- `OverrideLLMClient` in `engine/llm/client.py`, routed like the other providers.
- (Slice 2) `AudienceModal.vue` gains a dev-mode outcome control; the chosen outcome is threaded to
  the conclude step.

## Done when

**Slice 1**
- `LLMConfig` accepts `provider="override"`; `LLMClient` routes to `OverrideLLMClient`, which never
  makes a network call — `tests/test_override_llm.py`  `[automated]`
- Given a supplied outcome (`accepted` + terms), the override's conclude output parses via
  `ResponseParser` into exactly those terms — `tests/test_override_llm.py`  `[automated]`
- A supplied **reject** outcome yields `accepted=False` with empty term lists —
  `tests/test_override_llm.py`  `[automated]`
- The override provider satisfies the active-AI requirement (an audience is allowed with it) —
  `tests/test_override_llm.py`  `[automated]`
- An audience driven through the override applies the chosen deal's effects — e.g. a supplied
  `Rally` commitment sets `faction.committed_action == "Rally"` — `tests/test_override_llm.py`  `[automated]`

**Slice 2**
- With `POLIS_DEV_MODE` set, `/audience/begin` with `override=True` holds the audience using an
  override config even with no profile (1 AP spent, step-1 returned); without dev mode it is
  rejected by the normal active-AI gate — `tests/test_override_audience.py`  `[automated]`
- `/audience/conclude` with `override_outcome` produces exactly that deal (accept → proposed terms;
  reject → terminal no-deal) — `tests/test_override_audience.py`  `[automated]`
- In dev mode the audience modal exposes the outcome chooser and the audience opens on a stub run;
  the chooser is absent in normal mode  `[human-required]` (verified live 2026-06-22)

## Tests

- `tests/test_override_llm.py` — provider routing + no-network, outcome → parseable deal, reject
  path, active-AI gate, effect application (incl. a Rally/Agitate term).
- `tests/test_override_audience.py` — dev-mode gating + the live begin/conclude/finalize route path.

## File Structure

```
engine/llm/client.py        ← OverrideLLMClient + provider "override"
frontend/src/components/AudienceModal.vue  ← (slice 2) dev-mode outcome control
```

## Cross-references

- [llm-system_spec](llm-system_spec.md) — the provider abstraction this plugs into.
- [audience_spec](audience_spec.md) — the deal-term schema the supplied outcome must match, and the
  active-AI requirement override satisfies.
