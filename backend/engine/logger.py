"""
logger.py — Narrative log + system log for Polis v3.

narrative.log — Dramatic events only, human readable (dramatic > 0).
system.log    — Every cycle event in detail.
"""
from __future__ import annotations
import os
import sys
from typing import Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .models import ActionResult, CycleEvent, Faction, WorldState


class SimLogger:
    def __init__(
        self,
        narrative_path: str = "logs/narrative.log",
        system_path: str = "logs/system.log",
        print_narrative: bool = False,
        print_system: bool = False,
    ):
        self.print_narrative = print_narrative
        self.print_system = print_system

        os.makedirs(os.path.dirname(os.path.abspath(narrative_path)), exist_ok=True)
        os.makedirs(os.path.dirname(os.path.abspath(system_path)), exist_ok=True)

        self._narrative_file = open(narrative_path, "w", encoding="utf-8")
        self._system_file = open(system_path, "w", encoding="utf-8")
        self._write_header()

    def _write_header(self) -> None:
        sep = "=" * 72
        self._narrative_file.write(f"{sep}\nPOLIS v3 — NARRATIVE LOG\n{sep}\n\n")
        self._narrative_file.flush()
        self._system_file.write(f"{sep}\nPOLIS v3 — SYSTEM LOG\n{sep}\n\n")
        self._system_file.flush()

    def log_cycle_event(self, event: "CycleEvent") -> None:
        target_str = event.target_id or "-"
        domain_str = event.domain or "-"
        line = (
            f"[C{event.cycle:>3}][{event.action:<16}][{event.actor_id:<24}] "
            f"tgt={target_str:<24} dom={domain_str:<20} "
            f"drm={event.dramatic} | {event.narrative}\n"
        )
        self._system_file.write(line)
        self._system_file.flush()
        if self.print_system:
            print(line, end="")

        if event.dramatic > 0 and event.narrative:
            dline = f"[Cycle {event.cycle:>3}][{'★' * event.dramatic}] {event.narrative}\n"
            self._narrative_file.write(dline)
            self._narrative_file.flush()
            if self.print_narrative:
                safe = dline.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8")
                print(safe, end="")

    def log_dramatic(self, cycle: int, message: str) -> None:
        line = f"[Cycle {cycle:>3}] {message}\n"
        self._narrative_file.write(line)
        self._narrative_file.flush()
        if self.print_narrative:
            safe = line.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8")
            print(safe, end="")

    def log_system(self, cycle: int, category: str, entity_id: str, message: str) -> None:
        line = f"[C{cycle:>3}][{category:<8}][{entity_id:<22}] {message}\n"
        self._system_file.write(line)
        self._system_file.flush()
        if self.print_system:
            print(line, end="")

    def log_cycle_start(self, cycle: int, world_state: "WorldState") -> None:
        sep = "─" * 60
        chaos_active = {k: v for k, v in world_state.chaos.items() if v > 0}
        chaos_str = f" | chaos={chaos_active}" if chaos_active else ""
        self._system_file.write(f"\n{sep}\n  CYCLE {cycle}{chaos_str}\n{sep}\n")
        self._system_file.flush()
        self._narrative_file.write(f"\n── Cycle {cycle} ──────────────────────────────────────────\n")
        self._narrative_file.flush()

    def close(self) -> None:
        self._narrative_file.write("\n[END OF LOG]\n")
        self._system_file.write("\n[END OF LOG]\n")
        self._narrative_file.close()
        self._system_file.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
