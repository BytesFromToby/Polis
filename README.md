# Polis — Govern the Ungovernable

> A pure rules engine wrapped in a living conversation. Watch a Greek city rise or fall on the deals you strike.

![Polis — the game view](docs/InPlayScreenshots/Maininterface.png)

**Polis** simulates power struggles inside an ancient Greek city-state. Eight spheres of influence are contested by **41 factions** (noble houses, priesthoods, merchant guilds, generals, orators), each with embedded leadership and AI-driven personalities. You play the **Prytanis** — the presiding official who cannot command, only negotiate.

**The innovation:** Faction leaders bargain through live LLM audiences. The terms you settle aren't flavor text — they parse into structured `<deal>` blocks that the deterministic simulation engine enforces. Honored, broken, or ignored — consequences persist across cycles.

## Current Status: Playable Alpha 🧪

**The core loop is complete and tested.** The simulation engine, treasury logic, mayor actions, live LLM negotiation audiences, and structured deal enforcement all run end-to-end.

- ✅ **Proven Mechanics:** 268 committed tests cover contest math, cycle order, events, and the LLM deal-parser.
- ✅ **Stable Engine:** Runs deterministically with zero external dependencies (stub mode) or with live AI providers.
- ⏳ **Thematic Implementation:** No final art, audio, or UI assets. Visuals rely on raw engine output; placeholder content remains throughout.
- ⏳ **Content & Systems In Progress:**
    - End-game victory/defeat conditions (bankruptcy, coalition, revolt loss)
    - Population, food, and disaster systems
    - City-wide Project implementation (mechanics ready, thematic content pending)
    - Prytanis advancement (dynamic respect scaling based on city growth)

This is a **foundation-ready** codebase. The hard problems of state safety, emergence, and AI integration are solved; next comes content scaling and game feel tuning.

## Quick Start

Want to run the simulation, play as the Prytanis, or dive into the code?
*   🚀 **[Getting Started](./GETTING_STARTED.md)** — Install dependencies, set up LLM providers, and run the headless or full UI version.
*   🎮 **[How to Play](./HOW_TO_PLAY.md)** — Learn the rules of negotiation, faction dynamics, and the cycle loop.

## Architectural Innovations

Polis moves beyond standard "chat-with-NPC" tropes by treating AI as a **negotiation layer** rather than a narrative generator. The system is built on four pillars that ensure stability, emergence, and player agency.

### 1. An LLM Whose Words Become Rules
Audiences aren't flavor text. When a faction leader agrees to a deal, their spoken terms are parsed into a structured `<deal>` block. This JSON object is validated against the engine's constraints (e.g., "Is this tax rate legal?", "Does this faction control the Harbor?") and enforced as **live game state**.
*   **The Innovation:** The simulation trusts *neither* side blindly. If a faction breaks a deal, the engine records it, updating reputation scores and triggering cascading consequences in future cycles.
*   **Why It Matters:** This creates genuine accountability. Players aren't just roleplaying; they are making binding contracts that alter the math of the world.

### 2. Emergent, Not Scripted
There are no hand-authored event chains or "scripted outcomes." The story emerges from the collision of 41 distinct personalities acting on a deterministic rules engine.
*   **The Mechanics:** Factions have traits, resources, and goals. They act sequentially each cycle, reacting to the state left by previous actors. A slight change in a single trait (e.g., a General becoming more aggressive) can trigger a power vacuum or a civil war in a way no designer could predict.
*   **Why It Matters:** Every playthrough is unique. The depth scales with complexity without requiring exponential authoring time.

### 3. Bounded, Summarized Memory
Factions remember their history with the Prytanis, but memory is finite. As interactions accumulate, the LLM summarizes older notes into condensed memories, preventing context overflow while retaining long-term strategic intent.
*   **The Balance:** This allows for deep, multi-cycle relationships (grudges, alliances) without breaking token limits or degrading performance over long runs.

