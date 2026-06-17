# Proposal: The Public — state model, scales, and crisis events

**Date:** 2026-06-14
**Status:** SUBSTANTIALLY SHIPPED — six of seven scales live. fed/happy/health (barley/fish/flocks),
**piety + unrest** (2026-06-16), and **consumption + both Public→production wires** (2026-06-17,
`decisions/2026-06-16-consumption-and-production-wire.md`) are built. The **U-shaped consumption
axis** subsumes the old `drunk` flag; the **efficiency multiplier** (health↑ / consumption↓) is the
first two-way loop. **Still proposal-only:** confidence's band-consequences (the axis itself is the
existing `support` — only its removal-spiral/acclamation effects remain), the misery→drink feedback
(deferred behind a governor), the multiplier on non-food production, and the richer extreme-event
deck (Witch-Hunt, Oracle's Demand, Insurrection, the Exodus). The Public outgrew being a subsection
of `resource-chains.md`; this is its home. Companions: `resource-chains.md`, `food-supply_spec.md`,
`faction-resource-map.md`.

## Belief is the mechanic; the gods are not

The engine models whether the **people feel the city is in good standing with the heavens** —
never whether prayers work. Every material outcome stays materially caused; belief is the
*lens* on it, with real political teeth. Temples *produce* piety (rites/festivals) and
*interpret* crises: a plague reads as "divine punishment / the Mayor angered the gods" → blame,
or "a trial we'll endure" → rallying, depending on piety + which temple has the people's ear.
Historical anchor — the Athenian plague of 430 BC: belief was the decisive political force
without the gods being real. (No god ever reaches into physics; temple "multiplier" effects are
human — organization, morale, interpretation.)

## The seven scales, in three layers

A scale earns a stored slot only with a **distinct driver**, a **distinct consequence**, and
**benefit from memory** — and the sharpest filter: *both extremes must do something, and ideally
neither extreme is purely "good."* Derived descriptors that fail this stay derived. **Not
balancing them yet — they exist as the model.**

**Layer 1 — Needs** (inputs; driven by suppliers; memory/drift): **fed** · **happy** · **health**
(all shipped) + **piety** (adopted, belief-based).

**Layer 2 — Standing axes** (political/output): **confidence** = the existing `support`
(−50..+50; removal spiral + audience leverage; *already tracked*) and **unrest** = the aggregate
of pressure (hunger + impiety + low confidence + drunken volatility), with memory because the
City Guard suppresses it while the cause festers. Unrest sits **on top of** the needs (output),
not beside them.

**Layer 3 — The balance-axis** (interior optimum — tune to the middle): **consumption** (alcohol),
driven by wine supply; bad at *both* ends.

**Derived (never stored):** `disposition` (off unrest/confidence), `drunk` (off consumption —
and *feeds* unrest as volatility).

## Band matrix (20% increments)

Read each row for its *shape*: needs and confidence climb (low bad → high good); unrest inverts
(low good → high bad); consumption peaks in the middle (both ends bad).

| Scale (shape) | 0–20 | 20–40 | 40–60 | 60–80 | 80–100 |
|---|---|---|---|---|---|
| **Fed** (high good) | starving — pop dies, riots | hungry — pop stalls, unrest↑ | fed — stable | well-fed — pop grows | bountiful — surplus to export |
| **Happy** (high good) | miserable — flight, unrest↑ | sullen — output dips | content — stable | cheerful — support↑ | festive — joy, but drink↑ |
| **Health** (high good) | plague — pop dies | sickly — output dips | healthy — stable | robust — pop grows, **output↑** | thriving — disease-proof, **output↑** |
| **Piety** (high good*) | godless — crises blamed on you | lax — unease | observant — stable | devout — crises become trials | zealous — temples defy you |
| **Confidence** (high good) | hostile — removal coalition | suspicious — audiences harder | neutral — stable | favorable — cooperation | beloved — political capital |
| **Unrest** (low good) | placid — calm (passive) | quiet — fine | restless — crime↑ | agitated — riots loom | boiling — riot, revolt |
| **Consumption** (mid good) | dry — bad water sickens | sober — a bit brittle | tempered — sweet spot | tipsy — work↓, Watch dull | sodden — work stops, drunk riots |

\* piety: the high end tips into zealotry — not purely good.

**Two Public→production wires** (state reaching *back into* output — the first two-way loops;
model each as a single global efficiency multiplier, balance carefully): **health** (robust/
thriving → output↑) and **consumption** (tipsy/sodden → output↓).

## Crisis events at the extremes

The extremes are where the deck should be richest — a scale at 0–20 or 80–100 is a *story* the
city tells about itself. The strongest extreme-events hand the Mayor a **fork**, not just a
number — that's what reveals what kind of Prytanis you are, and several feed the stance layer
later. *(Fed/health gating is shipped; the rest need their scale built first.)*

- **Fed — low:** *Bread Riot* (shipped — mob storms the bakeries, Ovenmen damaged, unrest↑);
  *The Exodus* (sustained starving → population walks out; fork: open the granaries (gold) or bar
  the gates (support hit)). **high:** *Festival of Demeter* (fat harvest → joy + piety; nudges
  complacency).
- **Happy — low:** *The Lament* (despair → emigration, confidence drains). **high:** *Spontaneous
  Revel* (joy feeds itself, but consumption creeps up — the high end seeds the next problem).
- **Health — low:** *Plague Outbreak* (shipped, sickly-gated — Asklepiads swamped); *Blame the
  Foreigners* (dying city scapegoats the metics/Port newcomers — a faction takes the mob's fury;
  fork: protect them (support cost) or look away (a darker city)). **high:** *City of Vigor*
  (crowds, athletes shine → pop growth + civic pride).
- **Piety — low:** *The Ignored Omen* (a portent the godless city shrugs off → the next disaster
  lands harder, unprepared). **high:** *The Witch-Hunt* (zealots demand a scapegoat — a faction
  the temples dislike takes damage, chosen by the strongest cult); *The Oracle's Demand* (an
  over-mighty temple demands the Mayor fund the great rite or lose piety *and* gain the priests'
  enmity).
