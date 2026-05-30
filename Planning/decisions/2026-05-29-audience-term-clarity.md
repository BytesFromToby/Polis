# Decisions: Audience Term Clarity + Remove budget_allocation

Spec: Planning/specs/audience_spec.md (v4)
Date: 2026-05-29

- **Remove `budget_allocation` entirely** — it was offered in the prompt and accepted by the
  parser, but `_apply_mayor_terms` (engine/llm/audiences.py) never applied it, so a faction
  could "agree" to a budget allocation that silently did nothing. Rather than wire up an effect
  for this version, cut it: cleaner term set, no phantom promise. Removal spans prompt_builder,
  response_parser (`VALID_TERM_TYPES`, `_STRING_TERM_MAP`), the `DealTerm` type comment,
  `data-models.md`, `llm-system_spec.md`, `mayor_spec.md`, and `audience_spec.md`.

- **Targeting is per-action, not a generic "optional target"** — the prompt previously described
  `target_id` as "optional faction/project id" for every `committed_action`, so the model
  attached a faction target to `Protect` and negotiated nonsense ("Protect you from House X").
  Protect's resolver (`resolve_protect(faction)`) takes no target — it's self-defense against
  all. Fix: the prompt explains each action and shows `target_id` only where it's real
  (`BuildProject` → a project; `committed_abstain` → a faction), and the parser clears
  `target_id` on `Grow`/`Protect` as defense-in-depth.

- **Removed/unknown term types are dropped, not deal-breaking (drop-and-continue)** — a `<deal>`
  containing `budget_allocation` (or any unknown type) drops that term and parses the rest; the
  deal still seals if a valid term remains on each side. This changes the parser's prior
  unknown-type behavior (which hard-rejected the whole deal) and aligns it with what
  `llm-system_spec` already specified ("invalid type → term dropped"), fixing existing drift. A
  budget_allocation-only Mayor side collapses to one-sided → no deal, via the existing
  both-sides-must-commit rule.

- **Scope held to clarity + cleanup** — no action mechanics change and no new terms are added.
  This only reshapes prompt wording, hardens the parser's target handling, and deletes a dead
  term.
