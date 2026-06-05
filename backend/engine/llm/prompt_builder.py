"""
engine/llm/prompt_builder.py — Translates engine model data into LLM system prompts.

Handles: trait → sentence, health/rating → narrative,
         recent events from narrative_log, memory notes, valid terms.
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from engine.models import Faction, Mayor
    from sqlalchemy.orm import Session


# ── Lookup Tables ─────────────────────────────────────────────────────────────

TRAIT_SENTENCES: dict[str, str] = {
    "aggressive":   "You push hard for advantage and do not back down easily.",
    "defensive":    "You protect what you have before seeking more.",
    "industrious":  "You build and invest — conflict is a distraction from growth.",
    "destructive":  "You would rather tear down a rival than build yourself up.",
    "conservative": "You prefer stability and proven methods over risk.",
    "ambitious":    "You are always looking for the next opening.",
    "cautious":     "You weigh every move carefully before committing.",
    "pragmatic":    "You deal with the world as it is, not as you wish it were.",
    "proud":        "Your reputation matters to you — slights are not forgotten.",
    "distrusts":    "You distrust {target} — their motives have disappointed you before.",
    "angry at":     "You are angry at {target} — they wronged you and you have not forgotten.",
    "trusts":       "You trust {target} — you have found them reliable.",
    "allied with":  "You consider {target} an ally — you would rather see them succeed than fail.",
}

INTENSITY_PREFIX: dict[str, str] = {
    "slight":   "You are mildly inclined to feel that ",
    "moderate": "",
    "strong":   "You strongly feel that ",
    "very":     "You are deeply convinced that ",
}

# Health range tuples are (min_inclusive, max_inclusive)
HEALTH_NARRATIVE: list[tuple[int, int, str]] = [
    (75, 100, "Your organisation is strong and functioning well."),
    (50,  74, "Your organisation is in reasonable shape but showing strain."),
    (25,  49, "Your organisation is struggling — resources are stretched thin."),
    (1,   24, "Your organisation is in crisis. You are fighting to survive."),
]

RATING_NARRATIVE: list[tuple[float, float, str]] = [
    (4.0, 5.0, "dominant"),
    (3.0, 3.99, "significant"),
    (2.0, 2.99, "established"),
    (1.0, 1.99, "modest"),
]

# Single canonical theme (see Planning/reference/theming.md, "LLM situation briefing").
# Placeholders are filled from the player's chosen city name, name, and title.
GREEK_BRIEFING = (
    "You are the leader of a faction in {city}, a free city-state of ancient Greece by "
    "the sea that bows to no king. No one rules {city}. Power is shared and forever "
    "contested among rival worlds — noble houses, guilds, merchants, priesthoods, "
    "generals, and orators — each proud, each jealous, none able to command the rest. "
    "You speak for your faction's interest first; you are loyal to your own, not to the "
    "city and not to the {title}.\n"
    "You have been summoned by, and stand before, the {title} {player_name} — a presiding "
    "official who governs from above but cannot command you. They can only work you: "
    "endorse and condemn, bargain and betray, spend coin and favor until the city tilts "
    "their way. They have called this audience because they want something from you. Treat "
    "them as a powerful figure to use, resist, or bargain with — never a master. Stay in "
    "character at all times."
)

VALID_MAYOR_TERMS_TEMPLATE = """What the {title} can offer you:
{tax_line}
- Public endorsement (immediate +10 reputation with the {title})"""

VALID_FACTION_TERMS_TEMPLATE = """What you can commit to (one commitment, every turn for 1–10 cycles):
- Grow — invest in your own strength; no target
- Protect — raise your defenses; you take less Harm from ALL rivals; no target
- BuildProject — work to build a specific city project; name the project
- Refrain from Harm or Steal against one named faction"""

SYSTEM_TEMPLATE = """{tone_line}

You are {leader_name}, leader of {faction_name}.{leader_note}

