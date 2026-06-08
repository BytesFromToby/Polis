"""200-cycle civic-public-works balance probe. Passive mayor; varies CIVIC_BUILD_WEIGHT.
Run from backend/:  py ../output/inspect/drive_civic_balance.py    (not a test)"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
import random
import engine.npc.behavior as behavior
from engine.models import WorldState, Mayor, Treasury
from engine.cycle import run_cycle
from engine.projects import new_base_stacks
from loaders import load_state_from_json


def run(weight, cycles=200, seed=42):
    behavior.CIVIC_BUILD_WEIGHT = weight
    random.seed(seed)
    world, factions, domains = load_state_from_json("data")
    mayor, treasury = Mayor(), Treasury()
    base_stacks = new_base_stacks(domains)
    rows = []
    for i in range(cycles):
        run_cycle(world, factions, domains, mayor=mayor, treasury=treasury, base_stacks=base_stacks)
        rows.append((world.cycle, treasury.gold, treasury.income_this_cycle,
                     base_stacks["civic"].active_count()))
    print(f"\n=== CIVIC_BUILD_WEIGHT={weight} ===")
    print(f"{'cyc':>4} {'gold':>8} {'inc':>5} {'offices':>7}")
    for r in [rows[9], rows[24], rows[49], rows[99], rows[149], rows[199]]:
        print(f"{r[0]:>4} {r[1]:>8} {r[2]:>5} {r[3]:>7}")
    golds = [r[1] for r in rows]
    print(f"final gold={golds[-1]} min={min(golds)} max={max(golds)} "
          f"final offices={rows[-1][3]} income={rows[-1][2]}")


for w in (12, 3, 1):
    run(w)
