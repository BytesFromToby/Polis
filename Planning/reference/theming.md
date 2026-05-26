# Theming (Reference)

The world identity that specs and content cite for naming and flavor. Reference doc —
definitional, no **Done when:** items.

**Date:** 2026-05-26

Polis has **one canonical theme: an ancient-Greek city-state.** There is no multi-theme
or themed-city-pack system. (The earlier medieval river-port city *Rivers Point* and the
"pick a themed city" idea are **retired** — see Retired section.)

---

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

## Domain roster (LOCKED 2026-05-26)

The nine canonical spheres of influence. Mechanically each is a domain with a cap, drift,
and a relationship row to every other domain.

Each domain is a distinct answer to *"where does your power come from?"* The English name is
used in-game; the Greek is flavor.

| Domain (English) | Greek | The sphere — and its source of power |
|---|---|---|
| **Aristocracy** | *Eupatridai* — "the well-born" | The old landed clans. Power by **birth** — blood, lineage, inherited estates. |
| **Guilds** | *Demiourgoi* — "craftsmen" | Smiths, masons, shipwrights and their backers. Power by **production** — they make things. |
| **Trade** | *Emporoi* — "merchants" | Merchants, money, banking. Power by **exchange** — they move goods and coin, they don't make them. |
| **The Professions** | *Technitai* — "people of skill" | Healers, performers, skilled practitioners. Power by **cultivated skill and public renown**. |
| **Temples** | *Hiereis* — "the priesthood" | Cults, priesthoods, oracles. Power by **divine legitimacy**. |
| **Military** | *Stratos* — "the host" | The hoplite phalanx and the sellswords it absorbs. Power by **force of arms**. |
| **Academy** | *Akadēmeia* — "the school" | Philosophers, sophists, rhetoricians. Power by **intellect** — shaping thought and opinion. |
| **Harbor** | *Limēn* — "the port" | Shipping, the fleet, dock labor. Power by **command of the sea**. |
| **Underclass** | *Metoikoi* — "resident outsiders" | Metics, the unfranchised, smugglers. Power at the **margins** — outside the law and the citizen rolls. |

The canonical roster is these **nine domains**. The common people are handled by a separate
future *population* system (not a domain); **Assembly** and **Council** are deferred to the
future institutions feature (see the player-title note below).

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
> A once-great house in decline, clinging on through favors, debts, and quiet leverage.
> Character: `opportunistic` (strong), `corrupt` (slight)
> Leader: **Demarete of the Skiadai** — gracious in public, ruthless in the dark.

### Temples (*Hiereis*) — power by divine legitimacy

Rival priesthoods and cults, each claiming the city's faith — and the wealth and authority
that come with it. The first four are core; the last two are extras to keep or cut.

> **The Tidesworn** — *priests of the Earth-Shaker (Poseidon)*
> The sea-god's cult — storms, earthquakes, the harbor's fear. They claim the god's wrath as leverage.
> Character: `aggressive` (moderate), `ambitious` (moderate)
> Leader: **Nereus Halios** — booming and volatile; speaks of the god's anger as if it were his own.

> **The Hearthwardens** — *keepers of the eternal flame (Hestia)*
> Guardians of the city's sacred hearth, the unbroken civic fire. The still, traditional soul of the polis.
> Character: `conservative` (strong), `defensive` (moderate)
> Leader: **Hestaia the Unmoved** — serene, rigid; treats every reform as a draft on the flame.

> **The Greenmantle** — *the harvest cult of the earth-mother (Demeter)*
> The grain-and-fertility cult, rooted in the seasons; blesses the fields and feeds the festivals.
> Character: `industrious` (moderate), `defensive` (slight)
> Leader: **Chloris of the Furrow** — warm and patient; thinks in seasons, slow to anger and slow to forgive.

> **The Raving Choir** — *ecstatic prophets of the mad god (Dionysos)*
> Frenzied seers who prophesy in fits and whip crowds into ecstasy. Beloved, feared, uncontrollable.
> Character: `destructive` (moderate), `opportunistic` (moderate)
> Leader: **Eurymache the Raving** — wild-eyed, speaks in the god's tongue; no one knows what she'll do next.

