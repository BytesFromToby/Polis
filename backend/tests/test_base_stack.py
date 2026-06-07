"""
BaseProjectStack derived-view unit tests (projects_spec v6, Concepts & Data).

Pins the cap-tier / pool / active-count / defense math that the cap-derivation and
maintenance features build on. Pure data layer — no engine wiring.
"""
from engine.models import BaseProjectStack, project_tier


def _stack(**kw):
    base = dict(name="Estate", domains=["aristocracy"])
    base.update(kw)
    return BaseProjectStack(**base)


def test_project_tier_bands():
    assert project_tier(0) == 0
    assert project_tier(20) == 0
    assert project_tier(21) == 1
    assert project_tier(50) == 1
    assert project_tier(51) == 2
    assert project_tier(100) == 2


def test_cap_contribution_empty():
    assert _stack(count=0).cap_contribution() == 0


def test_cap_contribution_all_pristine():
    # N pristine completed instances → N × +2
    assert _stack(count=1, completed=True, progress=100).cap_contribution() == 2
    assert _stack(count=3, completed=True, progress=100).cap_contribution() == 6


def test_cap_contribution_building_top():
    # The building top adds 0; the pristine pool below it still counts.
    assert _stack(count=1, completed=False, progress=50).cap_contribution() == 0
    assert _stack(count=2, completed=False, progress=50).cap_contribution() == 2  # 1 pristine below


def test_cap_contribution_damaged_top():
    # Damaged top in the 21–50 band → +1; in 1–20 → +0; pristine pool below still +2 each.
    assert _stack(count=1, completed=True, progress=30).cap_contribution() == 1
    assert _stack(count=2, completed=True, progress=30).cap_contribution() == 3   # 2 + 1
    assert _stack(count=2, completed=True, progress=10).cap_contribution() == 2   # 2 + 0


def test_pool_count():
    assert _stack(count=3, completed=True, progress=100).pool_count() == 3   # top pristine → in pool
    assert _stack(count=3, completed=False, progress=50).pool_count() == 2   # building top broken out
    assert _stack(count=3, completed=True, progress=40).pool_count() == 2    # damaged top broken out
    assert _stack(count=0).pool_count() == 0


def test_active_count():
    assert _stack(count=3, completed=True, progress=100).active_count() == 3
    assert _stack(count=3, completed=False, progress=50).active_count() == 2  # building not active
    assert _stack(count=3, completed=True, progress=40).active_count() == 3   # damaged still active
    assert _stack(count=0).active_count() == 0


def test_defense_rating():
    assert _stack(count=1, completed=False, progress=0).defense_rating() == 1   # floor
    assert _stack(count=1, completed=True, progress=100).defense_rating() == 5


def test_top_state_predicates():
    pristine = _stack(count=2, completed=True, progress=100)
    assert pristine.top_is_pristine() and not pristine.top_is_building() and not pristine.top_is_damaged()
    building = _stack(count=2, completed=False, progress=25)
    assert building.top_is_building() and not building.top_is_pristine() and not building.top_is_damaged()
    damaged = _stack(count=2, completed=True, progress=40)
    assert damaged.top_is_damaged() and not damaged.top_is_pristine() and not damaged.top_is_building()
