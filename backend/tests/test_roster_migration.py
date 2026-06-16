"""Roster restructure — save-policy regression (roster-restructure_spec, Feature: Seed, saves &
regression integrity).

The restructure applies to NEW games only. Existing snapshots serialize their own factions and
domains, so they restore graceful-but-stale on their old roster regardless of the current data
files — no migration. Proven with a snapshot carrying a cut faction (silverbench) and a
cut/renamed domain (trade)."""
from engine.models import WorldState, Faction, Domain, Leader
from serializer import serialize_state, deserialize_state


def test_old_roster_snapshot_still_restores():
    # a snapshot from before the restructure: a cut faction in a cut domain
    world = WorldState(cycle=3)
    factions = {
        "silverbench": Faction(id="silverbench", name="The Silverbench",
                               domain_primary="trade", leader=Leader(name="Aristion")),
    }
    domains = {"trade": Domain(id="trade", name="Trade", cap=300)}

    snap = serialize_state(world, factions, domains)
    w, f, d, *_ = deserialize_state(snap)

    # restores without error, on its own (old) roster — the current data files are irrelevant
    assert w.cycle == 3
    assert "silverbench" in f and f["silverbench"].domain_primary == "trade"
    assert "trade" in d and d["trade"].name == "Trade"
