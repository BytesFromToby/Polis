"""
Inspector evidence capture — Game UI Projects Panel (domain-grouped).
Drives the real Vue UI at http://localhost:8000 and seeds deterministic project
data through the API (the guest user is a singleton, so the API and browser share
the same in-memory sim session). Saves screenshots under output/inspect/.
"""
import json
import time
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8000"
OUT = Path(__file__).parent
SHOT = "spec_game-ui-projects-domain-grouping_final"


def api(method, path, token=None, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read().decode()
        return json.loads(raw) if raw else None


def seed():
    """Guest login, load official city, start sim, bank AP, then build projects:
    one domain funded to completion (active) and one broken-ground (under construction)."""
    tok = api("POST", "/auth/guest")["access_token"]
    import base64
    payload = json.loads(base64.urlsafe_b64decode(tok.split(".")[1] + "=="))
    uid = payload["sub"]

    cities = api("GET", "/cities", tok)
    official = next((c for c in cities if c.get("is_official")), cities[0])
    api("POST", f"/users/{uid}/city/load", tok, {"city_id": official["city_id"]})
    api("POST", f"/users/{uid}/sim/start", tok,
        {"llm_profile_id": None, "player_name": "Kallisto", "player_title": "Prytanis"})

    # Bank action points (start at 1, +1/cycle, cap 6) by stepping cycles.
    for _ in range(6):
        api("POST", f"/users/{uid}/sim/step", tok)

    domains = list(api("GET", f"/users/{uid}/state", tok)["domains"].keys())
    dom_complete, dom_building = domains[0], domains[1]

    # Fund dom_complete 4x -> active project; dom_building 1x -> under construction.
    built = []
    for _ in range(4):
        try:
            api("POST", f"/users/{uid}/mayor/act", tok,
                {"action": "BuildProject", "target_id": dom_complete})
            built.append(dom_complete)
        except Exception as e:
            print("build complete step skipped:", e)
    try:
        api("POST", f"/users/{uid}/mayor/act", tok,
            {"action": "BuildProject", "target_id": dom_building})
        built.append(dom_building)
    except Exception as e:
        print("build building step skipped:", e)

    projs = api("GET", f"/users/{uid}/projects", tok)
    print("seeded projects:", [(p["name"], p["domain"], p["status"], p["build_progress"]) for p in projs])
    return uid, tok


def main():
    uid, tok = seed()
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1366, "height": 900})
        # Seed auth into localStorage before the app boots, then land directly on /game
        # (clicking "New Game" would call sim.start again and wipe the seeded projects).
        ctx.add_init_script(
            f"localStorage.setItem('token', '{tok}');"
            f"localStorage.setItem('userId', '{uid}');"
            f"localStorage.setItem('username', 'guest');"
        )
        pg = ctx.new_page()
        pg.goto(BASE + "/#/game", wait_until="networkidle")
        pg.wait_for_timeout(2500)

        # 1 + 4 + 5: full panel, all domain headers (expanded by default), populated groups
        pg.screenshot(path=str(OUT / f"{SHOT}_01_panel_default.png"))

        # 2: collapse a domain group by clicking its header (right panel), then screenshot
        right = pg.locator(".panel-right .domain-header").first
        right.click()
        pg.wait_for_timeout(400)
        pg.screenshot(path=str(OUT / f"{SHOT}_02_group_collapsed.png"))
        right.click()  # re-expand
        pg.wait_for_timeout(400)

        # 6: click a project row -> details modal
        pg.locator(".panel-right .project-row").first.click()
        pg.wait_for_timeout(600)
        pg.screenshot(path=str(OUT / f"{SHOT}_03_details_modal.png"))

        # 6: advance a cycle with the modal open -> stays in sync.
        # The full-screen modal overlay blocks the top-bar button, so force the click
        # to exercise runCycle() -> refresh() -> selectedProject re-sync with the modal open.
        pg.get_by_role("button", name="Run Cycle").click(force=True)
        pg.wait_for_timeout(3000)
        pg.screenshot(path=str(OUT / f"{SHOT}_04_modal_after_cycle.png"))

        b.close()
    print("screenshots written to", OUT)


if __name__ == "__main__":
    main()