> **The Bright Order** — *the great oracle of the far-shooting god (Apollo)*
> The establishment oracle — prestigious, panhellenic, consulted before wars and colonies. Kingmakers in robes.
> Character: `ambitious` (strong), `opportunistic` (moderate)
> Leader: **High Seer Aletheian** — calm and smiling; every prophecy is a move on a longer board.

### Military (*Stratos*) — power by force of arms

The armed power of the city: the citizen soldiery, the hired companies, and the ambitious
commanders who would point them. The fourth is an extra to keep or cut.

> **The Shieldsworn** — *the citizen phalanx*
> The hoplite militia of property-owning citizens, the city's backbone — and proud that only citizens should bear its spear.
> Character: `defensive` (strong), `conservative` (moderate)
> Leader: **Drakon the Steadfast** — stolid, dutiful; distrusts hired blades and glory-hounds alike.

> **The Free Spears** — *the sellsword companies*
> Professional soldiers for hire, foreign and rootless, loyal to coin and the next contract.
> Character: `opportunistic` (strong), `corrupt` (moderate)
> Leader: **Kallias the Coinbought** — affable, amoral; serves whoever pays and remembers who didn't.

> **The Companions** — *a victorious general's sworn veterans*
> The personal following of a celebrated commander — battle-hardened, devoted to their man over the city.
> Character: `ambitious` (strong), `aggressive` (moderate)
> Leader: **Antimachos the Laurelled** — charismatic and hungry; wears past victories like a claim on the future.

> **The Oarsworn** — *the war fleet and its crews*
> The triremes and the citizen-rowers who drive them — the city's reach across the sea, and a restless power base of the common man.
> Character: `expansionary` (strong), `ambitious` (moderate)
> Leader: **Naukrates of the Long Oars** — bold and restless; dreams of a city whose walls are its ships.

### Harbor (*Limēn*) — power by command of the sea

The commercial maritime world — the labor, the boats, the authority, and the carrying trade
that move goods and people across the water. (The *war* fleet sits under Military; Harbor is
the civilian port.) Trade buys and sells; Harbor *moves and handles*.

> **The Quaymen** — *the dockhands and stevedores*
> The labor of the wharves — they load, unload, and haul. Numerous and organized; a word from them can still the whole port.
> Character: `defensive` (moderate), `aggressive` (moderate)
> Leader: **Brontes Bighand** — gruff and immovable; protective of his gangs and quick to down tools.

> **The Netmenders** — *the fishing crews who feed the city*
> The boat crews who work the waters — weather-beaten, independent, traditional. The city's daily catch and a food supply unto themselves.
> Character: `conservative` (moderate), `defensive` (slight)
> Leader: **Glaukos the Weathered** — salt-cured and plain-spoken; trusts the tide more than any magistrate.

> **The Harborwardens** — *the port authority — berths, customs, bonded warehouses*
> The officials who decide who docks, when, and at what toll — and who control the stored cargo. Gatekeepers who take their cut.
> Character: `corrupt` (strong), `conservative` (slight)
> Leader: **Warden Pheidon** — courteous and dry; every favor has a price, and he never forgets a ledger.

> **The Saltroad Houses** — *the shipowners and freight-carriers (naukleroi)*
> The owners of the merchant hulls that carry the city's cargo — they don't buy the goods, they move them, and they live to expand the routes.
> Character: `expansionary` (strong), `ambitious` (moderate)
> Leader: **Timaios the Farsailed** — restless and far-seeing; measures the city by how far its hulls reach.

### Trade (*Emporoi*) — power by exchange

The world of buying, selling, lending, and the games played with supply and price. Trade
*moves goods and coin*; it does not make them (Guilds) or carry them by sea (Harbor).

> **The Amphora Houses** — *the great wholesale merchants*
> The big import-export traders who deal in bulk — grain, oil, wine, slaves. The dominant commercial power, always reaching for a wider market.
> Character: `expansionary` (strong), `ambitious` (moderate)
> Leader: **Polemarchos the Stout** — jovial and grasping; counts the city's worth in cargoes landed.

> **The Silverbench** — *the money-changers and lenders (trapezitai)*
> The bankers at their tables — deposits, loans, currency, debt. Quiet, patient, and owed by half the city.
> Character: `conservative` (strong), `corrupt` (slight)
> Leader: **Aristion of the Bench** — cool and exact; never raises his voice, never forgives a default.

