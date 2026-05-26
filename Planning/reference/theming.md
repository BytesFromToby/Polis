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
