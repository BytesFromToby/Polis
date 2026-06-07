"""
Inspector evidence — Projects v6 stacked panel (game-ui_spec Projects Panel).
Seeds a base-project stack via the API (banks AP across cycles, then funds builds) so the
panel shows a pooled `Name xN` row plus an in-flux front, then screenshots the real UI.
"""
import base64, json, time, urllib.request, urllib.error
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8000"
OUT = Path(__file__).parent
SHOT = "spec_projects_final"


def api(method, path, token=None, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "detail": e.read().decode()}


def seed():
    tok = api("POST", "/auth/guest")["access_token"]
    uid = json.loads(base64.urlsafe_b64decode(tok.split(".")[1] + "=="))["sub"]
    cities = api("GET", "/cities", tok)
    official = next((c for c in cities if c.get("is_official")), cities[0])
    api("POST", f"/users/{uid}/city/load", tok, {"city_id": official["city_id"]})
    api("POST", f"/users/{uid}/sim/start", tok,
        {"llm_profile_id": None, "player_name": "Kallisto", "player_title": "Prytanis"})

    dom = list(api("GET", f"/users/{uid}/state", tok)["domains"].keys())[0]
    # 9 builds → complete two instances (pool x2) + break ground a third (building front).
    builds = 0
    for _ in range(60):
        if builds >= 9:
            break
        r = api("POST", f"/users/{uid}/mayor/act", tok, {"action": "BuildProject", "target_id": dom})
        if r and not r.get("_error"):
            builds += 1
        else:
            api("POST", f"/users/{uid}/sim/step", tok)   # bank an action point
    stacks = api("GET", f"/users/{uid}/projects", tok)
    print("seeded:", [(s["name"], s["domain"], s["count"], s["completed"], s["progress"]) for s in stacks if s["count"] > 0])
    return uid, tok


def main():
    uid, tok = seed()
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1366, "height": 900})
        ctx.add_init_script(
            f"localStorage.setItem('token','{tok}');"
            f"localStorage.setItem('userId','{uid}');"
            f"localStorage.setItem('username','guest');"
        )
        pg = ctx.new_page()
        pg.goto(BASE + "/#/game", wait_until="networkidle")
        pg.wait_for_timeout(2500)
        pg.screenshot(path=str(OUT / f"{SHOT}_01_panel.png"))

        # Open the seeded stack's details modal (first project row in the right panel)
        rows = pg.locator(".panel-right .project-row")
        if rows.count():
            rows.first.click()
            pg.wait_for_timeout(600)
            pg.screenshot(path=str(OUT / f"{SHOT}_02_details.png"))
        b.close()
    print("screenshots written to", OUT)


if __name__ == "__main__":
    main()
