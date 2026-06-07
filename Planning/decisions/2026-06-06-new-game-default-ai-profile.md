# New-game default AI profile stored in localStorage

**Date:** 2026-06-06

## What

Added a "Default for new games" AI-profile preference, surfaced in the AI Settings
modal and applied automatically when starting a new game (both the title-screen
quick-start and the builder's Start Sim modal). Stored per-browser in `localStorage`
(`defaultLlmProfileId`), exposed through `store.defaultLlmProfileId` /
`store.setDefaultLlmProfile`.

## Why localStorage and not a backend per-user setting

- The request was explicitly frontend-scoped, and there is no existing per-user
  settings table/endpoint — a backend default would mean new schema, a route, and
  migration for a single convenience field.
- The preference is non-authoritative: once a game starts, the chosen profile is
  copied to the `SimRun.llm_profile_id` row, which is the real source of truth and
  already persists/restores on resume. The default only seeds new runs, so losing it
  (e.g. on another device) is harmless — it falls back to `None (stub mode)`.

## Robustness note

A stored default can become stale if its profile is deleted from another browser.
Guards: the AI Settings modal clears the default when its profile is deleted locally;
the title-screen quick-start validates the id against the live profile list before
passing it to `/sim/start`, falling back to `None` rather than triggering a 404.

## Not changed

Backend persistence of a run's own AI setting already worked (`_restore_session`
restores `llm_profile_id` from the run row on `/sim/switch`). No backend changes were
needed for "a loaded city keeps its setting."
