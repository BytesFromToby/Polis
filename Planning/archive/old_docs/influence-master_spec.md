# Influence Master — Implementation Spec

_Created: 2026-04-11_

---

## Overview

Add LARP support to the city sim. Cities can run in **GM mode** (existing behavior) or **LARP mode** (phased cycle controlled by an Influence Master). The IM role mirrors the GM interface for now. Player-facing features are stubbed for future implementation.

---

## 1. City Ownership & Roles

### City model changes

Add these fields to the `cities` table:

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `mode` | String | `"gm"` | `"gm"` or `"larp"` |
| `owner_id` | FK → users | required | The user who created the city |

Add a new junction table `city_members`:

| Field | Type | Notes |
|-------|------|-------|
| `id` | String (PK) | UUID |
| `city_id` | FK → cities | |
| `user_id` | FK → users | |
| `role` | String | `"gm"`, `"im"`, or `"player"` |
| `created_at` | DateTime | |

- Owner is always implicitly a master (GM or IM depending on city mode) but is also stored in `city_members` for query simplicity.
- A city can have multiple masters (GMs or IMs). For now the UI only supports one, but the data model allows many.
- A city can have multiple players. No player UI yet — the list exists for future assignment.

### Login & role selection

No change to the auth flow itself. After login:

1. User lands on the home/city-selection screen.
2. Cities display their `mode` tag (GM or LARP).
3. The user's role is determined by their `city_members.role` for each city — not a global account setting.
4. The interface is identical for GM and IM for now. The role distinction exists in the data so we can diverge later.

### Who can do what (access rules)

| Action | Owner | Master (GM/IM) | Player |
|--------|-------|----------------|--------|
| Edit city settings | Yes | Yes | No |
| Run/advance cycle | Yes | Yes | No |
| View all results | Yes | Yes | No |
| Submit player actions | No | No | Yes (future) |
| View own results | No | No | Yes (future) |
| Add/remove members | Yes | No | No |

---

## 2. LARP Cycle Phases

In LARP mode, the cycle is not instant. It moves through **phases** controlled by the IM.

### Phase flow

```
[1] ACTION_SUBMISSION
        |
    IM advances (manual or timer)
        v
[2] ACTION_REVIEW
        |
    IM approves/rejects actions
        v
[3] CYCLE_READY
        |
    IM triggers cycle
        v
[4] PROCESSING  (engine runs)
        |
        v
[5] RESULTS_REVIEW
        |
    IM reviews, then pushes
        v
[6] RESULTS_PUBLISHED
        |
    Players can view results
        |
    IM starts new cycle
        v
[1] ACTION_SUBMISSION  (next cycle)
```

### Phase definitions

| Phase | Value | What happens |
|-------|-------|-------------|
| Action Submission | `action_submission` | Players submit actions. IM waits. (Stubbed — no player UI yet.) |
| Action Review | `action_review` | IM sees submitted actions. Approve, reject, or edit. (Stubbed — shows empty queue for now.) |
| Cycle Ready | `cycle_ready` | All actions reviewed. IM can trigger the cycle engine. |
| Processing | `processing` | Engine is running. Brief — transitions automatically to results_review. |
| Results Review | `results_review` | IM reviews cycle output before players see it. Same as current post-cycle view. |
| Results Published | `results_published` | Results are visible. Players can read their outcomes. (Player view stubbed.) |

### Phase storage

Add to `sim_runs` table:

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `larp_phase` | String (nullable) | `null` | Only set for LARP-mode runs. One of the phase values above. |
| `phase_advanced_at` | DateTime (nullable) | `null` | When the current phase started. Used for timer logic. |
| `phase_timer` | String (nullable) | `null` | `"weekly"`, `"biweekly"`, `"monthly"`, or `null` (manual only). Future — not implemented in alpha. |

### GM mode behavior

When `city.mode == "gm"`, `larp_phase` stays `null`. The cycle works exactly as it does today — click step, cycle runs, results appear. No phase gates.

---

## 3. Player Actions (Stubbed)

### Table: `player_actions`

| Field | Type | Notes |
|-------|------|-------|
| `action_id` | String (PK) | UUID |
| `run_id` | FK → sim_runs | Which run this belongs to |
| `cycle_number` | Integer | The cycle this action targets |
| `user_id` | FK → users | The submitting player |
| `unit_id` | String | The unit performing the action (engine unit ID) |
| `action_type` | String | Engine action type (Harm, Block, Support, Grow, etc.) or `"larp"` for narrative actions |
| `target_id` | String (nullable) | Target unit/faction/domain ID |
| `description` | Text | Free-text intent for LARP actions, or notes for cycle actions |
| `status` | String | `"submitted"`, `"approved"`, `"rejected"`, `"executed"` |
| `im_notes` | Text | IM's notes on this action (approval reason, tweaks, etc.) |
| `created_at` | DateTime | |
| `updated_at` | DateTime | |

