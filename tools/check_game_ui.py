"""
check_game_ui.py — pinned source-invariant check for the Game UI surgical-correctness
pass (Planning/specs/game-ui_spec.md). The frontend has no JS test runner, so these
[automated] Done-when items are encoded here and re-run by inspector.

Run from the repo root:  py tools/check_game_ui.py
Exits 0 and prints OK when every invariant holds; exits 1 with the failures otherwise.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "frontend" / "src"
MODAL = SRC / "components" / "MayorActionsModal.vue"
GAMEVIEW = SRC / "views" / "GameView.vue"
DASHBOARD = SRC / "views" / "DashboardView.vue"
API = SRC / "api.js"

REMOVED_ACTIONS = [
    "BrokerADeal", "RequestAReport", "PlantARumor", "AllocateBudget",
    "WithholdResources", "IssueADecree", "AppointAnOfficial", "TurnABlindEye",
]


def _read(p: Path) -> str:
    if not p.exists():
        raise SystemExit(f"FAIL: expected file not found: {p}")
    return p.read_text(encoding="utf-8")


def main() -> int:
    failures = []

    modal = _read(MODAL)
    # 1. Modal carries the two new levers and none of the eight removed actions.
    if "Sabotage" not in modal:
        failures.append("MayorActionsModal: missing Sabotage")
    if "BuildProject" not in modal:
        failures.append("MayorActionsModal: missing BuildProject")
    for a in REMOVED_ACTIONS:
        if a in modal:
            failures.append(f"MayorActionsModal: removed action still present: {a}")
    # 2. Modal declares a gold prop and shows gold in the header.
    if "gold:" not in modal:
        failures.append("MayorActionsModal: no gold prop declared")
    if "{{ gold }}" not in modal:
        failures.append("MayorActionsModal: gold not shown in header")

    gameview = _read(GAMEVIEW)
    # 3. GameView leads with integer level, relabels the audience button, and never
    #    dispatches the deterministic MeetWithFaction action.
    if "Math.floor(f.rating)" not in gameview:
        failures.append("GameView: faction block does not lead with integer level")
    if "Request Audience" not in gameview:
        failures.append("GameView: standalone audience button not relabelled")

    # 4. No UI source dispatches MeetWithFaction (audience is the sole engagement path).
    for vue in SRC.rglob("*.vue"):
        if "MeetWithFaction" in vue.read_text(encoding="utf-8"):
            failures.append(f"{vue.name}: dispatches MeetWithFaction")

    dash = _read(DASHBOARD)
    # 5. Dashboard drops entrench and leads with integer level.
    if "entrench" in dash:
        failures.append("DashboardView: entrench reference still present")
    if "entrenchClass" in dash:
        failures.append("DashboardView: entrenchClass still present")
    if "Math.floor(f.rating)" not in dash:
        failures.append("DashboardView: faction row does not show integer level")

    api = _read(API)
    # 6. The retired commission endpoint is gone from the client.
    if "commission" in api:
        failures.append("api.js: commission still present")
    if "projects/commission" in api:
        failures.append("api.js: /projects/commission reference still present")

    if failures:
        print("FAIL:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
