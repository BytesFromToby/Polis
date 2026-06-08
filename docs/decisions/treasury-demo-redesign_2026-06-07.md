# Decisions: Treasury Demo Redesign (v3)
Spec: Planning/specs/treasury_spec.md
Date: 2026-06-07

- Income = flat base 20 + 20 per completed Tax Office; per-domain auto-tax removed. The v2
  auto-tax silently taxed every domain at the default 0.20 (unearned, ballooning), and the
  rate-tier lever was already broken post projects-v6. A flat base + buildable lever is the
  simplest model that makes gold a real decision in a short demo. Rejected reconnecting the
  rate-tier system for the demo (more wiring, more concepts) — deferred to future.
- Tax Offices live in a faction-less city-wide domain `civic` ("Public Treasury"), not in a
  faction-bearing domain. Putting the tax lever in e.g. `professions` would make that faction
  the gatekeeper of city income — a power concentration the user explicitly ruled out.
- No hard cap on Tax Office count. Discovered during architect that `mayor_build_base` is
  explicitly "not gated by cap" — the domain cap is a display/influence metric and building
  raises it. So the originally-proposed "civic cap = 12 → ~6 offices" premise was false. Tax
  Offices are paced by the gold/AP economy (~200 gold + 4 AP each) instead. Rejected adding a
  new build-count cap (new mechanic, contradicts existing build rule) for the demo; revisit
  after playtest if needed.
- Faction-less domains keep their authored cap (skip the fill-based `_freeze_base_caps`), and
  Tax Offices add no `stack_cap_contribution`. Without this, `civic` would freeze to cap 0 and
  then creep upward as offices are built — a meaningless readout. Mirrors the old
  tax_collection "no domain cap effect" principle.
- Insolvency: clamp gold at 0 and convert the shortfall into damage to random NON-civic base
  projects; Tax Offices excluded. Excluding Tax Offices is essential — damaging income
  projects would deepen the shortfall (death spiral) instead of self-correcting. Destroying
  maintenance-costing projects lowers upkeep, so the system rebalances. Replaces the v2
  bankruptcy ladder.
- Moneylender, emergency guard surge, public works, rate-tier effects, and the bankruptcy
  ladder are deferred to future. Half-wired complexity with no payoff in a short demo; engine
  blocks left dormant rather than ripped out to keep the build small.