### 4. A Pure Rules Engine at the Core
The `engine/` directory is a pure Python library that imports **only the standard library**. No web frameworks, no database calls, no I/O.
*   **The Architecture:** The API, database, and UI wrap this engine; they do not reach into it. This separation ensures the simulation logic is:
    *   **Fast:** The full suite runs in ~1 second.
    *   **Testable:** 268 unit tests verify every formula and state transition.
    *   **Portable:** It can run headless, in the browser, or inside a backend service with zero dependencies.
*   **Why It Matters:** This proves the codebase is engineered for longevity and reliability, not just prototyping.

## Design Decisions

The specific engineering choices that prioritize safety and player agency:

### Treating the LLM as an Untrusted Source
A faction leader can say anything. The engine trusts **none** of it.
*   **The Safety Layer:** The response parser extracts the `<deal>` block and validates every term against what is mechanically possible (known action types, valid IDs, clamped durations). Invalid terms are silently dropped; one-sided deals are rejected.
*   **Result:** A malformed model response degrades to "no deal" — never a crash, never an illegal state mutation. The model proposes; the rules engine disposes.

### A Confirmation Gate Between Dialogue and Consequence
A leader *accepting* a proposal does not immediately create a deal. The human player (Prytanis) must **confirm**.
*   **The Reason:** This keeps the probabilistic nature of the LLM from unilaterally writing durable state. It makes the human the commit point, ensuring players feel agency over critical decisions.

### Sequential Initiative for Genuine Emergence
Each cycle, factions are shuffled into a random turn order and act **one at a time**.
*   **The Effect:** Faction B reads the state left by Faction A. This allows for real-time reactions—cascades, power vacuums, and collapses—that fall out of ordering and contest math, not a script.

### Provider-Agnostic & Offline-First
The system uses a decoupled three-layer architecture (Engine ↔ Prompt Adapter ↔ Provider Interface) that supports:
1.  **Live Providers:** Anthropic, OpenAI-compatible endpoints (Ollama, LM Studio), and more.
2.  **Offline Stub:** A deterministic fallback for zero-dependency testing.
3.  **Future Path:** Integration with a purpose-built, fine-tuned small language model (SLM) optimized for negotiation logic.

*   **The Benefit:** The full game and test suite run with **zero external dependencies** by default (using the stub). This architecture ensures immediate portability today, while paving the way for fully self-hosted, low-latency AI operations tomorrow.

### Snapshot-Based Persistence
Saves are engine snapshots (self-contained JSON per cycle), not ORM rows. Loading rehydrates the pure engine objects directly. Forward-only column migrations keep older saves loadable as the schema grows.

## Tech Stack

A modern, type-safe stack chosen for performance and testability:

| Layer | Technology | Why Chosen |
| :--- | :--- | :--- |
| **Simulation Engine** | Python 3.13 (Standard Lib Only) | Deterministic logic, zero framework overhead, max portability. |
| **API & Auth** | FastAPI + Uvicorn | High performance async, automatic OpenAPI docs, JWT/Bcrypt security. |
| **Database** | SQLite + SQLAlchemy | Lightweight persistence, forward-compatible schema migrations. |
| **Frontend** | Vue 3 + Vite | Reactive UI, fast build times, clean component separation. |
| **Testing** | pytest | Strict test coverage (268+ tests) tied to spec criteria. |

> *Note: The frontend layer is intentionally decoupled from `engine/`. Future builds may replace Vue 3 with alternative UI frameworks without affecting simulation logic.*

## Development Workflow: The Plumbline Method

Polis was engineered using **Plumbline**, a custom spec-driven workflow I designed to replace ad-hoc prompting with a disciplined, auditable pipeline.

Unlike typical AI-assisted development where prompts generate unverified code, Plumbline enforces a strict lifecycle. Every Blueprint, decision, and deviation is documented and reviewable. Trust but verify. More information on Plumbline is available on GitHub: https://github.com/BytesFromToby/plumbline

> The goal isn't that AI wrote the code. It's that the intent behind each piece is documented, verified, and signed off against running software.