> **The Stallmongers** — *the agora retailers and shopkeepers (kapeloi)*
> The petty traders of the marketplace stalls — numerous, scrappy, working every angle for a thin margin.
> Character: `opportunistic` (strong), `defensive` (moderate)
> Leader: **Myrto Quicktongue** — sharp and fast-talking; speaks for the little traders and misses nothing.

> **The Storehouse Ring** — *the warehouse speculators who corner the market*
> A cartel that buys up stock and sits on it — hoarding grain and goods to choke supply and spike the price, then selling at the city's worst hour.
> Character: `corrupt` (strong), `opportunistic` (moderate)
> Leader: **Hieron the Patient** — soft-spoken and predatory; waits for famine the way others wait for harvest.

### Guilds (*Demiourgoi*) — power by production

The makers — those whose power is the things they build. Guilds *make* goods; Trade sells
them, Harbor ships them. This is the city's largest domain — a crowded quarter of crafts.

> **The Bronzehands** — *the smiths and metalworkers*
> The forges — bronze and iron, arms, tools, fittings. Their hammers arm the city and shoe its every need.
> Character: `industrious` (strong), `defensive` (slight)
> Leader: **Akmon the Forgemaster** — soot-stained and blunt; guards the secrets of the forge like family.

> **The Stonewrights** — *the masons and builders*
> The stoneworkers who raise temples, walls, and monuments — the muscle behind every great public work, and hungry for the next big contract.
> Character: `industrious` (strong), `ambitious` (moderate)
> Leader: **Lithos the Master-Builder** — proud and driven; sees the city as unfinished and himself as the one to finish it.

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

> **The Carpenters** — *the woodworkers and joiners*
> The timber workshops — furniture, carts, beams, doors, tools. The frame behind daily life, beside (not in) the shipyards.
> Character: `industrious` (strong), `conservative` (slight)
> Leader: **Tekton the Joiner** — methodical and exacting; measures twice and trusts wood over words.

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

> **The Garland-Chasers** — *the champion athletes and gymnasium trainers*
> The victors of the games and the men who train them — living glory, courted by every faction that wants the crowd's adoration reflected onto itself.
> Character: `ambitious` (strong), `aggressive` (slight)
> Leader: **Pankrates the Victor** — proud and restless; measures his worth in wreaths and refuses to lose at anything.

> **The Quillsworn** — *the city's clerks, record-keepers, and tax-farmers*
> The bureaucrats who run the paperwork and the purse — registries, deeds, proclamations, and the collection of the city's taxes, which they bid to farm and quietly skim. They know where every document and every drachma sits.
> Character: `conservative` (moderate), `corrupt` (moderate)
> Leader: **Grapheus the Reckoner** — meticulous and unhurried; forgets nothing, files everything, and counts twice.

> **The Perfumers** — *the purveyors of scented oils (myrepsoi)*
> Blenders of *myron* for the rich and the temples — but their real trade is access: scent, flattery, and the secrets of every household they serve.
> Character: `opportunistic` (moderate), `ambitious` (slight)
> Leader: **Myrrha of the Flask** — elegant and discreet; knows what the great families whisper, and to whom it's worth a word.

> **The Adorners** — *the jewelers and gem-setters to the great houses*
> The high-end goldsmiths — diadems, signet rings, necklaces. Status made wearable, fitted to the elite they flatter — and they compete with the Perfumers to be closest to power.
> Character: `opportunistic` (moderate), `ambitious` (moderate)
> Leader: **Chrysanthe of the Gem** — dazzling and watchful; dresses the powerful, and listens while she fastens the clasp.

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

---

## Open questions

- **Polis name.** Defaults to "Polis"; players will be able to name their own city.

---

## Retired

- **Rivers Point** — the medieval/D&D river-port city (nine domains: guilds, docks, noble
  houses, city watch, underworld, temple, commons, arcane, registry). No longer part of the
  project; its data and seed entry are being removed.
- **Themed-city packs / multi-theme selection** — the idea of choosing among multiple themed
  cities is dropped. Ancient Greek is the sole theme.
- **Twin Cities / Minneapolis roster** — the original real-world placeholder (`data/*.json`),
  superseded by the Greek re-theme.
