# City Sim — Phase 2 Brainstorm

---

## 2026-05-17

### The Pitch
You are the Mayor. The city's factions and leaders have their own agendas. How much or little pressure will you exert? Where do you want the city to go? The city keeps moving even if you do nothing.

---

### End Conditions
- Mayor is removed from power
- City falls to outside forces
- No traditional win state — survival length and achievements are the measure

### Achievements
- Soft goals the player can pursue during a run
- TBD specifics

---

### Factions — Personality System
- Each faction has a list of character traits
- Traits have intensity (slightly → very)
- Traits can be general or targeted at a specific faction ("angry at X", "trusts Y")
- Traits evolve over time — reinforced or changed by events
- AI reads trait list each cycle to weight faction decisions
- Personality drives behavior; goals emerge from personality, not the other way around

---

### Mayor's Toolkit
Indirect and costly — nudge, pressure, deal. Never direct command.

**Political**
- Meet with a faction leader
- Publicly endorse or condemn a faction
- Broker a deal between two factions

**Resources**
- Allocate city budget to a domain
- Withhold resources from a faction
- Commission a project (factions compete over it)

**Authority**
- Issue a decree (factions comply or resist based on traits)
- Appoint or remove an official
- Turn a blind eye

**Information**
- Request a report on a faction
- Plant a rumor

---

### Mayor — Action Economy & Turn Structure

**Real-time with pause:**
- City runs in real time — factions act sequentially, one by one, visible to the player
- Player watches the cycle play out as events: "Faction 1 did X, Faction 2 did Y..."
- Player can pause at any time to study the state and decide what to do
- When paused, current faction waits — city holds until player unpauses
- Mayor gets an action slot at the end of each full cycle, or can spend mid-cycle on a pause

**Speed controls:**
- Slow / normal / fast — player tunes how much they can absorb
- Auto-pause triggers — player configures what events cause an automatic pause (faction collapse, project attacked, reputation drop, etc.)

**Action economy:**
- Mayor accumulates actions up to a cap — can't hoard indefinitely
- Actions are a resource spent over time, not one-per-turn
- Some mayor actions cost more than one action (building a dock expansion = multiple actions over several cycles)
- Big projects lock up action budget — creates opportunity cost
- Crisis mid-project forces a choice: finish the commitment or respond to the emergency

**Mayor reputation:**
- Tracked per faction and per domain — not a single number
- Ironmongers can love you while the Public despises you
- That tension is the game
- Reputation drives end condition — removal happens when enough factions or the public turn against you

**Mayor removal:**
- Requires coalition or threshold — TBD specifics
- Treasury bankruptcy is a potential trigger
- Public revolt if public reputation collapses

---

### New Engine Primitives Needed
- Currency / city budget (political and weighted, not supply chain)
- External threats (bandits etc. — aggressive factions with no domain stake, just pressure)

---

### Mayor's Treasury
- Mayor has a treasury — income from taxes, expenditure on city needs
- Taxes are a lever: raise them for income, but creates faction friction and attitude penalties (-growth)
- City guard requires ongoing funding — neglect it and the city becomes unsafe

**Treasury mechanics:**
- Idle treasury earns nothing
- Invest with moneylender — locked for a set period, earns interest, unavailable for emergencies
- Borrow — immediate funds, interest bleeds treasury each cycle

**The moneylender as a faction:**
- Has traits like any other faction
- Can be pressured
- If you borrow heavily, they gain leverage over the mayor

---

### Events — Scripted Pressure Sequences
Resources exist as flavor and triggers, not mechanics to manage. A mine disaster doesn't add a resource system — it injects timed pressure into the faction system via cascades.

**Event structure:**
- Trigger (what happened)
- Target (which faction or domain is hit)
- Duration (how many cycles the effect lasts)
- Cascade (secondary factions or domains affected later)

**Example:** Iron mine disaster → Ironmongers take "outside attack" pressure for 2 cycles → docks get -growth modifier cycles 3-4

