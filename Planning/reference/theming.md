# Theming (Reference)

The world identity that specs and content cite for naming and flavor. Reference doc —
definitional, no **Done when:** items.

**Date:** 2026-05-26

Polis has **one canonical theme: an ancient-Greek city-state.** There is no multi-theme
or themed-city-pack system. 

---

## Tag Lines

#1 Polis — rule the unrulable
Polis — rule the city that devours its rulers
Polis — climb the city that buries its masters
Polis — they say no one can rule it. Prove them wrong.
Polis — seize a city built to resist you
Polis — rule the ungovernable
Polis — master the city that bows to no one

## The premise

The game models the struggle for influence inside a single ancient-Greek **polis** — a
self-governing city-state in the classical mold (think Athens, Corinth, Syracuse, but
fictional). Factions — noble clans, the citizen assembly, merchant houses, priesthoods,
the generals, the harbor crews — contest the city's **spheres of influence** one move at a
time, forming and breaking alliances. The result is emergent civic drama: demagogues rise,
oligarchies fracture, the mob turns, exiles return.

The human player governs from above and intervenes in the city's politics. (Player title
under the Greek theme is an open question — see below.)

---

## Theme vs. mechanics — what theming may and may not touch

The engine is **theme-agnostic**: a city is just data (domains, factions, relationships,
leaders). Theming is **content and flavor only**.

- **Theming MAY change:** domain names, faction names and descriptions, leader names and
  personality notes, project names, event flavor text, UI copy.
- **Theming MUST NOT change:** the relationship vocabulary, the contest math, faction
  fields, cycle order, or any tested behavior. Those are mechanical and live in
  [`data-models.md`](data-models.md) and [`formulas.md`](formulas.md). Re-skinning a
  domain does not change how it behaves.

Mechanical vocabulary that stays fixed regardless of theme:
- **Domain↔domain relationship traits:** `Friend`, `Foe`, `Client`, `Neutral`, `Hide`
- **Faction↔faction relationship traits:** `Friend`, `Foe`, `Client`, `Neutral`
- **Leader status:** `present`, `weakened`, `absent`
- **Personality trait intensities:** `strong`, `moderate`, `slight`

---

## Default names
City name: Polis
Mayor name: Kallisto

---

## Overall Theme

**Polis is a free city by the sea** — a self-governing Greek city-state that bows to no king
and trusts no single hand for long. It is proud, crowded, and quarrelsome: a few thousand
citizens who believe the city belongs to them, and who will argue, bribe, sue, and shout to
prove it. Its wealth comes off the water and out of the workshops; its glory comes from its
temples, its games, and its fleet; its politics never sleep. To live here is to live inside an
argument that never ends.

Climb up from the harbor and the city rises in layers. Below, the docks and shipyards reek of
pitch and brine, loud with stevedores and the crews of the war-fleet. Inland spreads the agora,
the city's beating heart — merchants haggling, bankers reckoning at their tables, orators
working the crowd, every rumor in the city bought and sold by noon. Above it all stand the
temples on the heights, white marble catching the sun; and beyond the walls lie the olive groves
and the estates of the old families who still believe the city is theirs by blood.

**No one rules Polis.** Power is shared, contested, and forever in motion among its rival
worlds — the old aristocratic houses, the guilds of makers, the merchant and banking houses,
the skilled professions, the priesthoods and their oracles, the generals and the citizen-
soldiers, the philosophers and orators of the schools. Each is proud, each is jealous, and none
can command the rest. They court one another and knife one another in the same breath, and the
city lurches forward on the sum of their schemes.

This is a city always **one crisis from greatness or ruin.** A good harvest and a won war make
it the envy of the sea; a famine, a plague, a lost fleet, or a clever demagogue can tip it into
riot, exile, and the strong hand of a tyrant. Polis has buried more leaders than it remembers.
It raises them up on the roar of the assembly and casts them down just as fast — and it is
always, quietly, afraid of the one who will not let go.

Into this steps the player. You do not own Polis and you cannot command it; you can only *work*
it — endorse and condemn, bargain and betray, spend coin and spend favor, and lean on the
factions until the city tilts your way. You begin as one presiding voice among many, and the
long game is to climb toward an authority the city both craves and dreads. Polis will make you
or break you. It usually does both.

---

## LLM situation briefing

