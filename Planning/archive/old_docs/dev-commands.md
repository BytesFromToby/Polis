# Dev Commands — City Sim

## Start the server

```powershell
cd H:\workspace2.0\city_sim_Project\scr
py -m uvicorn api.server:app --reload
```

Open browser at: **http://localhost:8000**

---

## Stop the server

`Ctrl + C` in the terminal running uvicorn.

---

## Restart the server

`Ctrl + C` to stop, then run the start command again.

---

## Rebuild the frontend

Run this after making changes to any `.vue` or `.js` files in `/frontend`:

```powershell
cd H:\workspace2.0\city_sim_Project\frontend
npm run build
```

Then restart the server to serve the new build.

---

## Dev mode (live frontend reload)

Run both at the same time in separate terminals:

**Terminal 1 — backend:**
```powershell
cd H:\workspace2.0\city_sim_Project\scr
py -m uvicorn api.server:app --reload
```

**Terminal 2 — frontend:**
```powershell
cd H:\workspace2.0\city_sim_Project\frontend
npm run dev
```

Open browser at: **http://localhost:5173**

---

## Run tests

```powershell
cd H:\workspace2.0\city_sim_Project\scr
py -m pytest tests/ -q
```
