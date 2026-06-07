"""
main.py — Entry point for Polis v3.

Usage:
    python main.py --cycles 50
    python main.py --cycles 100 --seed 42 --verbose
    python main.py --cycles 50 --narrative-only
"""
import argparse
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.models import WorldState, Mayor, Treasury
from engine.cycle import run_cycle
from engine.projects import new_base_stacks
from engine.logger import SimLogger
from loaders import load_state_from_json


# ── End-of-Run Summary ────────────────────────────────────────────────────────

def print_summary(world: WorldState, factions: dict) -> None:
    print("\n" + "=" * 60)
    print(f"  SIMULATION COMPLETE — {world.cycle} cycles run")
    print("=" * 60)

    print("\n  FACTIONS:")
    for fid, f in factions.items():
        print(f"  [{f.name:<32}] level={f.level} rating={f.rating:.2f} "
              f"hp={f.health:3d} "
              f"leader={f.leader.name} ({f.leader.status})")

    chaos_active = {k: v for k, v in world.chaos.items() if v > 0}
    if chaos_active:
        print(f"  Chaos: {chaos_active}")
    print()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="City Faction Simulation Engine v3"
    )
    parser.add_argument("--cycles", type=int, default=50)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--data-dir", type=str, default="data")
    parser.add_argument("--log-dir", type=str, default="logs")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--verbose-system", action="store_true")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    os.makedirs(args.log_dir, exist_ok=True)

    try:
        world, factions, domains = load_state_from_json(args.data_dir)
    except FileNotFoundError as e:
        print(f"ERROR: Could not load required data file: {e}")
        print(f"domains.json and world_state.json must exist in '{args.data_dir}/'")
        sys.exit(1)

    mayor = Mayor()
    treasury = Treasury()
    base_stacks = new_base_stacks(domains)

    print("Polis v3")
    print(f"  Cycles:   {args.cycles}")
    print(f"  Factions: {len(factions)}")
    print(f"  Domains:  {len(domains)}")
    print(f"  Treasury: {treasury.gold} gold")
    if args.seed is not None:
        print(f"  Seed:     {args.seed}")
    print()

    logger = SimLogger(
        narrative_path=os.path.join(args.log_dir, "narrative.log"),
        system_path=os.path.join(args.log_dir, "system.log"),
        print_narrative=args.verbose,
        print_system=args.verbose_system,
    )

    for i in range(args.cycles):
        cycle_num = world.cycle
        logger.log_cycle_start(cycle_num, world)

        result = run_cycle(world, factions, domains, mayor=mayor, treasury=treasury,
                           base_stacks=base_stacks, logger=logger)

        for event in result.events:
            logger.log_cycle_event(event)

        print(".", end="", flush=True)
        if (i + 1) % 10 == 0:
            print(f" [{i + 1}/{args.cycles}]", flush=True)

    print()
    logger.close()
    print_summary(world, factions)
    print(f"  Narrative log: {os.path.join(args.log_dir, 'narrative.log')}")
    print(f"  System log:    {os.path.join(args.log_dir, 'system.log')}")
    print()


if __name__ == "__main__":
    main()