A short, drop-in explainer for the LLM that role-plays faction leaders in audience with the
player (see [`../specs/audience_spec.md`](../specs/audience_spec.md)). Hand it to the model as
scene-setting context. Written in the second person, addressed to the model-as-leader.

> You are the leader of a faction in **Polis**, a free city-state in Ancient Greece by the sea that bows to no king. No one rules Polis. Power is shared and forever contested among rival worlds — noble houses, guilds, merchants, priesthoods, generals, and orators — each proud, each jealous, none able to command the rest. You speak for **your faction's interest first**; you are loyal to your own, not to the city or to the player.
> You were summond by and stand before **Prytanis** — a presiding official who governs from above but cannot command you. They can only *work* you: endorse and condemn, bargain and betray, spend coin and favor until the city tilts their way. They have called this audience because they want something from you. Treat them as a powerful player to use, resist, or bargain with — never a master. Stay in character at all times.

---

## Domain roster (roster restructure 2026-06-14)

The six canonical spheres of influence (plus the faction-less `civic` treasury lane).
Mechanically each is a domain with a cap, drift, and a relationship row to every other domain.

Each domain is a distinct answer to *"where does your power come from?"* The English name is
used in-game; the Greek is flavor.

| Domain (English) | Greek | The sphere — and its source of power |
|---|---|---|
| **Aristocracy** | *Eupatridai* — "the well-born" | The old landed clans. Power by **birth** — blood, lineage, inherited estates. |
| **Guilds** | *Demiourgoi* — "craftsmen" | Smiths, masons, shipwrights and their backers. Power by **production** — they make things. |
| **Port** | *Limēn* — "the port" | The maritime-commercial bloc — dock labor, the merchant houses, the warehouses. Power by **command of the sea and its trade**. |
| **The Professions** | *Technitai* — "people of skill" | Healers, performers, clerks, skilled practitioners. Power by **cultivated skill and public renown**. |
| **Temples** | *Hiereis* — "the priesthood" | Cults, priesthoods, oracles. Power by **divine legitimacy**. |
| **Military** | *Stratos* — "the host" | The guard, the army, and the fleet. Power by **force of arms**. |