**Event types:**
- Random — engine rolls them during a run
- Scripted — city setup includes a deck of possible events
- Mayor-triggered — player deliberately causes one

---

### Mayor — Audience System
A showcase of AI in action. The player talks directly to a faction leader, filtered through their personality.

**Flow:**
1. Mayor requests an audience (costs an action, subject to cooldown)
2. AI writes a short framing sentence — sets the tone based on faction traits and current reputation
3. Player writes a prompt — what they say to the faction leader
4. AI responds in character, driven by faction personality
5. Player gets one follow-up exchange
6. Audience ends

**Outcomes — subtle and persistent:**
- Slight trait shift (reinforced or nudged by what was said)
- Faction's feeling toward the mayor adjusts
- One sentence added to the faction's personality record — a memory of the interaction
- Over time, faction personality grows richer with mayoral history

**Constraints:**
- Two exchanges per audience — choose words carefully
- Cooldown — can only meet a faction every X cycles, prevents spamming for information
- Paranoid or distrustful factions may mislead
- Factions that trust the mayor may reveal something useful

**What audiences are NOT:**
- Not a way to directly affect faction actions
- Not a shortcut to mechanical outcomes
- Conversations affect personality and relationship only — factions still act on their own agenda

**Why it matters:**
- Intelligence gathering — learn what a faction is thinking
- Relationship building — shift reputation and traits slowly over time
- The AI personality does visible, interesting work here

**Status: POSSIBLE — not committed**
- Scope risk: significant. Freeform AI conversation could balloon complexity.
- For audiences to work properly, they must be bounded by real game mechanics — player can only offer/request things that exist as actual game actions. Otherwise AI negotiates fantasy with no game state effect.
- Decision: revisit after core mechanics are solid. May be a later feature or demo mode.

---

### Visibility
- Full trait visibility for now (build and test)
- Limited visibility as a future game mode

---

### Visual Layer
- A city you can look at, not just tables
- Layered — toggle domains, factions, health on/off
- Explore the data produced by the sim visually

---

### Projects — City Infrastructure
Projects are persistent city infrastructure — physical things that exist, get built, and can be destroyed.

**Structure:**
- Build cost (treasury)
- Build time (cycles)
- Permanent effect on city stats after completion
- Faction involvement during construction (work, rivalry, sabotage)

**Initiation:**
- Mayor-initiated (city wall, public works)
- Faction-initiated (Stevedores push for dock expansion)

**During construction:**
- Creates faction activity — who builds it gains influence
- Rivals may delay or sabotage
- Some projects require faction cooperation to proceed

**After completion:**
- Modifies city baseline stats permanently
- Example: city wall → city guard effectiveness bonus
- Example: dock expansion → increased trade capacity

**Destruction:**
- Projects can be attacked by factions or destroyed by events/disasters
- Destroying infrastructure is a faction attack vector — burn the docks, strangle trade, collapse the Stevedores
- Projects give factions a natural reason to target other domains — attack the infrastructure, not the faction directly
- Solves the current problem of cross-domain attacks feeling arbitrary — interconnected infrastructure makes it make sense

**Starting city:**
- City begins with existing infrastructure already in place
- Example: 5 docks set the baseline trade capacity at game start
- Starting projects define the city's initial stat baseline

---

### Special Factions
Factions that exist outside the normal domain power structure but affect the city and the mayor.

- **The Public** — general population as a faction. Has traits (content, restless, angry). Affected by taxes, safety, city events. Popular support is mayoral legitimacy — other factions have to respect it. Can turn on the mayor.
- **The Moneylender** — see Treasury section above.
- **External Threats** — bandits etc. Pure aggression, no domain stake, just pressure on the city.

---

### What We Have (Engine Bones)
- Faction health, influence, actions, cascades
- Named NPCs with ratings
- Domain system
- Cycle runner
- Emergent narrative already happening in runs
