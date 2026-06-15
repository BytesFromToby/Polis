# Decisions: Roster Restructure
Spec: Planning/specs/roster-restructure_spec.md
Date: 2026-06-14

Data migration to the designed 28-faction / 7-domain roster (`proposals/faction-resource-map.md`).
No new mechanics. Recon confirmed: the data has **zero cross-references** (no relational traits or
relationships), so cuts dangle nothing; the only *code* touch is `BASE_PROJECT_NAMES`.

- **Skiadai split conserves aristocracy Σ level (9)** — the harvest chain pools `domain:aristocracy`,
  so any change to the estates re-tunes barley. Skiadai (was rating 2.0, level 2) splits into the
  vine estate (`skiadai`, r1.0, level 1) + the new olive estate (`elaiades`, r1.5, level 1). Σ stays
  4+3+1+1 = 9 → barley raw unchanged → the shipped food balance is undisturbed. The olive estate is
  the *stronger* of the pair by rating (1.5 vs 1.0) but still level 1, so the food math is unaffected.
  "Olive meaningfully stronger" is deferred to when the oil chain is built (it grows then). Rejected:
  giving the olive estate level 2 — it would raise barley supply and force a food re-tune in a slice
  that is supposed to be food-neutral.
- **New games only; no save migration** — existing snapshots serialize their own factions/domains, so
  they restore graceful-but-stale on the old roster; new games (fresh seed) get the 28/7 roster. Same
  precedent as the faction-descriptions slice. This is an alpha/tech-demo — building snapshot-migration
  tooling for a roster this different isn't worth it. The official "Polis" seed row is refreshed;
  user-created cities/saves are left untouched.
- **Military keeps evocative names** — `shieldsworn` serves as the Army (the citizen phalanx *is* the
  land force) and `oarsworn` as the Fleet (the war fleet *is* the fleet); only the City Guard is a
  genuinely new entry. Rejected literal renames to "The Army"/"The Fleet" — they'd clash with the
  all-evocative roster (Shieldsworn next to "The Army" reads wrong). Net military 4→3: keep 2, cut
  Free-spears + Companions, add City Guard. The mercenary (Free-spears) gold-for-force lever is parked
  as a future Army property, not a faction.
- **Stargazers → Bright Order, Silverbench bookkeeping → Quillsworn** are *identity* absorptions
  (blurb/description notes), not field changes — the absorbing faction's mechanics are unchanged here;
  the absorbed roles activate in their own later slices (sensor, finance).

## Proposed flavor for the 5 new factions (user-reviewable — see Open Questions)
- `elaiades` — **The Elaiades** · aristocracy · r1.5 · blurb: "the olive-groves of the inland slopes" ·
  description: "a younger branch of the old estates, rich in oil if not yet in name."
- `the-builders` — **The Builders** · guilds · r3.0 · blurb: "the masons and carpenters" ·
  description: "the joined guild of stone and timber that raises wall, roof, and temple."
- `dockhands` — **The Dockhands** · port · r4.0 · blurb: "the wharf-hands and port wardens" ·
  description: "labour and authority of the quay — berths, customs, and how much the harbour can bear."
- `merchant-houses` — **The Merchant Houses** · port · r4.0 · blurb: "the wholesale traders and shipowners" ·
  description: "the great houses that move grain and oil by sea — the city's lifeline and its purse."
- `city-guard` — **The City Guard** · military · r3.0 · blurb: "the watch within the walls" ·
  description: "the force that keeps the peace at home — and leans on the crowd when it must."
