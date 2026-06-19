# Deviations — Pottery UI

Blueprint: Planning/blueprints/pottery-ui_BP.md
Date: 2026-06-17

| Slice | Step | Deviation | Why |
|-------|------|-----------|-----|
| 3 | 2 | **Health** is shown as its value + sickly marker (not a band word). | `serialize_the_public` emits `fed/happy/piety/unrest/consumption/confidence` bands + `sickly`, but **no `health_band`** — so the truthful readout is the value + sickly. Spec Done-when asks for "Health (sickly marker)", which this meets. The mockup's "Robust" was illustrative. |
| 3 | 1 | Mayor title renders "Mayor — the Prytanis" (no player name). | No mayor/player **name** field is in the snapshot (`leaderName` is faction-only); the historical title stands in. A real name can drop in once player-identity surfaces it. |
| 3 | — | Dropped Standing/World left `topReputation`/`repColor`/`chaosDisplay`/`world` computeds unused (harmless). | Removing them is dead-code tidying, not behaviour; left for a later cleanup pass to keep this slice focused. |
| Final | 3 | The **Chronicle** shows a flat newest-first frieze of recent deeds (dramatic beats in oxblood); the **full cycle-grouped log view is deferred** (no dedicated "full log" affordance yet). | The band's job is the highlights; the cycle-grouped component still exists in code but isn't surfaced. A "full log" button is a small follow-up. |
| Final | 1 | `_event_kind` classifies disaster/boon/neutral from the event's effects in the **serializer** (withhold / chaos+ / negative health-support-fed-happy-piety → disaster). | Per the blueprint's "Stuck if" — do the classification server-side where `GameEvent.effects` is available, not in Vue. |

**Backend test:** `tests/test_state_active_events.py` (3) — state serializes `active_events` with
name/cycles_remaining/target_id/kind; empty list omits the key; kind classification. Full backend
suite **556 green** (553 → 556).

**Build:** `npm run build` exit 0 after every slice. Slices: ① token swap + chrome + fonts → ②
command bar + quadrant relayout → ③ Mayor command panel (7 scales surface) → ④ active-events
serializer + Events/Chronicle band. Visual verification is the inspector's playwright pass.
