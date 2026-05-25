# Decision: Vue.js Frontend

**Date:** 2026-04-04
**Status:** Accepted

## Context

The API is complete. The GM interface needs a browser frontend to make the
sim usable for an actual game master. The UI spec is already written.

## Decision

Vue.js (Options API) served via Vite. Lives in `city_sim_Project/frontend/`.

- Dev: Vite dev server on port 5173, FastAPI on port 8000. CORS already open.
- Local "prod": `npm run build` outputs to `frontend/dist/`. FastAPI serves it as static files.

## Rationale

- Vue Options API matches the existing spec decision
- Vite is fast, minimal config, good Vue 3 support
- Keeping frontend separate from /scr keeps Python and JS concerns cleanly split
- FastAPI static file serving means one server in production (no separate hosting)

## Consequences

- Node/npm required for frontend development
- Build step required before FastAPI can serve the frontend as static files
- During dev, both servers must run simultaneously
