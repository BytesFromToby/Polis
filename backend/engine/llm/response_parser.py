"""
engine/llm/response_parser.py — Extracts and validates <deal> blocks from LLM responses.

Never raises on parse failure — returns deal=None with a reason logged instead.
"""
from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from engine.models import Deal, DealTerm, Mayor, Faction

VALID_TERM_TYPES = {
    "tax_exemption", "endorsement",
    "committed_action", "committed_abstain",
}

VALID_FACTION_ACTIONS = {"BuildProject", "Protect", "Grow", "Toil"}

_DEAL_RE = re.compile(r"<deal>\s*(.*?)\s*</deal>", re.DOTALL)
_DEAL_OPEN_RE = re.compile(r"<deal>\s*(.*?)$", re.DOTALL)  # truncated fallback

# Simple string → term-type mapping for when LLM returns strings instead of dicts
_STRING_TERM_MAP = {
    "public_endorsement": {"type": "endorsement", "duration": 3},
    "endorsement": {"type": "endorsement", "duration": 3},
    "tax_exemption": {"type": "tax_exemption", "duration": 5},
}


def _try_parse_json(text: str, truncated: bool) -> tuple:
    """Try to parse JSON, attempting recovery if truncated. Returns (dict|None, error_str)."""
    try:
        return json.loads(text), ""
    except json.JSONDecodeError:
        pass
    if not truncated:
        return None, f"JSON decode error in deal block"
    # Attempt progressive repair of truncated JSON
    for suffix in ['"}', '", "reasoning": ""}', '}']:
        try:
            return json.loads(text + suffix), "truncated response (partial recovery)"
        except json.JSONDecodeError:
            pass
    return None, "JSON decode error: response was truncated and could not be recovered"


@dataclass
class ParsedAudienceResponse:
    narrative: str
    memory_note: str
    accepted: bool = False
    mayor_terms: list = field(default_factory=list)      # List[DealTerm]
    faction_terms: list = field(default_factory=list)    # List[DealTerm]
    rep_cost_if_broken: int = 20
    reasoning: str = ""
    parse_error: str = ""


class ResponseParser:

    def parse(
        self,
        text: str,
        faction: "Faction",
        mayor: "Mayor",
    ) -> ParsedAudienceResponse:
        """
        Parse LLM response text. Extracts narrative and optional <deal> block.
        Returns ParsedAudienceResponse — deal fields are only populated when accepted=True.
        """
        match = _DEAL_RE.search(text)
        truncated = False

        if not match:
            # Fallback: response may be truncated before </deal>
            match = _DEAL_OPEN_RE.search(text)
            truncated = True

        narrative = text[:match.start()].strip() if match else text.strip()

        if not match:
            return ParsedAudienceResponse(
                narrative=narrative,
                memory_note="",
                parse_error="no <deal> block found",
            )

        raw, recovery_note = _try_parse_json(match.group(1).strip(), truncated)
        if raw is None:
            return ParsedAudienceResponse(
                narrative=narrative,
                memory_note="",
                parse_error=recovery_note,
            )

        memory_note = str(raw.get("memory_note", ""))[:60]
        accepted = bool(raw.get("accepted", False))
        reasoning = str(raw.get("reasoning", ""))
        rep_cost = int(raw.get("rep_cost_if_broken_by_mayor", 20))
        rep_cost = max(10, min(35, rep_cost))

        if not accepted:
            return ParsedAudienceResponse(
                narrative=narrative,
                memory_note=memory_note,
                accepted=False,
                reasoning=reasoning,
                rep_cost_if_broken=rep_cost,
            )

        mayor_terms, err = self._parse_terms(
            raw.get("mayor_terms", []), side="mayor", faction=faction, mayor=mayor
        )
        if err:
            return ParsedAudienceResponse(
                narrative=narrative,
                memory_note=memory_note,
                accepted=False,
                reasoning=reasoning,
                parse_error=err,
            )

        faction_terms, err = self._parse_terms(
            raw.get("faction_terms", []), side="faction", faction=faction, mayor=mayor
        )
        if err:
            return ParsedAudienceResponse(
                narrative=narrative,
                memory_note=memory_note,
                accepted=False,
                reasoning=reasoning,
                parse_error=err,
            )

        # Resource guard: mayor can't offer exemption if domain already has one
        for term in mayor_terms:
            if term.type == "tax_exemption":
                domain_has_exemption = any(
                    fid != faction.id and mayor.is_exempt(fid)
                    for fid in mayor.exemptions
                )
                if domain_has_exemption:
                    return ParsedAudienceResponse(
                        narrative=narrative,
                        memory_note=memory_note,
                        accepted=False,
                        reasoning=reasoning,
                        parse_error="tax_exemption rejected: domain already has an exempt faction",
                    )

        # A binding deal needs a commitment from BOTH sides. If either side ends up
        # empty (LLM gave nothing in return, or terms were dropped), treat as rejected.
        if not mayor_terms or not faction_terms:
            return ParsedAudienceResponse(
                narrative=narrative,
                memory_note=memory_note,
                accepted=False,
                reasoning=reasoning,
                parse_error="deal rejected: one side committed nothing",
            )

        return ParsedAudienceResponse(
            narrative=narrative,
            memory_note=memory_note,
            accepted=True,
            mayor_terms=mayor_terms,
            faction_terms=faction_terms,
            rep_cost_if_broken=rep_cost,
            reasoning=reasoning,
            parse_error=recovery_note,
        )

    # ── Internal ───────────────────────────────────────────────────────────────

    def _parse_terms(
        self,
        raw_list: list,
        side: str,
        faction: "Faction",
        mayor: "Mayor",
    ) -> tuple[list, str]:
        """Return (terms, error_string). error_string is empty on success."""
        from engine.models import DealTerm

        if not isinstance(raw_list, list):
            return [], f"{side}_terms is not a list"

        terms: list[DealTerm] = []
        for item in raw_list:
            if isinstance(item, str):
                mapped = _STRING_TERM_MAP.get(item.lower().replace(" ", "_"))
                if mapped:
                    item = mapped
                else:
                    continue
            if not isinstance(item, dict):
                continue
            term_type = item.get("type", "")
            if term_type not in VALID_TERM_TYPES:
                continue  # drop-and-continue: skip removed/unknown terms, keep the rest

            action = str(item.get("action", ""))
            target_id = str(item.get("target_id", ""))
            duration = int(item.get("duration", 0))
            duration = max(1, min(10, duration))

            if term_type in ("committed_action",) and action not in VALID_FACTION_ACTIONS:
                return [], f"invalid committed_action: {action!r}"

            # Targeting is per-action: only BuildProject takes a target. Grow/Protect/Toil are untargeted.
            if term_type == "committed_action" and action != "BuildProject":
                target_id = ""

            terms.append(DealTerm(
                type=term_type,
                action=action,
                target_id=target_id,
                duration=duration,
            ))

        return terms, ""
