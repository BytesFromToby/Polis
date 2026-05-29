# Decisions: Demo UI Restructure + Audience Confirmation/Debug
Specs: Planning/specs/game-ui_spec.md, Planning/specs/audience_spec.md
Date: 2026-05-28

- **Split into two specs, not one** — the screen layout is pure frontend over existing
  endpoints (`game-ui_spec.md`); the audience changes span backend behaviour + UI and
  belong to the existing feature (`audience_spec.md`). Keeping them separate keeps each
  spec coherent for the builder rather than one mixed UI/engine spec.

- **"Last Action" is derived client-side, not a new field** — `Faction` has no persisted
  last-action. The frontend already loads the event log; it reads the most recent
  `CycleEvent` where the faction is actor. Rejected adding an engine/DB field for what the
  log already records.

- **Domain fullness uses existing `Domain.cap` / `utilization`** — no new data. Fill bar
  is `utilization / cap`. Factions with an unknown domain fall under an "Other" group
  rather than being dropped.

- **Domain groups collapsed by default** — 41 factions across 8 domains would overwhelm an
  always-expanded left column. Click-to-expand per the user's request; inferred the
  default-collapsed state and a faction count/fill on the header as the at-a-glance cue.

- **Mayor confirmation: conclude stops committing; a finalize step seals the deal** —
  previously `conclude_audience_step` auto-created the deal the instant the LLM said
  `accepted`. To give the Mayor the final say, conclude now parses without committing on
  faction-accept and defers to a new finalize call (`mayor_accepts`). Faction-decline
  finalises inside conclude (nothing to confirm) to avoid forcing a pointless extra call.
  Considered making conclude always defer (uniform) but the decline path has no decision
  to make, so the asymmetry buys simpler client flow.

- **Memory note + cooldown move to finalise time** — so the faction's memory can record the
  Mayor's actual decision (sealed vs declined-after-agreement), not just the LLM's verdict.
  AP is still spent up front at Step 1; confirming/declining costs no extra AP.

- **Deal status is a client-computed phase label, not LLM-emitted interim terms** — chosen
  over having the LLM emit structured terms after every speech. Avoids changing the
  step-1/step-3 output contract and the extra parsing/failure surface, which buys little
  for a demo. (User decision.)

- **Debug payload always returned, controls always visible** — the audience is the
  marquee demo feature, so exposing the real prompt/response is a selling point, not a
  hidden dev mode. Collapsed-by-default keeps it unobtrusive. (User decision.) Rejected
  gating behind an env/debug flag.

- **Theming/visual restyle deliberately out of scope** — this round is layout + audience
  flow only. A Greek thematic pass is noted as a separate later effort.
