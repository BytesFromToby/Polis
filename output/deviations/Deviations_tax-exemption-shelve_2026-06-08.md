# Deviations — Shelve Tax Exemption
Blueprint: Planning/blueprints/tax-exemption-shelve_BP.md
Date: 2026-06-08

| Slice | Step | Deviation | Why |
|-------|------|-----------|-----|
| 1 | 1 | Also removed the unused `domain=faction.domain_primary` kwarg from `VALID_MAYOR_TERMS_TEMPLATE.format(...)` | Only `title` is used after dropping the tax line; pure cleanup, same result. |
| Final | 2 | `treasury_spec.md` had no "Faction Tax Exemption" section; added the deferral note to its "Deferred to future" list instead | The v3 rewrite had already removed the section. Inspector correctly flagged that Done-when item 6 still requires a treasury_spec note, so a "Faction tax exemption — shelved" bullet was added to close it. |

Otherwise implemented as written. Remaining tax-exemption mentions in the specs all describe
the intentionally-dormant engine machinery (domain jealousy, mayor.exemptions, deal-term
revocation, VALID_MAYOR_ACTIONS allowlist), consistent with the dormant-hide decision.