- **Confidence — low:** *The Removal Coalition* (hostile factions move to oust you; countdown);
  *Effigy in the Agora* (public symbolic rejection emboldens rivals). **high:** *Acclamation*
  (the assembly grants an honor — a title-ladder step + political-capital windfall).
- **Unrest — high:** *The Mob Marches* (open riot — projects damaged, Guard forced into a contest
  it may lose, factions Steal in the chaos); *Insurrection* (at boiling point, a bid to take the
  city — direct removal threat; the bill for every masked symptom). **low:** *Civic Torpor*
  (minor — a too-placid city is apathetic: low turnout, low civic energy; the faint cost of the
  "good" end).
- **Consumption — low:** *The Wells Sicken* (too little wine → too much raw water → a waterborne
  plague drives health down; abstinence causing illness is period-true and will surprise players).
  **high:** *Drunken Riot* (a festival tips to violence, the Watch too sodden to hold it — the
  consumption+unrest combo); *The City Sleeps It Off* (a wasted cycle, production craters).

## Design notes

- **Watch the feedback loop:** if misery drives drinking *and* high drinking cuts output → doom
  spiral. First cut: consumption tracks wine supply only; add drink-to-cope later *with a governor*.
- **The "buy time vs. fix the cause" spine:** festivals (Dionysos), the games-event, and the City
  Guard are *symptom* levers (soothe/suppress now); the real fixes (feed them, raise piety
  honestly, prepare for the disaster) are the hard road. Many ways to mask pressure, few to solve
  it, bills compound.
- **Sequencing:** fish first (needs none of this); then piety + unrest as the next public-needs
  extension; consumption after; the extreme-events deck grows as each scale lands.
