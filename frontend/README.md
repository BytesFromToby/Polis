# City_Sim — Frontend

Vue 3 (Options API) + Vite browser UI for the City_Sim engine. It provides the
game-master interface: create a city, configure factions, run simulation cycles,
view events and faction standings, and conduct mayor actions and LLM negotiation
audiences.

The backend (FastAPI) serves the built output from `dist/` at the app root, so for
normal use you only need to build once and run the backend server.

## Develop

```bash
npm install
npm run dev      # hot-reloading dev server (expects the API on :8000)
```

## Build

```bash
npm run build    # outputs to dist/ — restart the backend server to pick it up
```

See the [root README](../README.md) for full setup and how the frontend fits into
the overall system.
