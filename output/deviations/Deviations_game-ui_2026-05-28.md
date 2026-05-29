# Deviations — Game UI (Demo Layout)
Blueprint: Planning/blueprints/game-ui_BP.md
Date: 2026-05-28

| Slice | Step | Deviation | Why |
|-------|------|-----------|-----|
| 1 | 2 | `lastActionFor` matches on `ev.actor_id` and iterates a cycle's events in reverse. | Confirmed `actor_id` is the log-event actor field (verified against `engine/llm/prompt_builder.py:181`); reverse iteration returns the genuinely most-recent action within a cycle. |
| 1 | 4 | `openAudience(f.id)` stub introduced an `audienceFactionId` data field early (nominally Slice 4). | So the stub assignment is reactive; full modal wiring still done in Slice 4. |
| 2 | 1 | Event Log markup moved into the centre-bottom (`.center-log`) here, during the shell restructure (nominally Slice 3 Step 1). Right column given a "Projects" placeholder. | The vertical centre split forces the log's placement; could not leave centre-bottom empty without dead structure. |
| 2 | 2 | AP/reputation section labelled "Standing", not "Actions". | The Act button moved to the window header bar; avoids two elements both named "Actions". Content unchanged (AP x/cap, top reputation, exemptions). |
| 2 | 4 | Removed the embedded `<AudienceModal>` from `MayorActionsModal` (import, `components`, `audienceFactionId`/`showAudience` data, `audienceFaction` computed, `openAudience`/`onAudienceActed` methods). | The audience launches from GameView now; the embedded mount was dead weight. Bundle dropped 47→45 modules. |
| 3 | 1 | No new work — Event Log relocation already done in Slice 2 Step 1. | Recorded so the blueprint and code agree. |
| 3 | 2 | Added an `otherProjects` computed (`status !== 'under_construction'`). | "Then the rest" must include damaged/critical projects, not just `active` ones. |
| Final | 1 | Standalone audience uses a faction-picker modal (`showAudiencePicker`, `.picker-*`); both entry paths share one `AudienceModal` mount keyed off `audienceFactionId`. | Cleanest way to satisfy "card → pre-targeted" and "standalone → selector" with one modal instance. |
| Final | — | Removed now-dead `entrenchClass` method and `.faction-meta` style left over from the old faction card. | Code rule: no dead code. The old per-card entrench display was dropped in Slice 1. |