### API stubs (no frontend yet)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/runs/{run_id}/actions` | Player submits an action |
| GET | `/runs/{run_id}/actions` | List actions for a cycle (IM sees all, player sees own) |
| PATCH | `/runs/{run_id}/actions/{action_id}` | IM approves/rejects/edits |

These endpoints return valid responses but the frontend doesn't call them yet. They exist so the phase flow is complete end-to-end.

---

## 4. IM Cycle Controls (UI)

### New UI elements for LARP-mode runs

The dashboard gets a **phase indicator** and **phase controls** when the city is in LARP mode:

**Phase indicator:**
- Shows current phase name prominently (e.g., "Action Submission", "Results Review")
- Visual step progress (6 dots/steps showing where we are)

**Phase controls (IM only):**

| Phase | Button(s) |
|-------|-----------|
| `action_submission` | "Advance to Review" |
| `action_review` | "Actions Reviewed — Ready to Run" (disabled until future action review UI exists; auto-skips for now) |
| `cycle_ready` | "Run Cycle" (same as current step button) |
| `results_review` | "Push Results to Players" |
| `results_published` | "Start New Cycle" |

### GM-mode dashboard

No changes. Existing cycle controls remain as-is.

---

## 5. Results Visibility

### Current behavior (GM mode)
All cycle results are visible immediately after the cycle runs. No gating.

### LARP mode behavior
- During `results_review`: only the IM can see cycle results.
- After `results_published`: results are visible to all members.
- Future: per-player visibility filtering (some results shown to specific players only). Not implemented now — publish is all-or-nothing.

### Implementation

Add to `narrative_log` table:

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `published` | Boolean | `true` | In LARP mode, set to `false` when created. IM sets to `true` on publish. GM mode always `true`. |

API log endpoints check this flag when the requesting user is a player. Masters always see everything.

---

## 6. Database Migration Plan

New/changed tables:

1. **`cities`** — add `mode` (String, default `"gm"`), `owner_id` (FK → users, nullable for existing rows)
2. **`city_members`** — new junction table
3. **`sim_runs`** — add `larp_phase`, `phase_advanced_at`, `phase_timer`
4. **`player_actions`** — new table (stubbed)
5. **`narrative_log`** — add `published` (Boolean, default `true`)

Existing data: all current cities get `mode="gm"`, `owner_id` set to the user who created the first sim_run for that city (or null if no runs). All existing narrative logs get `published=true`.

---

## 7. API Changes Summary

### New endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/runs/{run_id}/phase/advance` | IM advances to next phase |
| GET | `/runs/{run_id}/phase` | Get current phase info |
| POST | `/runs/{run_id}/actions` | Stub: player submits action |
| GET | `/runs/{run_id}/actions` | Stub: list actions |
| PATCH | `/runs/{run_id}/actions/{action_id}` | Stub: IM reviews action |
| POST | `/cities/{city_id}/members` | Add a member (player/master) |
| GET | `/cities/{city_id}/members` | List members |
| DELETE | `/cities/{city_id}/members/{user_id}` | Remove a member |

### Modified endpoints

| Endpoint | Change |
|----------|--------|
| POST `/cities` (create) | Accept `mode` field, set `owner_id` to current user |
| GET `/cities` | Return `mode` and `owner_id` in response |
| POST `/sim/start` | If LARP mode, initialize `larp_phase = "action_submission"` |
| POST `/sim/step` | In LARP mode, only allowed during `cycle_ready` phase. Auto-transitions to `results_review` after. |
| GET `/logs` | Filter by `published` flag based on requester role |

---

## 8. Implementation Order

| Step | What | Depends on |
|------|------|-----------|
| 1 | DB migration — new fields and tables | Nothing |
| 2 | City model + API — mode, owner, members | Step 1 |
| 3 | Phase state + advance API | Step 1 |
| 4 | Player actions table + stub API | Step 1 |
| 5 | Frontend — city mode tag on home screen | Step 2 |
| 6 | Frontend — phase indicator + controls on dashboard | Step 3 |
| 7 | Narrative log `published` flag + API filtering | Step 1 |

---

## 9. Out of Scope (for now)

- Player login and player-facing UI
- Per-player result visibility (publish is all-or-nothing)
- Phase auto-advance timer (weekly/biweekly/monthly)
- Multiple masters managing the same city simultaneously
- Player action review UI (phase auto-skips)
- LARP action type (narrative intent actions adjudicated by IM)
