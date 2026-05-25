# Game Master UI — Spec

**Status:** Scoping
**Last updated:** 2026-04-03

---

## Purpose

A browser-based interface for game masters to watch the simulation run cycle by cycle and intervene — editing factions, units, and world state in real time. Supports multiple users, each running their own city.

---

## Tech Direction

- **Browser-based** from the start. No terminal UI.
- **Near term:** FastAPI serving HTML/JS frontend, runs on localhost.
- **Long term:** Same frontend, potentially hosted.
- **Real-time updates:** Polling for now. WebSocket push added later.

---

## Screens / Sections

### 1. Login / Register
- [ ] Register with username and password (email optional, hidden for now)
- [ ] Login with username and password
- [ ] Logout

---

### 2. City Selection (Home Screen)
Shown after login. User picks what to do next.

- [ ] List user's existing cities / sim runs (name, cycle count, last played)
- [ ] Browse city templates (pre-built + user published)
  - Show: city name, author, description, setting
- [ ] Load a template to start a new run
- [ ] Start a blank city (city builder)
- [ ] Resume an existing run

---

### 3. City Builder
For creating or editing a city before the sim starts.

- [ ] Set city name, description, setting, details
- [ ] Add / edit / remove domains
- [ ] Add / edit / remove factions (name, rating, domain, traits)
- [ ] Add / edit / remove named starting units (domain ratings, traits, faction)
- [ ] Save city
- [ ] Publish city as a template (fills name, author, description, setting, details)

---

### 4. GM Dashboard (active sim)
Main view while the sim is running.

#### View & Watch
- [ ] Current cycle number and world state summary
- [ ] Faction panel — all factions with key stats (rating, entrench, domain, member count, leader)
- [ ] Unit panel — named units with domain ratings, faction, traits
- [ ] Domain panel — all domains and which factions occupy them
- [ ] Narrative log — readable output per cycle

#### Sim Controls
- [ ] **Step** — run one cycle. GM can intervene freely between steps.
- [ ] **Run X** — run X cycles uninterrupted (max 100). GM cannot intervene mid-run. Auto-stops early if a Crisis is triggered (Crisis system TBD).
- [ ] Reset to starting city (cycle 0)

#### GM Interventions
- [ ] Edit faction stats mid-sim (entrench, rating, traits)
- [ ] Edit unit stats mid-sim (domain ratings, traits, faction membership)
- [ ] Add a new faction mid-sim
- [ ] Dissolve a faction manually
- [ ] Add a new named unit mid-sim
- [ ] Remove a unit
- [ ] Force a specific action for a unit or faction next cycle
- [ ] Trigger an event manually (collapse, split, cascade)

#### Cycle History
- [ ] Browse past cycle snapshots
- [ ] View state and narrative log from any previous cycle

---

## Decisions

| Question | Decision |
|----------|----------|
| Tech stack | FastAPI backend, browser frontend |
| Real-time updates | Polling first, WebSocket later |
| Framework | Vue.js — Options API style |
| GM edits logged? | Yes — written as part of each cycle snapshot in SQLite |
| Read-only during Run X? | Yes — GM interventions blocked while Run X is in progress |

---

## Out of Scope (for now)
- Users viewing each other's running cities
- Scripted scenarios / automation
- Mobile layout
