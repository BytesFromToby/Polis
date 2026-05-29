"""
engine/llm/audiences.py — Full 5-step Mayor audience flow.

Step sequence:
  1. LLM opens (system prompt injected, user message = "The Mayor requests an audience.")
  2. Mayor player provides opening offer (passed in as mayor_opening)
  3. LLM responds / counters
  4. Mayor player provides closing offer (passed in as mayor_closing)
  5. LLM concludes — must include <deal> block

On accepted deal: persists Deal to DB, applies mayor terms immediately,
                  sets faction committed fields, writes memory note.
On rejection: writes memory note only.

Cooldown is set by the caller (MayorAction handler), not here.
"""
from __future__ import annotations

import uuid
from typing import Optional, TYPE_CHECKING

from engine.llm.client import LLMClient, LLMConfig, LLMError
from engine.llm.prompt_builder import PromptBuilder
from engine.llm.response_parser import ResponseParser
from engine.llm.memory import MemoryWriter

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from engine.models import Faction, Mayor

_OPENING_USER_MSG = "The Mayor requests an audience."

_PROMPT_BUILDER = PromptBuilder()
_RESPONSE_PARSER = ResponseParser()
_MEMORY_WRITER = MemoryWriter()


class AudienceError(Exception):
    """Raised when the audience flow cannot complete (LLM or config failure)."""


class AudienceResult:
    def __init__(
        self,
        step1_narrative: str,
        step3_narrative: str,
        step5_narrative: str,
        accepted: bool,
        deal_id: Optional[str],
        memory_note: str,
        parse_error: str = "",
        finalized: bool = True,
        mayor_terms: Optional[list] = None,
        faction_terms: Optional[list] = None,
    ):
        self.step1_narrative = step1_narrative
        self.step3_narrative = step3_narrative
        self.step5_narrative = step5_narrative
        self.accepted = accepted
        self.deal_id = deal_id
        self.memory_note = memory_note
        self.parse_error = parse_error
        # v3: finalized is False after a faction-accept conclude, until the Mayor confirms.
        self.finalized = finalized
        # v3: proposed terms surfaced so the Mayor can review before confirming.
        self.mayor_terms = mayor_terms if mayor_terms is not None else []
        self.faction_terms = faction_terms if faction_terms is not None else []


def begin_audience_step(
    *,
    faction: "Faction",
    mayor: "Mayor",
    run_id: str,
    cycle: int,
    db: "Session",
    factions: dict,
    domains: dict,
    city_description: str = "",
    city_setting: str = "",
    city_name: str = "Polis",
    player_name: str = "Kallisto",
    player_title: str = "Prytanis",
    llm_config: Optional[LLMConfig] = None,
) -> dict:
    """Phase 1 — build context + run step 1 (faction opens). Returns opaque state dict."""
    cfg = llm_config or LLMConfig.from_env()
    client = LLMClient(cfg)
    system = _PROMPT_BUILDER.build(
        faction=faction, run_id=run_id, mayor=mayor, db=db,
        factions=factions, domains=domains,
        city_description=city_description, city_setting=city_setting,
        city_name=city_name, player_name=player_name, player_title=player_title,
    )
    messages: list[dict] = [{"role": "user", "content": _OPENING_USER_MSG}]
    messages_sent = list(messages)
    step1_text = _call(client, system, messages)
    messages.append({"role": "assistant", "content": step1_text})
    return {
        "system": system,
        "messages": messages,
        "step1_narrative": step1_text,
        "llm_config": cfg,
        "debug_begin": _debug(system, messages_sent, step1_text),
    }


def reply_audience_step(*, state: dict, mayor_opening: str) -> dict:
    """Phase 2 — mayor's opening offer → faction responds (step 3). Returns updated state."""
    cfg = state["llm_config"]
    client = LLMClient(cfg)
    messages = list(state["messages"]) + [{"role": "user", "content": mayor_opening}]
    messages_sent = list(messages)
    step3_text = _call(client, state["system"], messages)
    messages.append({"role": "assistant", "content": step3_text})
    return {
        **state, "messages": messages, "step3_narrative": step3_text,
        "mayor_opening": mayor_opening,
        "debug_reply": _debug(state["system"], messages_sent, step3_text),
    }