{faction_name} is a {domain} organisation.{city_desc}{faction_desc}

Your character:
{trait_lines}

Your relationship with the {title}: {rep_label} ({rep_score:+d})

Your organisation right now:
{health_line} Your influence is {rating_desc} (level {level}, rating {rating:.2f}).

Recent events (last 5 cycles):
{recent_events}

What you remember:
{memory_notes}

{valid_mayor_terms}

{valid_faction_terms}

Speak in character throughout. Keep responses to 3–4 sentences — sharp and vivid, speaking with the pride and edge of who you are; never flat or fawning.
On your third and final response only, after your closing words, output a <deal> block with this exact JSON:

<deal>
{{
  "accepted": true | false,
  "mayor_terms": [],
  "faction_terms": [],
  "rep_cost_if_broken_by_mayor": <int 10-35>,
  "memory_note": "<10 words or fewer>",
  "reasoning": "<one sentence, out of character>"
}}
</deal>

Each entry in "mayor_terms" and "faction_terms" MUST be a JSON object — never a bare string:
- {title} terms ("mayor_terms"): {{"type": "tax_exemption", "duration": <1-10>}} or {{"type": "endorsement"}}
- Your terms ("faction_terms") — commit to exactly ONE:
  - {{"type": "committed_action", "action": "Grow", "duration": <1-10>}}
  - {{"type": "committed_action", "action": "Protect", "duration": <1-10>}}
  - {{"type": "committed_action", "action": "BuildProject", "target_id": "<a project id>", "duration": <1-10>}}
  - {{"type": "committed_abstain", "action": "Harm" | "Steal", "target_id": "<a faction id>", "duration": <1-10>}}

If you accept, "faction_terms" must contain at least one object stating what you commit to in return — an accepted deal where you give nothing will be rejected.
If no deal is reached set "accepted": false and leave term arrays empty.
memory_note must always be present even on rejection."""


# ── Helper Functions ──────────────────────────────────────────────────────────

def _health_narrative(health: int) -> str:
    for lo, hi, text in HEALTH_NARRATIVE:
        if lo <= health <= hi:
            return text
    return "Your organisation's condition is unknown."


def _rating_narrative(rating: float) -> str:
    for lo, hi, text in RATING_NARRATIVE:
        if lo <= rating <= hi:
            return text
    return "uncertain"


def _trait_lines(faction: "Faction", factions: dict) -> str:
    lines = []
    for ft in faction.traits:
        base = TRAIT_SENTENCES.get(ft.trait)
        if base is None:
            continue
        if ft.target_id:
            target_name = factions.get(ft.target_id)
            target_label = target_name.name if target_name else ft.target_id
            sentence = base.format(target=target_label)
        else:
            sentence = base
        prefix = INTENSITY_PREFIX.get(ft.intensity, "")
        if prefix:
            sentence = prefix + sentence[0].lower() + sentence[1:]
        lines.append(f"- {sentence}")
    return "\n".join(lines) if lines else "- No strong defining traits noted."


def _recent_events(run_id: str, faction_id: str, db: "Session") -> str:
    """Query last 5 cycles of narrative_log, filter to this faction's events."""
    try:
        from db.models import NarrativeLog
        rows = (
            db.query(NarrativeLog)
            .filter(NarrativeLog.run_id == run_id)
            .order_by(NarrativeLog.cycle_number.desc())
            .limit(5)
            .all()
        )
        events = []
        for row in rows:
            try:
                cycle_events = json.loads(row.events_json)
            except Exception:
                continue
            for ev in cycle_events:
                if ev.get("actor_id") == faction_id or ev.get("target_id") == faction_id:
                    events.append(f"- {ev.get('narrative', '')} (cycle {row.cycle_number})")
            if len(events) >= 8:
                break
        return "\n".join(events) if events else "- No recent events recorded."
    except Exception:
        return "- Recent events unavailable."


