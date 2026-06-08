# Polis — Govern the Ungovernable

> A pure rules engine wrapped in a living conversation. Watch a Greek city rise or fall on the deals you strike.

![Polis — the game view](docs/InPlayScreenshots/Maininterface.png)

**Polis** simulates power struggles inside an ancient Greek city-state. Eight spheres of influence are contested by **41 factions** (noble houses, priesthoods, merchant guilds, generals, orators), each with embedded leadership and AI-driven personalities. You play the **Mayor** — historically the *Prytanis*, the city's presiding official, who cannot command, only negotiate.

**The innovation:** Faction leaders bargain through live LLM audiences. The terms you settle aren't flavor text — they parse into structured `<deal>` blocks that the deterministic simulation engine enforces. Honored, broken, or ignored — consequences persist across cycles.

## Current Status: Playable Alpha 🧪

**The core loop is complete and tested.** The simulation engine, treasury logic, mayor actions, live LLM negotiation audiences, and structured deal enforcement all run end-to-end.

- ✅ **Proven Mechanics:** 372 committed tests cover contest math, cycle order, events, and the LLM deal-parser.
- ✅ **Stable Engine:** Runs deterministically with zero external dependencies (stub mode) or with live AI providers.
- ⏳ **Thematic Implementation:** No final art, audio, or UI assets. Visuals rely on raw engine output; placeholder content remains throughout.
- ⏳ **Content & Systems In Progress:**
    - End-game victory/defeat conditions (bankruptcy, coalition, revolt loss)
    - Population, food, and disaster systems
    - City-wide Project implementation (mechanics ready, thematic content pending)
    - Mayor advancement (dynamic respect scaling based on city growth)
    - Self-improving AI groundwork: every live audience is captured to a structured JSONL corpus (`backend/logs/audiences.jsonl`) — the dataset for a future fine-tuned, packaged small model that runs the factions without per-call API cost

This is a **foundation-ready** codebase. The hard problems of state safety, emergence, and AI integration are solved; next comes content scaling and game feel tuning.

## Quick Start

Want to run the simulation, play as the Mayor, or dive into the code?
*   🚀 **[Getting Started](./GETTING_STARTED.md)** — Install dependencies, set up LLM providers, and run the headless or full UI version.
*   🎮 **[How to Play](./HOW_TO_PLAY.md)** — Learn the rules of negotiation, faction dynamics, and the cycle loop.

## How It Works — and Why It's Built This Way

Polis moves beyond standard "chat-with-NPC" tropes by treating AI as a **negotiation layer** rather than a narrative generator. Six choices give it stability, emergence, and player agency.

### 1. An LLM Whose Words Become Rules — and the Engine Trusts None of Them
Audiences aren't flavor text. When a faction leader agrees to a deal, their spoken terms are parsed into a structured `<deal>` block and validated against what is mechanically possible (known action types, valid IDs, clamped durations). Invalid terms are silently dropped; one-sided deals are rejected. A malformed model response degrades to "no deal" — never a crash, never an illegal state mutation. **The model proposes; the rules engine disposes.**

And even a *valid* acceptance doesn't bind on its own — the human Mayor must **confirm** it. This keeps the probabilistic LLM from unilaterally writing durable state and makes the player the commit point for every consequence.
*   **Why It Matters:** Players aren't roleplaying; they are making binding contracts that alter the math of the world. If a faction later breaks a deal, the engine records it — reputation drops and consequences cascade into future cycles. That is genuine accountability.

### 2. Emergent, Not Scripted
There are no hand-authored event chains or "scripted outcomes." Each cycle, the 41 distinct personalities are shuffled into a random turn order and act **one at a time** — so Faction B reads the state Faction A just left behind.
*   **The Mechanics:** Factions have traits, resources, and goals. Cascades, power vacuums, and collapses fall out of ordering and contest math, not a script. A slight change in a single trait (e.g., a General becoming more aggressive) can trigger a civil war no designer could predict.
*   **Why It Matters:** Every playthrough is unique. The depth scales with complexity without requiring exponential authoring time.

### 3. Bounded, Summarized Memory
Factions remember their history with the Mayor, but memory is finite. As interactions accumulate, the LLM summarizes older notes into condensed memories, preventing context overflow while retaining long-term strategic intent.
*   **The Balance:** This allows for deep, multi-cycle relationships (grudges, alliances) without breaking token limits or degrading performance over long runs.

### 4. A Pure Rules Engine at the Core
The `engine/` directory is a pure Python library that imports **only the standard library**. No web frameworks, no database calls, no I/O.
*   **The Architecture:** The API, database, and UI wrap this engine; they do not reach into it. This separation ensures the simulation logic is:
    *   **Fast:** The full suite runs in ~1 second.
    *   **Testable:** 372 unit tests verify every formula and state transition.
    *   **Portable:** It can run headless, in the browser, or inside a backend service with zero dependencies.
*   **Why It Matters:** This proves the codebase is engineered for longevity and reliability, not just prototyping.

### 5. Provider-Agnostic & Offline-First
The system uses a decoupled three-layer architecture (Engine ↔ Prompt Adapter ↔ Provider Interface) that supports:
1.  **Live Providers:** Anthropic, OpenAI-compatible endpoints (Ollama, LM Studio), and more.
2.  **Offline Stub:** A deterministic fallback for zero-dependency testing.
3.  **Future Path:** Integration with a purpose-built, fine-tuned small language model (SLM) optimized for negotiation logic.

*   **The Benefit:** The game runs fully **offline by default** — the stub needs no AI provider, API key, or network, so the whole loop and test suite work without any model configured. This ensures immediate portability today, while paving the way for fully self-hosted, low-latency AI operations tomorrow.

### 6. Snapshot-Based Persistence
Saves are engine snapshots (self-contained JSON per cycle), not ORM rows. Loading rehydrates the pure engine objects directly. Forward-only column migrations keep older saves loadable as the schema grows.

## Tech Stack

A modern, type-safe stack chosen for performance and testability:

| Layer | Technology | Why Chosen |
| :--- | :--- | :--- |
| **Simulation Engine** | Python 3.13 (Standard Lib Only) | Deterministic logic, zero framework overhead, max portability. |
| **API** | FastAPI + Uvicorn | High-performance async with automatic, self-documenting OpenAPI. |
| **Database** | SQLite + SQLAlchemy | Lightweight persistence, forward-compatible schema migrations. |
| **Frontend** | Vue 3 + Vite | Reactive UI, fast build times, clean component separation. |
| **Testing** | pytest | Strict test coverage (372+ tests) tied to spec criteria. |

> *Note: The frontend layer is intentionally decoupled from `engine/`. Future builds may replace Vue 3 with alternative UI frameworks without affecting simulation logic.*

## Development Workflow: The Plumbline Method

Polis was engineered using **Plumbline**, a custom spec-driven workflow I designed to replace ad-hoc prompting with a disciplined, auditable pipeline.

Unlike typical AI-assisted development where prompts generate unverified code, Plumbline enforces a strict lifecycle. Every Blueprint, decision, and deviation is documented and reviewable. Trust but verify. More information on Plumbline is available on GitHub: https://github.com/BytesFromToby/plumbline

> The goal isn't that AI wrote the code. It's that the intent behind each piece is documented, verified, and signed off against running software.




