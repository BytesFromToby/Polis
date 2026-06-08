# Decisions: Shelve Tax Exemption
Spec: Planning/specs/tax-exemption-shelve_spec.md
Date: 2026-06-08

- Shelved because it has no income effect under treasury_spec v3 (income = base + Tax Offices;
  `_calc_income` never reads factions or `is_exempt`). A control whose name implies a tax break
  it can't deliver is worse than none, and `tax_exemption` deal terms pollute the audience
  training log. Revive if a faction-based tax returns.
- Dormant-hide (depth A), not full removal. Removing it from the player UI and the LLM's offered
  terms achieves the goal (gone from the player flow + the training log) with minimal churn.
  Keeping the parser's `VALID_MAYOR_TERM_TYPES`, the engine exemption machinery, and the
  domain-jealousy rep hit intact-but-dormant avoids rewriting the specced deal contract and
  several committed tests. Mirrors how the Moneylender was shelved.
- The single change that removes it from negotiations is dropping `tax_exemption` from the
  prompt's offered terms — the LLM can only propose what it's told it can offer, so endorsement
  becomes the only Mayor term in play.
- Existing parser test that exercises a `tax_exemption` term stays (it verifies the dormant path
  still parses harmlessly); only prompt/UI assertions change.
