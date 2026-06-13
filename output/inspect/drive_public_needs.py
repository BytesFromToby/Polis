"""
Inspector evidence capture — Public Needs (the barley run), final sign-off.
Human-required item: "Watching the UI across a shortage: the needs read clearly."

Drives the real Vue UI at http://localhost:8000 with two throwaway users:
  A) healthy city  — The People section shows Fed/Content bands.
  B) shortage city — the three aristocracy estates are deleted in setup
     (the spec's dead-estates scenario), so the city starves on a clear arc:
     fed 60 -> 50 (Fed) -> 40/30 (Hungry) -> 20.. (Starving), bands shifting visibly.

Screenshots -> H:/Polis/docs/InPlayScreenshots/public-needs_2026-06-12_*.png
"""
import base64
import json
import time
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8000"
OUT = Path(__file__).resolve().parents[2] / "docs" / "InPlayScreenshots"
STAMP = "public-needs_2026-06-12"


def api(method, path, token=None, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode()
        return json.loads(raw) if raw else None


def register(name):
    tok = api("POST", "/auth/register", body={
        "username": name, "email": f"{name}@throwaway.local",
        "password": "inspector-pass-1", "description": "inspector throwaway",
    })["access_token"]
    payload = json.loads(base64.urlsafe_b64decode(tok.split(".")[1] + "=="))
    return payload["sub"], tok


def setup_city(uid, tok, starve=False):
    cities = api("GET", "/cities", tok)
    official = next(c for c in cities if c.get("is_official"))
    api("POST", f"/users/{uid}/city/load", tok, {"city_id": official["city_id"]})
    if starve:
        city = api("GET", f"/users/{uid}/city", tok)
        factions = json.loads(city["factions_json"])
        estates = [fid for fid, f in factions.items()
                   if f.get("domain_primary") == "aristocracy"]
        for fid in estates:
            api("DELETE", f"/users/{uid}/city/factions/{fid}", tok)
        print("deleted estates:", estates)
    api("POST", f"/users/{uid}/sim/start", tok,
        {"llm_profile_id": None, "player_name": "Inspector", "player_title": "Episkopos"})


def public_state(uid, tok):
    s = api("GET", f"/users/{uid}/state", tok)
    return s.get("the_public")


def drive(uid, tok, shots):
    """shots: list of (cycles_to_run_first, filename). Screenshot the Game view
    plus an element shot of The People section."""
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1366, "height": 900})
        ctx.add_init_script(
            f"localStorage.setItem('token', '{tok}');"
            f"localStorage.setItem('userId', '{uid}');"
            f"localStorage.setItem('username', 'inspector');"
        )
        pg = ctx.new_page()
        pg.goto(BASE + "/#/game", wait_until="networkidle")
        pg.wait_for_timeout(2500)
        for cycles, fname in shots:
            for _ in range(cycles):
                pg.get_by_role("button", name="Run Cycle").click()
                pg.wait_for_timeout(1800)
            pg.screenshot(path=str(OUT / fname))
            sect = pg.locator(".mayor-section", has_text="The People")
            sect.screenshot(path=str(OUT / fname.replace(".png", "_people.png")))
            print(fname, "->", public_state(uid, tok))
        b.close()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    suffix = str(int(time.time()))[-5:]

    # A) healthy city
    uid, tok = register(f"insp_pn_a_{suffix}")
    setup_city(uid, tok, starve=False)
    drive(uid, tok, [(2, f"{STAMP}_01_healthy.png")])

    # B) shortage arc — dead estates
    uid, tok = register(f"insp_pn_b_{suffix}")
    setup_city(uid, tok, starve=True)
    drive(uid, tok, [
        (0, f"{STAMP}_02_shortage_cycle0.png"),   # fed 60, Fed
        (3, f"{STAMP}_03_shortage_hungry.png"),   # fed ~30-40, Hungry
        (4, f"{STAMP}_04_shortage_starving.png"), # fed <=20, Starving
    ])
    print("screenshots written to", OUT)


if __name__ == "__main__":
    main()