def conclude_audience_step(
    *,
    state: dict,
    mayor_closing: str,
    faction: "Faction",
    mayor: "Mayor",
    run_id: str,
    cycle: int,
    db: "Session",
) -> AudienceResult:
    """
    Phase 3 — mayor's closing offer → faction concludes (step 5).

    v3: no longer commits a deal when the faction accepts. The parsed result is stashed
    on `state` and returned with `finalized=False` so the Mayor can confirm (see
    `finalize_audience`). A faction *decline* is terminal and finalised here.
    """
    cfg = state["llm_config"]
    # Step 5 must fit narrative + full deal JSON; ensure tokens are sufficient
    if cfg.max_tokens < 1200:
        from dataclasses import replace as _replace
        cfg = _replace(cfg, max_tokens=1200)
    client = LLMClient(cfg)
    messages = list(state["messages"]) + [{"role": "user", "content": mayor_closing}]
    step5_text = _call(client, state["system"], messages)

    parsed = _RESPONSE_PARSER.parse(step5_text, faction, mayor)

    # Stash for the finalize step / debug.
    state["pending_parsed"] = parsed
    state["step5_raw"] = step5_text
    state["mayor_closing"] = mayor_closing
    state["debug_conclude"] = _debug(state["system"], messages, step5_text)

    # Faction declined → terminal, finalise now (writes memory note, sets cooldown).
    if not parsed.accepted:
        return finalize_audience(
            state=state, mayor_accepts=False,
            faction=faction, mayor=mayor, run_id=run_id, cycle=cycle, db=db,
        )

    # Faction accepted → defer to Mayor confirmation. No deal, no terms, no memory yet.
    return AudienceResult(
        step1_narrative=state["step1_narrative"],
        step3_narrative=state.get("step3_narrative", ""),
        step5_narrative=parsed.narrative,
        accepted=True,
        deal_id=None,
        memory_note=parsed.memory_note,
        parse_error=parsed.parse_error,
        finalized=False,
        mayor_terms=parsed.mayor_terms,
        faction_terms=parsed.faction_terms,
    )


def finalize_audience(
    *,
    state: dict,
    mayor_accepts: bool,
    faction: "Faction",
    mayor: "Mayor",
    run_id: str,
    cycle: int,
    db: "Session",
) -> AudienceResult:
    """
    Phase 4 (v3) — resolve a concluded audience on the Mayor's decision.

    Reads the parsed result stashed on `state` by `conclude_audience_step`:
    - mayor_accepts and faction accepted → create the deal, apply terms.
    - otherwise → no deal, no terms.
    In every branch writes the memory note and sets the faction cooldown.
    """
    parsed = state["pending_parsed"]
    client = LLMClient(state["llm_config"])

    deal_id = None
    if mayor_accepts and parsed.accepted and parsed.mayor_terms is not None:
        deal_id = _create_deal(parsed, faction, mayor, run_id, cycle, db)
        _apply_mayor_terms(parsed, faction, mayor, cycle)
        _apply_faction_terms(parsed, faction)
        note = parsed.memory_note or "deal reached"
    elif parsed.accepted and not mayor_accepts:
        note = parsed.memory_note or "mayor declined terms"
    else:
        note = parsed.memory_note or "no deal reached"

    _MEMORY_WRITER.write_note(
        run_id=run_id, faction_id=faction.id, cycle=cycle,
        note=note, note_type="audience", db=db, llm_client=client,
    )

    from engine.mayor.actions import MEET_COOLDOWN
    mayor.cooldowns[faction.id] = MEET_COOLDOWN

    return AudienceResult(
        step1_narrative=state.get("step1_narrative", ""),
        step3_narrative=state.get("step3_narrative", ""),
        step5_narrative=parsed.narrative,
        accepted=bool(mayor_accepts and parsed.accepted),
        deal_id=deal_id,
        memory_note=note,
        parse_error=parsed.parse_error,
        finalized=True,
        mayor_terms=parsed.mayor_terms,
        faction_terms=parsed.faction_terms,
    )


