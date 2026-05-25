"""
api/server.py — FastAPI application entry point.

Run with:
    uvicorn api.server:app --reload
from the /scr directory.

The built frontend (frontend/dist/) is served at / in production.
During development run the Vite dev server separately (npm run dev in /frontend).
"""
from __future__ import annotations
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from db.session import get_db, init_db
from db.seed import seed_official_cities

from api.routes.auth import router as auth_router
from api.routes.users import router as users_router
from api.routes.cities import router as cities_router
from api.routes.city import router as city_router
from api.routes.sim import router as sim_router
from api.routes.state import router as state_router
from api.routes.mayor import router as mayor_router
from api.routes.llm_profiles import router as llm_profiles_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    db = next(get_db())
    try:
        seeded = seed_official_cities(db)
        if seeded:
            print(f"[server] Seeded {seeded} official city template(s).")
    finally:
        db.close()
    yield
    # Shutdown (nothing to clean up)


app = FastAPI(
    title="City Sim API",
    version="0.1.0",
    description="FastAPI backend for the City Sim engine.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten before production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(cities_router)
app.include_router(city_router)
app.include_router(sim_router)
app.include_router(state_router)
app.include_router(mayor_router)
app.include_router(llm_profiles_router)


@app.get("/health")
def health():
    return {"status": "ok"}


# Serve built frontend at / — must come after all API routes
_DIST = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.isdir(_DIST):
    _index = os.path.join(_DIST, "index.html")

    # Serve index.html with no-cache so browsers always pick up the latest
    # Vite build after a rebuild. Hash-named assets are safe to cache.
    @app.get("/", include_in_schema=False)
    @app.get("/index.html", include_in_schema=False)
    def serve_index():
        return FileResponse(_index, headers={"Cache-Control": "no-store"})

    # Everything else (assets, favicon, etc.) served normally by StaticFiles.
    # html=True makes it return index.html for unknown paths (Vue hash routing
    # doesn't need this, but keeps direct-URL reloads working).
    app.mount("/", StaticFiles(directory=_DIST, html=True), name="frontend")
