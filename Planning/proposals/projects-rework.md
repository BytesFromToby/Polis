# Projects Rework — Working Decision Log

**Status:** PROPOSAL / in progress — not a spec. Decisions captured live as we work them through.
**Started:** 2026-06-05
**Supersedes (when promoted):** `Planning/specs/projects_spec.md` v4 (2026-05-19), which predates the demo redesign and still references removed concepts (`floor`, `entrench`, bespoke per-project effects).
**Goal:** simplify projects for the demo and **fuse them with the (parked) domain-cap system** — projects become the lever that grows a domain's ceiling.

Follows the faction/actions redesign (see `demo-redesign.md`). Factions are now `rank (1.0–10.0)` + `health`, permanent (they Break, never die); `level = int(rank)`; domain `utilization = Σ level`.

---

## Summary

Collapse the 45 bespoke named projects into a **small set of repeatable "base" project types — one per domain** — each with a uniform effect and a build count. A project is no longer a unique structure with a hand-authored effect; it's a repeatable, countable thing you stack to expand a domain.

```
Docks    · Harbor domain   · +2 cap each · built: 3
Barracks · Military domain  · +2 cap each · built: 1
Agora    · Trade domain    · +2 cap each · built: 2
...                                          (one base project per domain)
```

---

## Decided

### Base projects + the cap fusion
- **One base project per domain.** Same name every time it's built (it's a *type* with a count, not many unique entries). Five wharves = one `Docks` entry with `count: 5`.
- **Uniform effect: each build adds +2 to its domain's `cap`.** No per-domain tuning for now.
- **Projects ARE the cap lever.** A domain's ceiling grows only by building base projects in it. Building Docks → Harbor can hold more / bigger factions. This **fuses the projects rework and the cap rework into one job.**
- **Starting cap = starting faction fill × 1.20** (20% headroom over the cycle-0 `Σ level` in that domain).
  - Make it a single named constant — `CAP_HEADROOM = 0.20` — so it's feel-tunable without touching logic.
  - Rationale: domains start ~83% full, so projects matter from cycle 1. *Watch:* the behavior engine already shifts factions Grow→Steal at `utilization ≥ 90% of cap`, so 20% headroom tips a domain into Steal-pressure after a grow or two. 25–30% buys a longer peaceful-growth runway if that feels too tight in play.

### Build model — a project is 4 work units
- **Uniform 4 work units ("4 cycles") to complete a base project.** `build_time` and `faction_build_actions` (the old dual counters) merge into this single number.
- **Two ways to add a work unit:**

  | Path | Gate | Reliability | Cost |
  |---|---|---|---|
  | Faction `BuildProject` | **own domain only** (Military can't build Docks) | **chancy** — `d20 + level` vs DC 12; success = +1 unit, fail = nothing | the faction's action (free) |
  | Mayor "buy a cycle" | — | **guaranteed** +1 unit | **50 gold + 1 action point**, repeatable per AP |

- **Factions co-build:** four *same-domain* factions each spending a `BuildProject` action in one cycle can finish a Dock in that cycle (luck permitting). One faction alone = 4 cycles best case.
- **Mayor can rush:** 3 AP + 150 gold finishes a Dock solo in one turn.
- **Emergent property worth keeping:** the Mayor's *money buys certainty*; faction *labor is free but unreliable*. Two genuinely different paths, not redundant ones. The "4 cycles" is a best-case floor for faction-only building; bad rolls stretch it.
- **Keep the build roll** (DC 12). It adds texture; the determinism cost is acceptable.
- **Sabotage unchanged:** any faction (no domain gate), contested. So build = domain-gated, sabotage = open.

### What replaces `build_cost`
- **The upfront lump `build_cost` is removed.** The Mayor's involvement is now pay-per-cycle (50 gold + 1 AP each), which generalizes the old "50 gold = −1 cycle, once per cycle" accelerator into *the* Mayor build mechanic.

### Special project tiers
- **Keep `tax_collection`** projects (unlock higher tax tiers; already wired into Treasury).
- **Drop `faction_level`** projects and **all bespoke per-project effects.** Rebuild a richer special tier later, on top of the new model.

### Who initiates
- **Both Mayor and factions can initiate** base projects.
- **No gate, no initiation cost.** Any faction may initiate a base project **in its own domain** — no `level ≥ 3` requirement, nothing spent to start it. The build labor (rolls / gold) is the only cost. (The old v4 `floor ≥ 3` gate is dropped.)

### Starting state
- **A city starts with zero base projects.** Cycle-0 domain `cap = fill × 1.20`; every base project is built from scratch during play. (If `tax_collection` ever ships a pre-built starting instance, it's the lone exception — TBD with the tax tier.)

### Base project names (one per domain — proposed defaults, confirm/adjust)
Each is buildable infrastructure that raises its domain's `cap`:

| Domain | Base project | Alt |
|---|---|---|
| harbor | **Docks** | Quays |
| trade | **Agora** | Deigma (the Piraeus showroom/exchange) |
| guilds | **Workshop** | Ergasterion |
| military | **Barracks** | Stratopedon |
| temples | **Temenos** | Sanctuary |
| academy | **Lyceum** | Stoa |
| aristocracy | **Estate** | Megaron |
| professions | **Gymnasion** | Stoa (colonnade of practitioners' shops/offices) |

`professions` is a grab-bag (physicians, performers, athletes, scribes) — `Gymnasion`/`Stoa` is the loosest fit, open to a rename.

### Data migration
- **`data/projects.json` is dropped and replaced** by the ~8 base project types. No current entry is preserved (bespoke effects are gone; rebuild specials later).

### Future scaling lever
- **`count` is carried in the data model** to future-proof "each new one is harder to build." When we want it, the difficulty can hook onto any one of: more work units, a higher DC, or higher gold/cycle — as `count` rises. **Not decided now.**

---

## Changes vs. projects_spec v4

| v4 | This proposal |
|---|---|
| 45 unique named projects, hand-authored effects | ~8 base project types (one/domain), uniform +2 cap, counted |
| `build_time` (fallback cycles) + `faction_build_actions` (separate) | single **4 work units** |
| `build_cost` paid upfront from treasury | removed → Mayor pays **50 gold + 1 AP per cycle eliminated** |
| Accelerate: 50 gold = −1 cycle, once/cycle | that *is* the Mayor build mechanic now, repeatable per AP |
| Faction build gated to own domain | **kept** |
| `faction_level` + bespoke effects | dropped (rebuild later) |
| `tax_collection` | kept |
| Cap is a fixed authored budget | cap = `fill × 1.20` at start, **grown only by projects** |
| Effects reference `floor` / `entrench` | gone (redesign removed both) |

---

## Open questions (deferred)

1. **DC tuning / count scaling.** DC stays 12 for now. Whether "each new one is harder" attaches to work units, DC, or gold/cycle as `count` rises is deferred until we feel-test the base loop.

*(Resolved 2026-06-05 — see Decided: faction initiation no-gate/no-cost; start at zero base projects; base-project names; `data/projects.json` dropped & replaced.)*

---

## Touches (when promoted to spec/build)
- `Planning/specs/projects_spec.md` → v5 rewrite
- `Planning/reference/formulas.md` + `data-models.md` (cap = `fill × CAP_HEADROOM`; Project gains `count`, loses `build_cost`/`build_time`/`faction_build_actions` in favor of work units)
- `engine/projects/processing.py`, `engine/actions/faction.py` (BuildProject/Sabotage), Mayor build action, `engine/formulas.py` (cap), `data/projects.json`, serializer/loaders, treasury (tax tiers stay)
