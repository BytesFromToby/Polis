# Features Todo

Rough backlog — no priority order implied.

## Known Balancing Debt
- [ ] **Domain cap rebalancing** — current caps (300 base, 600 with starting projects) are placeholder values set for early testing. Needs full review once faction population and project system are playable. All city templates will need updating.

## Open Decisions
- [ ] **Faction `unstable_stacks` — reset or decay?** A faction accumulates unstable_stacks (max 3, −1/stack to rolls) when hit by a partial Attack.
  - **A — Decay (current code):** stacks persist across cycles, drop 1/cycle (3 stacks = 3 cycles to clear).
  - **B — Reset (original spec intent):** stacks reset to 0 at end of each cycle.
  - Where: `engine/cycle/end_of_cycle.py` (~L106), `engine/models.py` (`unstable_stacks`). Changed reset→decay on 2026-04-05. *(Merged from CLEANUP.md, 2026-05-25.)*

---

## Mayor Panel (Player Agency)
- [ ] Treasury display — gold, income, expenses per cycle
- [ ] Mayor action points — show AP available, spend on actions
- [ ] Mayor action accumulation cap — can't hoard indefinitely
- [ ] Projects panel — list active projects, commission new ones, show status
- [ ] Mayor actions wired to API and engine

## Mayor's Toolkit — Action Types
Political:
- [ ] Meet with a faction leader (audience)
- [ ] Publicly endorse a faction
- [ ] Publicly condemn a faction
- [ ] Broker a deal between two factions

Resources:
- [ ] Allocate city budget to a domain
- [ ] Withhold resources from a faction
- [ ] Commission a project

Authority:
- [ ] Issue a decree (factions comply or resist based on traits)
- [ ] Appoint or remove an official
- [ ] Turn a blind eye

Information:
- [ ] Request a report on a faction
- [ ] Plant a rumor

## Mayor Reputation
- [ ] Per-faction reputation tracking (not a single number)
- [ ] Per-domain reputation tracking
- [ ] Reputation display in UI
- [ ] Reputation affects faction behavior toward mayor

## Mayor Removal / End Conditions
- [ ] Removal by coalition — enough factions turn against mayor
- [ ] Removal by treasury bankruptcy
- [ ] Removal by public revolt
- [ ] City falls to external forces
- [ ] No traditional win — survival length and achievements are the measure
- [ ] End-of-run summary screen

## Achievements
- [ ] Soft goals the player can pursue during a run
- [ ] Achievement tracking and display
- [ ] TBD specifics

## Treasury
- [ ] Tax rate lever — raise for income, creates faction friction
- [ ] Idle treasury earns nothing
- [ ] Invest with moneylender — locked period, earns interest
- [ ] Borrow — immediate funds, interest bleeds each cycle
- [ ] City guard funding — neglect → city becomes unsafe

## Audience System (POSSIBLE — revisit after core is solid)
- [ ] Mayor requests audience with faction leader (costs action, cooldown)
- [ ] AI frames the scene based on faction traits and reputation
- [ ] Player writes what they say; AI responds in character
- [ ] One follow-up exchange, then audience ends
- [ ] Outcomes: trait shift, reputation adjustment, memory added to faction personality record
- [ ] Paranoid/distrustful factions may mislead
- [ ] Cooldown — can't spam audiences

## Faction UI
- [ ] Faction detail view — click faction to expand full info
- [ ] Traits display with intensity
- [ ] Relationships display (Friend/Foe list)
- [ ] Leader detail — name, traits, status
- [ ] Faction history — what it did last N cycles
- [ ] Mayor's reputation with this faction shown on card

## Event Log
- [ ] Cycle headers — group events under collapsible cycle blocks
- [ ] Filter by faction or domain
- [ ] Dramatic event callouts more prominent
- [ ] Show cascade and collapse events distinctly

## Special Factions
- [ ] The Public — display disposition, support level, trait state
- [ ] Moneylender — show debt/leverage state, borrow/invest UI
- [ ] External Threats — show active threats and duration

## Projects
- [ ] Mayor-initiated projects
- [ ] Faction-initiated projects
- [ ] Faction activity during construction (sabotage, rivalry)
- [ ] Project destruction as a faction attack vector
- [ ] Starting city infrastructure display

## Game Structure / Scenario
- [ ] Turn limit or scenario length setting
- [ ] Visibility modes — full (current) vs limited (fog of war)

## Sim Controls
- [ ] Cycle speed setting (run N cycles at once)
- [ ] Auto-pause triggers — player configures what events cause a pause
- [ ] Speed controls — slow / normal / fast (for future real-time mode)
- [ ] Keyboard shortcut for Run Cycle

## City Builder
- [ ] Custom city creation flow
- [ ] Add/edit domains
- [ ] Add/edit factions with traits
- [ ] Save as template

## Multiple Cities / Campaigns
- [ ] Additional starting cities beyond Rivers Point
- [ ] City select screen on title

## Backend / API Gaps
- [ ] Mayor action endpoints
- [ ] Projects endpoints (commission, repair, list)
- [ ] Events endpoints (active events, deck state)
- [ ] Special faction state endpoints
- [ ] Mayor reputation endpoints

## Polish
- [ ] Loading states on all async actions
- [ ] Error messages surfaced clearly in UI

## Long Term
- [ ] Visual map of the city — toggle domains, factions, health layers
- [ ] Real-time with pause mode (watch cycle play out event by event)
- [ ] Sound and music
- [ ] LARP / multiplayer mode

## City Builder (Procedural Generation)
- [ ] Procedural city generation — replace hand-authored JSON templates with generated starting states (see `city-generation_spec.md`)
