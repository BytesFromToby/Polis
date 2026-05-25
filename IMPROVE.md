# Improvement Plan

This file tracks what `/improve` does and where outputs go.

## How to run
```
/improve
```
Or manually follow the phases in `H:\my_skills\improve\skill.md`.

## Outputs

| File | What |
|------|------|
| `tools/output/ImproveLog.md` | Everything done during the improvement pass |
| `tools/output/Recommendations.md` | Suggested changes that need human decision |
| `tools/output/AUDIT.md` | Engine snapshot (entity attrs, actions, traits, formulas) |
| `tools/output/*.csv` | Same data in spreadsheet form |

## Phase Summary

1. **Audit & Baseline** — Run audit tool, run tests, log starting state
2. **Spec Drift** — Compare each spec to code, fix drift, log everything
3. **Test Coverage** — Add pytest tests for uncovered engine modules
4. **MD Optimization** — Rewrite MD files for Claude efficiency
5. **Tools** — Build reusable scripts for health checks, validation
6. **Recommendations** — Compile prioritized change list
