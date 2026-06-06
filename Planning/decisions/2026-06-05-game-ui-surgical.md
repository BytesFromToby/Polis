# Decisions: Game UI — Surgical Correctness Pass
Spec: Planning/specs/game-ui_spec.md
Date: 2026-06-05

Aligns the existing play UI with the faction redesign + the projects-rework and
mayor-actions-rework, without a redesign.

- **Surgical, not a redesign** — the goal is a *correct, demo-able* UI fast. The backend just went through two reworks; making the existing layout truthful (right levers, right fields) is higher-value now than a play-UI redesign, and the redesign's layout calls are better made after seeing the corrected UI run. Redesign explicitly deferred.
- **Mayor Actions modal = the 8-lever demo roster** — drop the seven cut actions' rows (Broker, Report, Rumor, Allocate Budget, Withhold, Decree, Appoint, Blind Eye), add Sabotage + Build Project. All dispatch through the existing generic `mayor.act` → `/mayor/act`, so no new API plumbing — just rows.
- **Surface gold in the modal** — Sabotage (50g) and Build Project (50/30g) are the first gold-costing levers in the action menu; the modal previously showed only AP. Sabotage disables at `gold < 50`; Build disables only on AP and lets the backend reject gold shortfalls (its cost is context-dependent: 50 to build, 30 to repair), surfacing the existing error banner. Rejected pre-computing Build affordability client-side as fragile duplication of backend cost logic.
- **Drop deterministic Meet from the UI** — the audience is the sole faction-engagement path (matches the demo philosophy of concentrating faction influence in the LLM channel). `MeetWithFaction` stays in the engine but gets no button; the standalone button mislabelled "Meet with Faction ▸" (which actually opens an audience) is relabelled "Request Audience" to kill the conflation. Rejected surfacing both as redundant and confusing for a demo.
- **Lead faction readouts with integer level** (`int(rating)`, "3" not "3.34") — the integer level is the meaningful rank beat (level-ups are the dramatic event); the raw float is noise for a viewer. The precise `rating` is kept only as a de-emphasized secondary so information isn't lost. Applies to both GameView faction blocks and the DashboardView table.
- **Remove dead `entrench` column + `commission()` call** — both reference mechanics/endpoints retired by the prior reworks (`entrench` field gone from the API; `/projects/commission` retired in the mayor-actions-rework). Build now goes through the BuildProject mayor action.
- **Pending: play-UI redesign** flagged for later (resource header, rank/health bars, project progress, audience-as-hero) — out of scope here.