> **Restructure (2026-06-14):** was eight domains. **Trade** folded into **Port** (the merchant
> houses and the warehouse ring moved there; the bankers' bookkeeping went to the Quillsworn).
> **Academy** was dissolved — its philosophers and orators are parked for the future institutions
> feature, and its star-readers joined the Bright Order. **Harbor** was renamed **Port** to cover
> the whole maritime-commercial bloc. See `../specs/roster-restructure_spec.md`.

The common people are handled by the *public-needs* system (not a domain); **Assembly** and
**Council** are deferred to the future institutions feature (see the player-title note below).

---

## Faction & leader conventions

- **Factions** are named institutions or groups within a domain. Three per domain is the
  floor; many will have more. Internal rivalry is the point.
- **Leaders** carry Greek personal names and a short `personality_notes` line in character.
- Keep names **fictional but period-plausible** — Greek flavor, but not overwhelming. The
  "House Name — *the gloss*" shape works well.

**Character traits must be drawn from the engine's functional set** (anything else is dead
flavor — it won't affect behavior). The ten, each at intensity `slight` / `moderate` /
`strong` / `very`:

`aggressive` · `defensive` · `ambitious` · `paranoid` · `opportunistic` · `expansionary` ·
`conservative` · `corrupt` · `industrious` · `destructive`

**Per-faction format:**
> **Name** — *short gloss*
> One-line identity: who they are within the domain.
> Character: `trait` (intensity), `trait` (intensity)
> Leader: **Greek Name** — one-line personality in character.

---

## Factions by domain

Built one domain at a time. Numbers vary by domain; over-produce, then cut.

### Aristocracy (*Eupatridai*) — power by birth

Rival noble houses, each an ancient name with its own claim on the city.

> **The Eumelidai** — *"the well-flocked," old wealth in land and herds*
> The senior clan: vast estates, an ancient name, treats the city as theirs by right.
> Character: `conservative` (strong), `defensive` (moderate)
> Leader: **Lysandros the Elder** — venerable, immovable; sees every change as decay.

> **The Pyrrhidai** — *"the fire-blooded"*
> A rising house, new money married into old blood, hungry to displace the Eumelidai.
> Character: `ambitious` (strong), `expansionary` (moderate)
> Leader: **Kleon Pyrrhos** — young, brilliant, impatient for primacy.

> **The Skiadai** — *"the shadowed"*
> A once-great house in decline, clinging on through favors, debts, and quiet leverage; what
> remains of its land is mostly vineyard now.
> Character: `opportunistic` (strong), `corrupt` (slight)
> Leader: **Demarete of the Skiadai** — gracious in public, ruthless in the dark.

> **The Elaiades** — *the olive-groves of the inland slopes*
> A younger branch of the old estates, rich in oil if not yet in name — climbing on the back of
> the city's most valuable crop.
> Character: `ambitious` (moderate), `conservative` (slight)
> Leader: **Theron of the Slopes** — patient and acquisitive; plants for grandsons and buys land the way others buy bread.

### Temples (*Hiereis*) — power by divine legitimacy

Rival priesthoods and cults, each claiming the city's faith — and the wealth and authority
that come with it. The first four are core; the last two are extras to keep or cut.

> **The Tidesworn** — *priests of the Earth-Shaker (Poseidon)*
> The sea-god's cult — storms, earthquakes, the harbor's fear. They claim the god's wrath as leverage.
> Character: `aggressive` (moderate), `ambitious` (moderate)
> Leader: **Nereus Halios** — booming and volatile; speaks of the god's anger as if it were his own.

> **The Greenmantle** — *the harvest cult of the earth-mother (Demeter)*
> The grain-and-fertility cult, rooted in the seasons; blesses the fields and feeds the festivals.
> Character: `industrious` (moderate), `defensive` (slight)
> Leader: **Chloris of the Furrow** — warm and patient; thinks in seasons, slow to anger and slow to forgive.

> **The Raving Choir** — *ecstatic prophets of the mad god (Dionysos)*
> Frenzied seers who prophesy in fits and whip crowds into ecstasy. Beloved, feared, uncontrollable.
> Character: `destructive` (moderate), `opportunistic` (moderate)
> Leader: **Eurymache the Raving** — wild-eyed, speaks in the god's tongue; no one knows what she'll do next.

> **The Bright Order** — *the great oracle of the far-shooting god (Apollo)*
> The establishment oracle — prestigious, panhellenic, consulted before wars and colonies. Kingmakers in robes. The city's star-readers and calendar-keepers now keep their charts under the Order's roof.
> Character: `ambitious` (strong), `opportunistic` (moderate)
> Leader: **High Seer Aletheian** — calm and smiling; every prophecy is a move on a longer board.

### Military (*Stratos*) — power by force of arms

The armed power of the city: the watch that keeps order within the walls, the citizen army,
and the fleet. (The hired companies and a victorious general's veterans have been folded into
these three — the mercenary lever survives as a way to reinforce the army.)

> **The City Guard** — *the watch within the walls*
> The force that keeps the peace at home — patrols, the gaols, the breaking of riots — and leans on the crowd with the spear-butt when the bread fails.
> Character: `defensive` (moderate), `aggressive` (slight)
> Leader: **Captain Brasidas** — hard and dutiful; keeps order first and asks after justice later.

> **The Shieldsworn** — *the citizen phalanx (the Army)*
> The hoplite militia of property-owning citizens, the city's backbone and its land army — and proud that only citizens should bear its spear.
> Character: `defensive` (strong), `conservative` (moderate)
> Leader: **Drakon the Steadfast** — stolid, dutiful; distrusts hired blades and glory-hounds alike.

> **The Oarsworn** — *the war fleet and its crews (the Fleet)*
> The triremes and the citizen-rowers who drive them — the city's reach across the sea, the shield of its grain-ships, and a restless power base of the common man.
> Character: `expansionary` (strong), `ambitious` (moderate)
> Leader: **Naukrates of the Long Oars** — bold and restless; dreams of a city whose walls are its ships.

### Port (*Limēn*) — power by command of the sea and its trade

The maritime-commercial bloc: the labor of the wharves, the merchant houses that run the
sea-lanes, the warehouses, and the fishing crews. Whoever holds the Port holds the city's food
imports and its purse. (The *war* fleet sits under Military.)

> **The Dockhands** — *the wharf-hands and port wardens*
> Labour and authority of the quay merged into one bloc — they load and haul, and they decide who docks, when, and at what toll. A word from them can still the whole harbour.
> Character: `industrious` (moderate), `conservative` (moderate)
> Leader: **Glaukos of the Quay** — gruff and immovable; protective of his gangs and his ledgers alike.

> **The Netmenders** — *the fishing crews who feed the city*
> The boat crews who work the waters — weather-beaten, independent, traditional. The city's daily catch and a food supply unto themselves.
> Character: `conservative` (moderate), `defensive` (slight)
> Leader: **Glaukos the Weathered** — salt-cured and plain-spoken; trusts the tide more than any magistrate.

> **The Merchant Houses** — *the wholesale traders and shipowners*
> The great houses that move grain and oil by sea — wholesale traders, shipowners, and the resident foreigners among them. The city's lifeline and its purse, always reaching for a wider market.
> Character: `opportunistic` (strong), `ambitious` (moderate)
> Leader: **Demaratos the Elder** — jovial and grasping; counts the city's worth in cargoes landed.

> **The Storehouse Ring** — *the warehouse speculators who corner the market*
> A cartel that buys up stock and sits on it — hoarding grain and goods to choke supply and spike the price, then selling at the city's worst hour. Courted, they cushion a famine; crossed, they make one worse.
> Character: `corrupt` (strong), `opportunistic` (moderate)
> Leader: **Hieron the Patient** — soft-spoken and predatory; waits for famine the way others wait for harvest.

### Guilds (*Demiourgoi*) — power by production

The makers — those whose power is the things they build. Guilds *make* goods; the Port ships
and trades them. This is the city's largest domain — a crowded quarter of crafts.

> **The Bronzehands** — *the smiths and metalworkers*
> The forges — bronze and iron, arms, tools, fittings. Their hammers arm the city and shoe its every need.
> Character: `industrious` (strong), `defensive` (slight)
> Leader: **Akmon the Forgemaster** — soot-stained and blunt; guards the secrets of the forge like family.

> **The Builders** — *the masons and carpenters*
> The joined guild of stone and timber — masons who raise temples, walls, and monuments, and the woodworkers who frame, beam, and joint the rest. The muscle behind every great public work, hungry for the next big contract.
> Character: `industrious` (strong), `conservative` (moderate)
> Leader: **Mnesikles the Master** — proud and driven; sees the city as unfinished and himself as the one to finish it.

> **The Keelwrights** — *the shipwrights*
> The yards that build the hulls — merchantmen and triremes alike. They rise and fall with the city's ambitions on the water.
> Character: `industrious` (moderate), `expansionary` (moderate)
> Leader: **Argeios the Keelwright** — steady and far-thinking; every keel he lays is a bet on a bigger fleet.

> **The Kerameis** — *the potters and vase-painters of the kiln-quarter*
> The clay-workers — everyday vessels and prized export ware. Numerous, ink-fingered, and prouder of their art than their station.
> Character: `industrious` (moderate), `opportunistic` (slight)
> Leader: **Pamphilos of the Kiln** — particular and vain; signs his finest work and remembers every slight.

> **The Ovenmen** — *the millers and bakers*
> The mills and ovens that turn grain into flour and flour into bread — the city's daily loaf, and a quiet lever whenever the granaries run low.
> Character: `industrious` (moderate), `opportunistic` (moderate)
> Leader: **Mazon the Baker** — flour-dusted and genial; smiles wider as the price of bread climbs.

> **The Winepressers** — *the vintners and winemakers*
> The presses and cellars behind the city's wine — from the rough stuff of the docks to the vintages of noble tables. Wine is everywhere, and so are they.
> Character: `industrious` (moderate), `opportunistic` (slight)
> Leader: **Oinops the Vintner** — ruddy and convivial; generous with a cup, shrewd over a ledger.

> **The Oil-pressers** — *the olive-oil makers*
> The presses that yield the city's olive oil — food, lamplight, athletes' sheen, and its single greatest export. Wealthy, and they know it.
> Character: `industrious` (strong), `expansionary` (moderate)
> Leader: **Elaios of the Press** — broad and unhurried; thinks in harvests and amphorae shipped abroad.

> **The Tanners** — *the leatherworkers and hide-curers*
> The reeking tan-yards at the edge of town — leather for armor, sandals, harness, and rigging. Rich, coarse, and loud in the assembly.
> Character: `industrious` (moderate), `aggressive` (moderate)
> Leader: **Bursas the Tanner** — blunt and foul-handed; a commoner's voice with a commoner's grudges.

> **The Weavers** — *the textile-makers*
> The looms that clothe the city — wool, linen, and dyed cloth for home and trade. Patient and domestic, and more powerful than their quiet suggests.
> Character: `industrious` (moderate), `defensive` (moderate)
> Leader: **Theano of the Loom** — soft-spoken and tireless; weaves alliances as readily as cloth.

### The Professions (*Technitai*) — power by cultivated skill and public renown

The skilled who rose by talent, not birth or making — those whose power is what they *can do*
and the name it earns them. (Academy owns thought and persuasion; the Professions own applied
skill and service.)

> **The Asklepiads** — *the physicians and healers*
> The secular doctors who trade in the one thing no one can refuse — health. Indispensable, and they know the worth of a cure withheld.
> Character: `defensive` (moderate), `ambitious` (slight)
> Leader: **Akesias the Physician** — calm and exacting; collects a quiet favor with every patient he saves.

> **The Players** — *the actors, musicians, and poets of the stage*
> The theatre folk who command the crowd's heart — beloved, mocking, and able to make or unmake a reputation in an afternoon's performance.
> Character: `opportunistic` (strong), `ambitious` (slight)
> Leader: **Komos of the Stage** — vain and magnetic; plays the audience like a lyre and never forgets a critic.

> **The Quillsworn** — *the city's clerks, record-keepers, and tax-farmers*
> The bureaucrats who run the paperwork and the purse — registries, deeds, proclamations, the collection of the city's taxes (which they bid to farm and quietly skim), and now the money-changing and book-keeping the old bankers' bench once handled. They know where every document and every drachma sits.
> Character: `conservative` (moderate), `corrupt` (moderate)
> Leader: **Grapheus the Reckoner** — meticulous and unhurried; forgets nothing, files everything, and counts twice.

> *(The champion athletes and their games are handled by the events system, not a standing
> faction — see `../proposals/faction-resource-map.md`.)*

> **The Perfumers** — *the purveyors of scented oils (myrepsoi)*
> Blenders of *myron* for the rich and the temples — but their real trade is access: scent, flattery, and the secrets of every household they serve.
> Character: `opportunistic` (moderate), `ambitious` (slight)
> Leader: **Myrrha of the Flask** — elegant and discreet; knows what the great families whisper, and to whom it's worth a word.

### Academy — dissolved (roster restructure 2026-06-14)

The intellect domain was cut. Its **philosophers (the Grove)** and **assembly orators (the
Goldentongues)** are parked for the future institutions / stance-layer features, to return placed
by function rather than as a standing domain; the **rhetoric-sellers (the Sophists)** were cut
outright; and the **star-readers (the Stargazers)** folded into the Bright Order. See
`../proposals/faction-resource-map.md`.

---

## Player title — the rank ladder

**Prytanis** is the initial title.  

### Future feature

The player rises through a ladder of Greek civic ranks as a long-run achievement track,
starting at **Prytanis** and climbing toward sole rule. The arc moves from legitimate office
(1–4) through exceptional authority (5–6) into autocracy (7–8). This is flavor + progression
only — the player's mechanical role (the "Mayor" in `mayor_spec.md`) is unchanged.

| Rank | Title (Greek) | English | What it meant |
|------|--------------|---------|---------------|
| 1 | **Prytanis** | Presiding Councillor | On the standing committee that ran the Boulḗ day-to-day — *the starting rank* |
| 2 | **Epistates** | Seal-Holder | The prytanis chosen by lot to chair the council and hold the state seal for a single day |
| 3 | **Archon** | Magistrate | One of the nine chief magistrates — real executive office |
| 4 | **Strategos** | General | Elected military-political commander; where real power flowed (Pericles' seat) |
| 5 | **Strategos Autokrator** | Supreme General | A general granted plenary, unchecked powers for a campaign or crisis |
| 6 | **Hegemon** | Pre-eminent Leader | First man of the city — informal supremacy over all factions |
| 7 | **Tyrannos** | Tyrant | Sole ruler who seized power outside the constitution |
| 8 | **Basileus** | King | Supreme sovereign rule — the top |