def _memory_notes(run_id: str, faction_id: str, db: "Session") -> str:
    """Fetch faction_memory rows ordered oldest→newest and format for prompt."""
    try:
        from db.models import FactionMemory
        rows = (
            db.query(FactionMemory)
            .filter(FactionMemory.run_id == run_id, FactionMemory.faction_id == faction_id)
            .order_by(FactionMemory.cycle.asc())
            .all()
        )
        if not rows:
            return "- No prior history recorded."
        lines = []
        for row in rows:
            if row.is_summary:
                lines.append(f"- older interactions summary: {row.note}")
            else:
                lines.append(f"- {row.note}")
        return "\n".join(lines)
    except Exception:
        return "- Memory unavailable."


def _tax_line(faction: "Faction", mayor: "Mayor", domains: dict) -> str:
    domain_id = faction.domain_primary
    # Check if any faction in this domain already has an exemption
    domain_has_exemption = any(
        fid != faction.id and mayor.is_exempt(fid) and
        domains.get(fid) is not None  # crude check — full check in audience flow
        for fid in mayor.exemptions
    )
    if domain_has_exemption:
        return "- Tax exemption: not currently available — another faction in your domain is already exempt"
    return "- Tax exemption for 1–10 cycles"


# ── Public API ────────────────────────────────────────────────────────────────

class PromptBuilder:

    def build(
        self,
        faction: "Faction",
        run_id: str,
        mayor: "Mayor",
        db: "Session",
        factions: dict,
        domains: dict,
        city_description: str = "",
        city_setting: str = "",
        city_name: str = "Polis",
        player_name: str = "Kallisto",
        player_title: str = "Prytanis",
    ) -> str:
        leader_name = faction.leader.name if faction.leader else faction.name
        leader_note = ""
        if faction.leader and faction.leader.personality_notes:
            note_text = " ".join(n.strip() for n in faction.leader.personality_notes if n.strip())
            if note_text:
                leader_note = f" {note_text}"
        # Single canonical theme: always open with the Greek briefing (city_setting is
        # accepted for back-compat but no longer selects a tone — see theming.md).
        tone_line = GREEK_BRIEFING.format(
            city=city_name, player_name=player_name, title=player_title,
        )
        city_desc = f" {city_description.strip()}" if city_description.strip() else ""
        fac_desc_text = getattr(faction, "description", "") or ""
        faction_desc = f"\n{fac_desc_text.strip()}" if fac_desc_text.strip() else ""

        trait_lines = _trait_lines(faction, factions)
        rep_score = mayor.get_reputation(faction.id)
        rep_label = mayor.reputation_label(faction.id).capitalize()

        health_line = _health_narrative(faction.health)
        rating_desc = _rating_narrative(faction.rating)

        recent_events = _recent_events(run_id, faction.id, db)
        memory_notes = _memory_notes(run_id, faction.id, db)

        tax_line = _tax_line(faction, mayor, factions)
        valid_mayor = VALID_MAYOR_TERMS_TEMPLATE.format(
            tax_line=tax_line,
            domain=faction.domain_primary,
            title=player_title,
        )

        valid_actions = "BuildProject, Protect, Grow"
        valid_faction = VALID_FACTION_TERMS_TEMPLATE.format(valid_actions=valid_actions)

        return SYSTEM_TEMPLATE.format(
            tone_line=tone_line,
            title=player_title,
            leader_name=leader_name,
            leader_note=leader_note,
            faction_name=faction.name,
            domain=faction.domain_primary,
            city_desc=city_desc,
            faction_desc=faction_desc,
            trait_lines=trait_lines,
            rep_label=rep_label,
            rep_score=rep_score,
            health_line=health_line,
            rating=faction.rating,
            level=faction.level,
            rating_desc=rating_desc,
            recent_events=recent_events,
            memory_notes=memory_notes,
            valid_mayor_terms=valid_mayor,
            valid_faction_terms=valid_faction,
            valid_actions=valid_actions,
        )
