import { readFileSync } from 'fs'
import { fileURLToPath } from 'url'
import { dirname, resolve } from 'path'
import { describe, it, expect } from 'vitest'
import GameView from '../views/GameView.vue'

const here = dirname(fileURLToPath(import.meta.url))
const apiSrc = readFileSync(resolve(here, '../api.js'), 'utf8')
const vueSrc = readFileSync(resolve(here, '../views/GameView.vue'), 'utf8')

const { bandClass, poolCount, frontKind } = GameView.methods

// ── api.js source guard ───────────────────────────────────────────────────────

describe('api.js source guard', () => {
  it('has no commission reference', () => {
    expect(apiSrc).not.toMatch(/\bcommission\b/)
  })

  it('has no /projects/commission route', () => {
    expect(apiSrc).not.toContain('/projects/commission')
  })
})

// ── GameView.vue source guard ─────────────────────────────────────────────────

describe('GameView.vue source guard', () => {
  it('f.rating.toFixed appears only inside the de-emphasised rating-sub span', () => {
    // Primary readout uses Math.floor; the raw float is muted
    expect(vueSrc).toMatch(/rating-sub muted[\s\S]{0,80}f\.rating\.toFixed/)
  })
})

// ── bandClass ─────────────────────────────────────────────────────────────────

describe('bandClass', () => {
  it('returns danger for all eight danger bands', () => {
    for (const b of ['Starving', 'Miserable', 'Plague', 'Godless', 'Boiling', 'Sodden', 'Dry', 'Hostile']) {
      expect(bandClass(b), b).toBe('danger')
    }
  })

  it('returns accent for notable bands (sample)', () => {
    expect(bandClass('Hungry')).toBe('accent')
    expect(bandClass('Suspicious')).toBe('accent')
    expect(bandClass('Favorable')).toBe('accent')
    expect(bandClass('Beloved')).toBe('accent')
    expect(bandClass('Zealous')).toBe('accent')
  })

  it('returns empty string for nominal bands', () => {
    expect(bandClass('Sated')).toBe('')
    expect(bandClass('Content')).toBe('')
    expect(bandClass('Neutral')).toBe('')
  })
})

// ── poolCount ─────────────────────────────────────────────────────────────────

describe('poolCount', () => {
  it('returns 0 for null stack', () => {
    expect(poolCount(null)).toBe(0)
  })

  it('returns full count for pristine stack (completed + progress=100)', () => {
    expect(poolCount({ completed: true, progress: 100, count: 3 })).toBe(3)
  })

  it('returns count − 1 when top is building', () => {
    expect(poolCount({ completed: false, progress: 50, count: 3 })).toBe(2)
  })

  it('returns 0 for a solo building (count 1, not completed)', () => {
    expect(poolCount({ completed: false, progress: 50, count: 1 })).toBe(0)
  })
})

// ── frontKind ─────────────────────────────────────────────────────────────────

describe('frontKind', () => {
  it('returns null for null stack', () => {
    expect(frontKind(null)).toBeNull()
  })

  it('returns null for empty stack (count < 1)', () => {
    expect(frontKind({ count: 0, completed: true, progress: 100 })).toBeNull()
  })

  it('returns null for pristine stack (completed, progress=100)', () => {
    expect(frontKind({ count: 2, completed: true, progress: 100 })).toBeNull()
  })

  it('returns building when not completed', () => {
    expect(frontKind({ count: 1, completed: false, progress: 60 })).toBe('building')
  })

  it('returns damaged when completed but progress < 100', () => {
    expect(frontKind({ count: 1, completed: true, progress: 75 })).toBe('damaged')
  })
})
