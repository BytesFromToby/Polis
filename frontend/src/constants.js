/**
 * constants.js — Shared engine constants for the frontend.
 * Mirrors the trait lists and domain definitions from the Python engine.
 */

export const DOMAINS = [
  { id: 'guilds',       name: 'Guilds' },
  { id: 'docks',        name: 'Docks' },
  { id: 'noble_houses', name: 'Noble Houses' },
  { id: 'city_watch',   name: 'City Watch' },
  { id: 'underworld',   name: 'Underworld' },
  { id: 'temple',       name: 'Temple' },
  { id: 'commons',      name: 'Commons' },
  { id: 'arcane',       name: 'Arcane' },
  { id: 'registry',     name: 'Registry' },
]

export const UNIT_TRAITS = [
  'Expansionary', 'Cautious', 'Revengeful', 'Satisfied', 'Callous',
  'Opportunistic', 'Loyal', 'Ambitious', 'Loner', 'Joiner',
]

export const FACTION_TRAITS = [
  'Expansionary', 'Defensive', 'Insular', 'Hierarchical',
  'Meritocratic', 'Corrupt', 'Ideological', 'Open',
]