def run_audience(
    *,
    faction: "Faction",
    mayor: "Mayor",
    run_id: str,
    cycle: int,
    mayor_opening: str,
    mayor_closing: str,
    db: "Session",
    factions: dict,
    domains: dict,
    city_description: str = "",
    city_setting: str = "",
    city_name: str = "Polis",
    player_name: str = "Kallisto",
    player_title: str = "Prytanis",
    llm_config: Optional[LLMConfig] = None,
) -> AudienceResult:
    """
    Run a full 5-step audience negotiation.

    Parameters
    ----------
    mayor_opening : str
        The Mayor's opening offer / opening remarks (step 2 user turn).
    mayor_closing : str
        The Mayor's closing / final offer (step 4 user turn).
    llm_config : LLMConfig | None
        Falls back to LLMConfig.from_env() if None.
    """
    cfg = llm_config or LLMConfig.from_env()
    client = LLMClient(cfg)

    system = _PROMPT_BUILDER.build(
        faction=faction,
        run_id=run_id,
        mayor=mayor,
        db=db,
        factions=factions,
        domains=domains,
        city_description=city_description,
        city_setting=city_setting,
        city_name=city_name,
        player_name=player_name,
        player_title=player_title,
    )

    messages: list[dict] = []

    # ── Step 1: LLM opens ─────────────────────────────────────────────────────
    messages.append({"role": "user", "content": _OPENING_USER_MSG})
    step1_text = _call(client, system, messages)
    messages.append({"role": "assistant", "content": step1_text})

    # ── Step 3: LLM responds to mayor's opening ───────────────────────────────
    messages.append({"role": "user", "content": mayor_opening})
    step3_text = _call(client, system, messages)
    messages.append({"role": "assistant", "content": step3_text})

    # ── Step 5: LLM concludes with <deal> block ───────────────────────────────
    messages.append({"role": "user", "content": mayor_closing})
    step5_text = _call(client, system, messages)

    parsed = _RESPONSE_PARSER.parse(step5_text, faction, mayor)

    deal_id = None
    if parsed.accepted and parsed.mayor_terms is not None:
        deal_id = _create_deal(parsed, faction, mayor, run_id, cycle, db)
        _apply_mayor_terms(parsed, faction, mayor, cycle)
        _apply_faction_terms(parsed, faction)

    _MEMORY_WRITER.write_note(
        run_id=run_id,
        faction_id=faction.id,
        cycle=cycle,
        note=parsed.memory_note or ("deal reached" if parsed.accepted else "no deal reached"),
        note_type="audience",
        db=db,
        llm_client=client,
    )

    return AudienceResult(
        step1_narrative=step1_text,
        step3_narrative=step3_text,
        step5_narrative=parsed.narrative,
        accepted=parsed.accepted,
        deal_id=deal_id,
        memory_note=parsed.memory_note,
        parse_error=parsed.parse_error,
        finalized=True,
        mayor_terms=parsed.mayor_terms,
        faction_terms=parsed.faction_terms,
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _call(client: LLMClient, system: str, messages: list[dict]) -> str:
    try:
        return client.complete(system, messages)
    except LLMError as exc:
        raise AudienceError(f"LLM call failed: {exc}") from exc


def _debug(system: str, messages: list[dict], raw_response: str) -> dict:
    """Capture the exact request sent to the LLM and the raw response, for inspection.

    Copies are taken so later mutation of the message list does not alter the record.
    """
    return {
        "system": system,
        "messages": [dict(m) for m in messages],
        "raw_response": raw_response,
    }


def _create_deal(parsed, faction: "Faction", mayor: "Mayor", run_id: str, cycle: int, db: "Session") -> str:
    import json
    from db.models import Deal as DBDeal

    duration = _max_duration(parsed.mayor_terms + parsed.faction_terms)

    deal_id = str(uuid.uuid4())
    db.add(DBDeal(
        deal_id=deal_id,
        run_id=run_id,
        faction_id=faction.id,
        cycle_created=cycle,
        total_duration=duration,
        cycles_remaining=duration,
        status="active",
        mayor_terms_json=json.dumps([_term_to_dict(t) for t in parsed.mayor_terms]),
        faction_terms_json=json.dumps([_term_to_dict(t) for t in parsed.faction_terms]),
        rep_cost_if_broken=parsed.rep_cost_if_broken,
        suspension_streak=0,
    ))

    from engine.models import Deal, DealTerm
    engine_deal = Deal(
        id=deal_id,
        faction_id=faction.id,
        mayor_terms=parsed.mayor_terms,
        faction_terms=parsed.faction_terms,
        cycles_remaining=duration,
        total_duration=duration,
        rep_cost_if_broken=parsed.rep_cost_if_broken,
        cycle_created=cycle,
    )
    mayor.deals[deal_id] = engine_deal
    db.flush()
    return deal_id


def _apply_mayor_terms(parsed, faction: "Faction", mayor: "Mayor", cycle: int) -> None:
    for term in parsed.mayor_terms:
        if term.type == "tax_exemption":
            mayor.exemptions[faction.id] = term.duration
        elif term.type == "endorsement":
            mayor.adjust_reputation(faction.id, 10)


def _apply_faction_terms(parsed, faction: "Faction") -> None:
    for term in parsed.faction_terms:
        if term.type == "committed_action":
            faction.committed_action = term.action
            faction.committed_target = term.target_id
        elif term.type == "committed_abstain":
            faction.committed_abstain_action = term.action
            faction.committed_abstain_target = term.target_id


def _max_duration(terms) -> int:
    durations = [t.duration for t in terms if t.duration > 0]
    return max(durations) if durations else 1


def _term_to_dict(term) -> dict:
    return {
        "type": term.type,
        "action": term.action,
        "target_id": term.target_id,
        "duration": term.duration,
    }
